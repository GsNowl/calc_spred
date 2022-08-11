import asyncio
import websockets
import time
import json
import hmac

NAME = 'calc_spred'
API_KEY = 't4de9ADWNW31iTBUx4'
API_SECRET = 'q5icfFz1HG5T7PaWupvDLl53DEoFcO4gtzBY'
url = 'wss://stream.bybit.com/spot/quote/ws/v1'
expires = int((time.time() + 1) * 1000)
signature = str(hmac.new(
                bytes(API_SECRET, "utf-8"),
                bytes(f"GET/realtime{expires}", "utf-8"), digestmod="sha256"
                ).hexdigest())

bybit_spot = {'for_sell': {},
              'for_buy': {}}


async def get_spot_bybit():
    async with websockets.connect('wss://stream.bybit.com/spot/quote/ws/v1') as client:
        simple_time = time.time()
        start_time = int(str(simple_time)[:14].replace('.', ''))
        await client.send(json.dumps({"ping": start_time}))
        print(await client.recv())

        await client.send('{"symbol":"BTCUSDT,ETHUSDT,BUSDUSDT,BNBUSDT,SHIBUSDT,ETHBTC","topic":"depth","event":"sub","params":{"binary":false}}')

        while True:
            now_time = time.time()
            if (now_time-simple_time) >= 10:
                simple_time = now_time
                await client.send(json.dumps({"ping": int(str(now_time)[:14].replace('.', ''))}))
                print('Send ping', simple_time)

            response = json.loads(await client.recv())
            if 'pong' in response:
                print('Ping received', response['pong'])
                continue

            symbol = response['symbol']
            bid_ask = response['data'][0]
            bid = bid_ask['b'][0]
            ask = bid_ask['a'][0]
            bybit_spot['for_sell'][symbol] = bid[0]
            bybit_spot['for_buy'][symbol] = ask[0]
            print(symbol, 'for buy', ask[0], 'for sell', bid[0])
            print(bybit_spot)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(get_spot_bybit())
