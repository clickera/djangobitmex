import json
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from .models import Account
from .bitmex import BitmexWS


class Consumer(WebsocketConsumer):
    bitmex_wss: dict

    def connect(self):
        self.accept()
        self.bitmex_wss = {}

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        if data.get('action') == 'subscribe':
            if self.bitmex_wss.get(data.get('account')) and data.get('symbol') == self.bitmex_wss[data['account']].symbol:
                return self._send({"status": "OK"})
            else:
                if self.bitmex_wss.get(data.get('account')):
                    self.unsubscribe(data)
                return self.subscribe(data)
        elif data.get('action') == "unsubscribe":
            if not self.bitmex_wss.get(data.get('account')):
                self._send({"status": "OK"})
            else:
                return self.unsubscribe(data)

        self.send(text_data=json.dumps({
            "status": "Error",
            "message": "Invalid command"
        }))

    def _send(self, data):
        return self.send(text_data=json.dumps(data))

    def subscribe(self, data):
        try:
            account = Account.objects.get(name=data['account'])
            self.bitmex_wss[account.name] = BitmexWS(
                self,
                account.name,
                endpoint="https://testnet.bitmex.com/api/v1",
                symbol=data['symbol'],
                api_key=account.api_key,
                api_secret=account.api_secret,
            )
            self._send({
                "status": "OKay"
            })
        except ObjectDoesNotExist:
            self._send({
                "status": "Error",
                "message": "Account not found"
            })

    def unsubscribe(self, data):
        try:
            account = Account.objects.get(name=data['account'])
            self.bitmex_wss[account.name].close()
            del self.bitmex_wss[account.name]
            self._send({
                "status": "OK",
            })
        except ObjectDoesNotExist:
            self._send({
                "status": "Error",
                "message": "Account not found"
            })

    def disconnect(self, code):
        for k in self.bitmex_wss:
            self.bitmex_wss[k].close()
        self.bitmex_wss = {}