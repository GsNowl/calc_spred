import json
import time
import asyncio
from aiogram import Bot, types

import config

api_token = '5476190061:AAGH7noOsFROoise3WezQnsmIM7tt_-FLZs'
channel_id = '-1001730407036'
bot = Bot(api_token)


async def calc():
    while True:
        s = time.time()
        profits = dict()
        with open('spot.json', 'r', encoding='utf-8') as file:
            data = json.loads(file.read())
            binance = data['binance']
            huobi = data['huobi']
            bybit = data['bybit']

            for i, j in binance.items():
                huobi_sell = huobi['for_sell']
                bybit_sell = bybit['for_sell']

                if i in huobi_sell.keys():
                    profit = ((huobi_sell[i]-j)/j)*100
                    profits[f'binance_huobi_{i}'] = profit
                if i in bybit_sell.keys():
                    profit = ((bybit_sell[i]-j)/j)*100
                    profits[f'binance_bybit_{i}'] = profit

            for i, j in huobi["for_buy"].items():
                bybit_sell = bybit['for_sell']
                if i in binance.keys():
                    profit = ((binance[i]-j)/j)*100
                    profits[f'huobi_binance_{i}'] = profit
                if i in bybit_sell.keys():
                    profit = ((bybit_sell[i]-j)/j)*100
                    profits[f'huobi_bybit_{i}'] = profit

            for i, j in bybit['for_buy'].items():
                huobi_sell = huobi['for_sell']
                if i in binance.keys():
                    profit = ((binance[i]-j)/j)*100
                    profits[f'bybit_binance_{i}'] = profit
                if i in huobi_sell.keys():
                    profit = ((huobi_sell[i]-j)/j)*100
                    profits[f'bybit_huobi_{i}'] = profit
            # print(sorted(profits.values())[::-1])

        best_spreds = dict()

        for i, j in profits.items():
            if j >= 0:
                best_spreds[i] = j
        await bot.send_message(channel_id, json.dumps(best_spreds))

        print(time.time()-s)

        await asyncio.sleep(config.SLEEP_TIME)

