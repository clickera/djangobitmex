from django.test import TestCase, client
import time
import json


class Test(TestCase):
    api_url = "/orders/test/"

    def setUp(self):
        from .models import Account
        Account.objects.create(name="test",
                               api_key="48GphC_MTWN_0ntW4V1osU4S",
                               api_secret="-hoVHM9kC1JRwlQBPjYdzosCCpKl7CNtomzyCTGVoLcQ5PSV")
        data = {
            "symbol": "XBTUSD",
            "volume": 1.0,
            "side": "Buy",
            "test": True
        }
        result = client.Client().post(self.api_url, data=data, content_type="application/json")
        assert result.status_code == 201

    def test_get_orders(self):
        result = client.Client().get(self.api_url)
        assert len(result.json()) > 0

    def test_get_order(self):
        result = client.Client().get(self.api_url)
        order_id = result.json()[0].get('id')
        order = client.Client().get(self.api_url + str(order_id) + "/")
        assert order_id == order.json()['id']

    def test_delete_order(self):
        result = client.Client().get(self.api_url)
        order_id = result.json()[0].get('id')
        result = client.Client().delete(self.api_url + str(order_id) + "/?test=true")
        assert result.status_code == 204

    def test_websocket(self):
        pass