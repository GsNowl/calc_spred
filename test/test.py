import gzip
import json
import websockets
import asyncio
from config import SLEEP_TIME
from google_sheets import update_sheets

result_spot = dict()
spot_prices = dict()

valuable_pairs = ['USDTRUB', 'BTCUSDT', 'BTCBUSD', 'BTCRUB', 'BUSDUSDT', 'BUSDRUB', 'BNBBTC',
                  'BNBBUSD', 'BNBETH', 'BNBRUB', 'ETHUSDT', 'ETHBTC', 'ETHBUSD', 'ETHRUB',
                  'SHIBUSDT', 'SHIBBUSD']


async def write_to_file():
    while True:
        print('Write file............')
        with open('../binance.json', 'w', encoding='utf-8') as bf, open('../huobi.json', 'w', encoding='utf-8') as hf:
            json.dump(spot_prices, bf, ensure_ascii=False, indent=4)
            json.dump(result_spot, hf, ensure_ascii=False, indent=4)
            print('Write file success')
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
            # await asyncio.create_task(write_to_file())
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


async def get_spot_binance():
    pairs = '/'.join([i.lower() + '@miniTicker' for i in valuable_pairs])
    url = f'wss://stream.binance.com:9443/stream?streams={pairs}'
    # url = 'wss://stream.binance.com:9443/stream?streams=!ticker@arr'  # все пары сразу

    async with websockets.connect(url) as client:
        while True:
            # await asyncio.create_task(write_to_file())
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


async def main():
    tb = asyncio.create_task(get_spot_binance())
    th = asyncio.create_task(get_spot_huobi())
    wtf = asyncio.create_task(write_to_file())
    us = asyncio.create_task(update_sheets())
    for task in [tb, th, wtf, us]:
        await task


# if __name__ == '__main__':
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     asyncio.run(main())

import websocket
import _thread
import time
import rel

def on_message(ws, message):
    print(message)


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


def on_open(ws):
    print("Opened connection")


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/stream",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever(dispatcher=rel)  # Set dispatcher to automatic reconnection
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
