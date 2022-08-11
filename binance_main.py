import asyncio
import datetime
import json
from time import sleep

import aiohttp
import websockets
from config import SLEEP_TIME

valuable_pairs = ['USDTRUB', 'BTCUSDT', 'BTCBUSD', 'BTCRUB', 'BUSDUSDT', 'BUSDRUB', 'BNBBTC',
                  'BNBBUSD', 'BNBETH', 'BNBRUB', 'ETHUSDT', 'ETHBTC', 'ETHBUSD', 'ETHRUB',
                  'SHIBUSDT', 'SHIBBUSD']
payments_p2p = ['Tinkoff', 'RosBank', 'RaiffeisenBankRussia', 'QIWI', 'YandexMoney', 'ABank']
SB_p2p = ['SELL', 'BUY']
crypto_p2p = ['USDT', 'BTC', 'BUSD', 'BNB', 'ETH', 'RUB', 'SHIB']

spot_prices = dict()
p2p_prices = dict()


async def write_to_file():
    while True:
        import json
        with open('binance.json', 'w', encoding='utf-8') as f:
            json.dump(spot_prices, f, ensure_ascii=False, indent=4)
        await asyncio.sleep(SLEEP_TIME)


async def get_p2p_binance(data, address_cell):
    async with aiohttp.ClientSession() as session:
        async with session.post(url='https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search',
                                json=data) as response:
            response = await response.json()
            try:
                p2p_prices.update({'_'.join(address_cell): response['data'][0]['adv']['price']})
            except IndexError:
                p2p_prices.update({'_'.join(address_cell): False})


async def gen_tasks_binance():
    while True:
        start = datetime.datetime.now().strftime('%H:%M:%S')
        # tasks = []
        # for payment in payments_p2p:
        #     for s_b in SB_p2p:
        #         for crypto in crypto_p2p:
        #             data1 = {
        #                 "page": 1, "rows": 1,
        #                 "payTypes": [payment], "asset": crypto, "tradeType": s_b,
        #                 "countries": [], "fiat": "RUB"
        #             }
        #             tasks.append(asyncio.create_task(get_p2p_binance(data1, [payment, s_b, crypto])))
        #             data2 = {
        #                 "page": 1, "rows": 1,
        #                 "payTypes": [payment], "tradeType": s_b, "asset": crypto,
        #                 "countries": [], "fiat": "RUB", "merchantCheck": False, "transAmount": "1000"
        #             }
        #             tasks.append(asyncio.create_task(get_p2p_binance(data2, [payment, s_b, crypto, '1000'])))
        #
        # for task in tasks:
        #     await task

        # print(p2p_prices)
        # print(spot_prices)

        data = {'p2p': p2p_prices,
                'spot': spot_prices,
                'start': start,
                'end': datetime.datetime.now().strftime('%H:%M:%S')}

        with open('binance.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print('BINANCE UPDATE AT ', datetime.datetime.now().strftime('%H:%M:%S'))
        await asyncio.sleep(20)


async def get_spot_binance():
    pairs = '/'.join([i.lower()+'@miniTicker' for i in valuable_pairs])
    url = f'wss://stream.binance.com:9443/stream?streams={pairs}'
    # url = 'wss://stream.binance.com:9443/stream?streams=!ticker@arr'  # все пары сразу

    async with websockets.connect(url) as client:
        while True:
            await asyncio.create_task(write_to_file())
            try:
                data = json.loads(await client.recv())
                pair = data['data']['s']
                price = float(data['data']['c'])
                if price < 0.0001:
                    price = float(f'{price:.{11}f}')
                spot_prices[pair] = price
                # print(spot_prices)
            except websockets.ConnectionClosed:
                continue


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(gen_tasks_binance())
