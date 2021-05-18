import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from asgiref.sync import sync_to_async

from .models import Account
from .bitmex import BitmexWS


class Consumer(AsyncWebsocketConsumer):
    bitmex_wss: dict

    async def websocket_connect(self, message):
        await self.accept()
        self.bitmex_wss = {}

    async def websocket_receive(self, message):
        data = json.loads(message['text'])

        if data.get('action') == 'subscribe':
            if self.bitmex_wss.get(data.get('account')) and data.get('symbol') == self.bitmex_wss[data['account']].symbol:
                await self._send({"status": "OK"})
            else:
                if self.bitmex_wss.get(data.get('account')):
                    await self.unsubscribe(data)
                await self.subscribe(data)
        elif data.get('action') == "unsubscribe":
            if not self.bitmex_wss.get(data.get('account')):
                await self._send({"status": "OK"})
            else:
                await self.unsubscribe(data)
        else:
            await self.send(text_data=json.dumps({
                "status": "Error",
                "message": "Invalid command"
            }))

    async def _send(self, data):
        print(data, dir(data))
        await self.send(text_data=json.dumps(data))

    async  def subscribe(self, data):
        try:
            account = await sync_to_async(lambda: Account.objects.get(name=data['account']), thread_sensitive=False)()
            self.bitmex_wss[account.name] = BitmexWS(
                self,
                account.name,
                endpoint="https://testnet.bitmex.com/api/v1",
                symbol=data['symbol'],
                api_key=account.api_key,
                api_secret=account.api_secret,
            )
            await self.bitmex_wss[account.name].watch()
            await self._send({
                "status": "OKay"
            })
        except ObjectDoesNotExist:
            await self._send({
                "status": "Error",
                "message": "Account not found"
            })

    async def unsubscribe(self, data):
        try:
            account = await sync_to_async(lambda: Account.objects.get(name=data['account']))()
            await self.bitmex_wss[account.name].close()
            del self.bitmex_wss[account.name]
            await self._send({
                "status": "OK",
            })
        except ObjectDoesNotExist:
            await self._send({
                "status": "Error",
                "message": "Account not found"
            })

    async def websocket_disconnect(self, message):
        for k in self.bitmex_wss:
            await self.bitmex_wss[k].close()
        self.bitmex_wss = {}