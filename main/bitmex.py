import time
import asyncio
import threading
import websockets
from bravado.exception import HTTPBadRequest
import signal
import json

import bitmex
from bitmex_websocket import BitMEXWebsocket


class Bitmex:
    def __init__(self, key, secret):
        self.client = bitmex.bitmex(True, api_secret=secret, api_key=key)

    def new_order(self, data):
        try:
            result = self.client.Order.Order_new(
                ordType=data.get('orderType', 'Market'),
                symbol=data.get('symbol', 'XBTCUSD'),
                orderQty=data['volume'],
                side=data.get('side', 'Buy'),
                # price=data.get('price')
            )
            result = result.result()
        except HTTPBadRequest as e:
            print("Error create order")
            errormessage = e.response.json()['error']['message']
            return {
                "error": True,
                "message": errormessage,
                "errorcode": e.status_code
            }
        if result and result.get('orderID'):
            return {
                "order_id": result['orderID'],
                "timestamp": result['timestamp'],
                "price": result['price'],
                "error": False
            }
        return {
            "error": True,
            "message": result.strerror
        }

    def amend_order(self, data, order_id):
        self.client.Order.Order_amend(
            orderID=order_id,
            orderQty=data['orderQty'],
        )

    def delete_order(self, order_id):
        try:
            self.client.Order.Order_cancel(orderID=order_id)
            return True
        except:
            return False


class BitmexInstrumentAsync:
    task: asyncio.Task = None

    def __init__(self, symbol: str):
        self.symbol = symbol

    async def connect(self):
        url = f"wss://testnet.bitmex.com/realtime?subscribe=instrument:{self.symbol}"
        async with websockets.connect(url) as ws:
            async for message in ws:
                message = dict(json.loads(message))
                if message.get('action') == 'partial':
                    await self.on_message(message.get('data')[0])
                elif message.get('action') == 'update' and message.get('data')[0].get('lastPrice'):
                    await self.on_message(message.get('data')[0])

    async def on_message(self, data: dict):
        pass

    async def watch(self):
        self.task = asyncio.create_task(self.connect())

    async def close(self):
        self.task.cancel()


class BitmexWS(BitmexInstrumentAsync):
    def __init__(self, context, account_name, symbol: str, **kwargs):
        self.context = context
        self.symbol = symbol
        self.account_name = account_name

    async def on_message(self, data):
        await self.context._send({
            'timestamp': data['timestamp'],
            'account': self.account_name,
            'symbol': data['symbol'],
            'price': data['lastPrice']
        })

    async def watch(self):
        await super().watch()

    async def close(self):
        await super().close()