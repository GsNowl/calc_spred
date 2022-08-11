import datetime
import gzip
import json
import time


import websockets
import asyncio
from config import SLEEP_TIME
from calculator import calc

huobi_spot = dict()
binance_spot = dict()
bybit_spot = {"for_sell": {},
              "for_buy": {}}

spot = {"binance": dict(),
        "huobi": {"for_sell": {},
                  "for_buy": {}},
        "bybit": {"for_sell": {},
                  "for_buy": {}}
        }

valuable_pairs = ["USDTRUB", "BTCUSDT", "BTCBUSD", "BTCRUB", "BUSDUSDT", "BUSDRUB", "BNBBTC",
                  "BNBBUSD", "BNBETH", "BNBRUB", "ETHUSDT", "ETHBTC", "ETHBUSD", "ETHRUB",
                  "SHIBUSDT", "SHIBBUSD"]


async def write_to_file():
    while True:
        with open("spot.json", "w", encoding="utf-8") as file:
            json.dump(spot, file, ensure_ascii=False, indent=4)
        print(datetime.datetime.now(), spot, 'write_to_file')
        await asyncio.sleep(SLEEP_TIME)


async def get_spot_huobi():
    url1 = "wss://api.huobi.pro/ws"
    # url2 = "wss://api-aws.huobi.pro/feed"

    async with websockets.connect(url1) as client:
        # await client.send(json.dumps({"sub": f"market.btcusdt.depth.step0", "symbol": "btcusdt", "id": "id1"}))

        for ticket in ["btcusdt", "ethusdt", "bnbusdt", "usdtrub", "shibusdt", "btcrub", "ethbtc"]:
            # Get offers from stock glass
            await client.send(json.dumps({"sub": f"market.{ticket}.depth.step0", "symbol": ticket, "id": "id1"}))

            # Get ticket
            # await client.send(json.dumps({"sub": f"market.{ticket}.ticker", "symbol": ticket, "id": "id1"}))

        while True:
            # await asyncio.create_task(write_to_file())
            # try:
            data = json.loads(gzip.decompress(await client.recv()).decode("utf-8"))

            keys = data.keys()

            if "ping" in keys:
                await client.send(json.dumps({"pong": data["ping"]}))
                print(datetime.datetime.now(), "Client send pong", data["ping"], 'BYBIT', 'get_spot_huobi')

            elif "ch" in keys:
                ticket = data["ch"].split(".")[1].upper()
                tick = data["tick"]
                # print(tick)

                sell = tick["bids"][0][0]
                buy = tick["asks"][0][0]
                spot["huobi"]["for_sell"][ticket] = sell
                spot["huobi"]["for_buy"][ticket] = buy
                # print(f"{ticket} -> FOR SELL: {sell}; FOR BUY: {buy}")

                # course = tick["ask"]
                # print(f"{ticket} -> {course}")
                # huobi_spot[ticket] = course

            else:
                print(datetime.datetime.now(), data, 'get_spot_huobi')

            # except Exception as e:
            #     print("Error: ", e)


async def get_spot_binance():
    pairs = "/".join([i.lower() + "@miniTicker" for i in valuable_pairs])
    url = f"wss://stream.binance.com:9443/stream?streams={pairs}"
    # url = "wss://stream.binance.com:9443/stream?streams=!ticker@arr"  # все пары сразу
    # url = "wss://stream.binance.com:9443/stream"

    async with websockets.connect(url) as client:
        # await client.send(await websockets.protocol.WebSocketCommonProtocol().pong(10))
        # print(await client.recv())
        #
        # await client.send(json.dumps({
        #     "method": "SUBSCRIBE",
        #     "params":
        #         [
        #             "!ticker@arr"
        #         ],
        #     "id": 1
        # }))

        while True:
            try:
                r = await client.recv()
                # print(r)

                # now_time = time.time()
                # if now_time - start >= 2:
                #     await client.send(json.dumps({
                #         "method": "GET_PROPERTY",
                #         "property": "ping",
                #         "id": 3
                #     }))
                #     start = now_time

                data = json.loads(r)["data"]
                pair = data["s"]
                price = float(data["c"])
                spot["binance"][pair] = price

            except websockets.ConnectionClosed:
                continue
            except KeyError:
                print(datetime.datetime.now(), r, 'get_spot_binance')


async def get_spot_bybit():
    async with websockets.connect("wss://stream.bybit.com/spot/quote/ws/v1") as client:
        simple_time = time.time()
        start_time = int(str(simple_time)[:14].replace(".", ""))
        await client.send(json.dumps({"ping": start_time}))
        print(datetime.datetime.now(), await client.recv(), 'get_spot_bybit')

        await client.send(
            '{"symbol":"BTCUSDT,ETHUSDT,BUSDUSDT,BNBUSDT,SHIBUSDT,ETHBTC","topic":"depth","event":"sub","params":{"binary":false}}')

        while True:
            now_time = time.time()
            if (now_time - simple_time) >= 10:
                simple_time = now_time
                await client.send(json.dumps({"ping": int(str(now_time)[:14].replace(".", ""))}))
                print(datetime.datetime.now(), "Send ping", simple_time, 'HUOBI', 'get_spot_bybit')

            response = json.loads(await client.recv())
            if "pong" in response:
                print(datetime.datetime.now(), "Ping received", response["pong"], 'HUOBI', 'get_spot_bybit')
                continue

            symbol = response["symbol"]
            bid_ask = response["data"][0]
            bid = bid_ask["b"][0]
            ask = bid_ask["a"][0]
            spot["bybit"]["for_sell"][symbol] = float(bid[0])
            spot["bybit"]["for_buy"][symbol] = float(ask[0])

            # print(symbol, "for buy", ask[0], "for sell", bid[0])
            # print(bybit_spot)


async def main():
    binance = asyncio.create_task(get_spot_binance())
    huobi = asyncio.create_task(get_spot_huobi())
    bybit = asyncio.create_task(get_spot_bybit())
    c = asyncio.create_task(calc())
    # us = asyncio.create_task(update_sheets())

    for task in [binance, huobi, bybit, c]:
        await task

    # await asyncio.create_task(get_spot_binance())


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

