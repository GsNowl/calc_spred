import asyncio
import datetime
import gzip
from time import sleep

import websockets
import aiohttp
import json
from config import SLEEP_TIME


p2p_dict = {2: 'usdt',
            1: 'btc',
            3: 'eth',
            29: 'sberbank',
            28: 'tinkoff',
            25: 'alfa',
            9: 'qiwi',
            36: 'raiffeisenbank',
            19: 'yoomoney',
            358: 'rosbank',
            'sell': 'buy',
            'buy': 'sell'}

result_p2p = dict()
result_spot = dict()


async def write_to_file():
    while True:
        import json
        with open('huobi.json', 'w', encoding='utf-8') as f:
            json.dump(result_spot, f, ensure_ascii=False, indent=4)

        await asyncio.sleep(SLEEP_TIME)


async def get_spot_huobi():
    url1 = 'wss://api.huobi.pro/ws'
    # url2 = 'wss://api-aws.huobi.pro/feed'

    async with websockets.connect(url1) as client:
        # await client.send(json.dumps({"sub": f"market.btcusdt.depth.step0", "symbol": "btcusdt", "id": "id1"}))

        for ticket in ['btcusdt', 'ethusdt', 'bnbusdt', 'usdtrub', 'shibusdt', 'btcrub', 'ethbtc']:
            # Get offers from stock glass
            # await client.send(json.dumps({"sub": f"market.{ticket}.depth.step0", "symbol": ticket, "id": "id1"}))

            # Get ticket
            await client.send(json.dumps({"sub": f"market.{ticket}.ticker", "symbol": ticket, "id": "id1"}))

        while True:
            await asyncio.create_task(write_to_file())
            try:
                data = json.loads(gzip.decompress(await client.recv()).decode('utf-8'))

                keys = data.keys()

                if 'ping' in keys:
                    await client.send(json.dumps({'pong': data['ping']}))
                    print('Client send pong', data['ping'])

                elif 'ch' in keys:
                    ticket = data['ch'].split('.')[1]
                    tick = data['tick']

                    # sell = tick['bids'][0][0]
                    # buy = tick['asks'][0][0]
                    # print(f'{ticket} -> FOR SELL: {sell}; FOR BUY: {buy}')

                    course = tick['ask']
                    print(f'{ticket} -> {course}')

                    result_spot[ticket] = course

                else:
                    print(data)

            except Exception as e:
                print('Error: ', e)


async def get_p2p_huobi(coin_id, pay_method, trade_type):
    if pay_method == 358:
        pay_method = '29,358'

    payload = {'coinId': coin_id,
               'currency': 11,
               'tradeType': trade_type,
               'currPage': 1,
               'payMethod': pay_method,
               'acceptOrder': 0,
               'country': '',
               'blockType': 'general',
               'online': 1,
               'range': 0,
               'amount': '',
               'onlyTradable': 'false'}

    url = 'https://otc-api.bitderiv.com/v1/data/trade-market'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, data=payload) as response:
            # print('P2P HUOBI ', f"{p2p_dict[pay_method]}_{trade_type}_{p2p_dict[coin_id]}")
            try:
                response = json.loads(await response.text())
                data = response['data']
                best_price = float(data[0]['price'])
                best_price_lb = False

                if float(data[0]['minTradeLimit']) <= 1000:
                    # print(best_price)
                    best_price_lb = best_price

                else:
                    for i in data[1:]:
                        lowest_budget = float(i['minTradeLimit'])
                        if lowest_budget <= 1000:
                            best_price_lb = i['price']
                            break

                if ',' in str(pay_method):
                    pay_method = 358
                trade_type = p2p_dict[trade_type]
                result_p2p.update({f"{p2p_dict[pay_method]}_{trade_type}_{p2p_dict[coin_id]}": best_price})
                result_p2p.update({f"{p2p_dict[pay_method]}_{trade_type}_{p2p_dict[coin_id]}_1000": best_price_lb})

            except IndexError:
                if ',' in str(pay_method):
                    pay_method = 358
                trade_type = p2p_dict[trade_type]
                result_p2p.update({f"{p2p_dict[pay_method]}_{trade_type}_{p2p_dict[coin_id]}": 0})
                result_p2p.update({f"{p2p_dict[pay_method]}_{trade_type}_{p2p_dict[coin_id]}_1000": 0})
                print('IndexError')
            except json.decoder.JSONDecodeError:
                if ',' in str(pay_method):
                    pay_method = 358
                print(f"{p2p_dict[pay_method]}_{trade_type}_{p2p_dict[coin_id]}")

            if ',' in str(pay_method):
                pay_method = 358
            print('P2P HUOBI success', f"{p2p_dict[pay_method]}_{trade_type}_{p2p_dict[coin_id]}")


async def huobi_main():
    while True:
        start = datetime.datetime.now().strftime('%H:%M:%S')
        tasks = [asyncio.create_task(get_spot_huobi())]

        # crypto = [1, 2, 3]
        # fiat = [25, 28, 9, 36, 19, 358]
        # for f in fiat:
        #     for c in crypto:
        #         for t in ['sell', 'buy']:
        #             tasks.append(asyncio.create_task(get_p2p_huobi(c, f, t)))

        for task in tasks:
            await task
        # print('HUOBI SUCCESS')

        # print(result_spot)
        # print(result_p2p)

        # data = {'p2p': result_p2p,
        #         'spot': result_spot,
        #         'start': start,
        #         'end': datetime.datetime.now().strftime('%H:%M:%S')}

        with open('huobi.json', 'w',  encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print('HUOBI UPDATE AT ', datetime.datetime.now().strftime('%H:%M:%S'))
        await asyncio.sleep(20)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(huobi_main())
