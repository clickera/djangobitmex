import datetime

from django.http import Http404
from django.views.generic import TemplateView
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Order, Account
from .serializers import OrderSerializer
from .bitmex import Bitmex


class OrderView(ModelViewSet):
    parser_classes = [JSONParser]
    serializer_class = OrderSerializer

    def get_queryset(self):
        account_name = self.kwargs.get('account_name')
        if not account_name:
            raise Http404
        return Order.objects.filter(account__name=account_name)

    def create(self, request, *args, **kwargs):
        self.get_queryset()
        data = dict(request.data)
        account = get_object_or_404(Account, name=self.kwargs.get('account_name'))
        if not request.data.get('test'):
            bitmex = Bitmex(account.api_key, account.api_secret)

            result = bitmex.new_order(request.data)
            if result['error']:
                return Response(data={
                    "status": "Error",
                    "message": result['message'],
                    "errorcode": result['errorcode']
                }, status=400)
            data['order_id'] = result['order_id']
            data['timestamp'] = result['timestamp']
            data['price'] = result['price']
            data['account'] = account.id
        else:
            data['order_id'] = 'test_order_id'
            data['timestamp'] = datetime.datetime.today()
            data['price'] = 10.0
            data['account'] = account.id


        serializer = OrderSerializer(data=data)
        if not serializer.is_valid():
            return Response(data={"error": serializer.errors}, status=400)
        serializer.save()

        return Response(data={"status": "OK"}, status=201)

    def destroy(self, request, *args, **kwargs):
        self.get_queryset()
        order_id = kwargs.get('pk')
        order = get_object_or_404(Order, pk=order_id)

        if not request.query_params.get('test'):
            account = get_object_or_404(Account, name=self.kwargs.get('account_name'))
            bitmex = Bitmex(account.api_key, account.api_secret)
            bitmex.delete_order(order.order_id)

        order.delete()

        return Response(data={"status": "OK"}, status=204)


class Index(TemplateView):
    template_name = "index.html"