import time
import threading
from bravado.exception import HTTPBadRequest

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


class BitmexWS(BitMEXWebsocket):
    def __init__(self, context, account_name, **kwargs):
        self.context = context
        self.symbol = kwargs.get('symbol')
        self.account_name = account_name
        super().__init__(**kwargs)
        self.watch()

    def on_message(self, data):
        self.context._send(self.context._send({
            'timestamp': data['timestamp'],
            'account': self.account_name,
            'symbol': data['symbol'],
            'price': data['lastPrice']
        }))

    def watch(self):
        self.thread = Watch(self)
        self.thread.start()

    def close(self):
        self.thread.active = False
        self.exit()


class Watch(threading.Thread):
    active = False

    def __init__(self, context, **kwargs):
        self.context = context
        super().__init__(**kwargs)

    def run(self, *args, **kwargs):
        self.active = True
        last_price = 0
        while self.active:
            instrument = self.context.get_instrument()
            if instrument['lastPrice'] != last_price:
                self.context.on_message(instrument)
                last_price = instrument['lastPrice']
            time.sleep(1)
        print("EXIT")