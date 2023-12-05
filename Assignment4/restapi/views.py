# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal

from django.http import HttpResponse
from django.contrib.auth.models import User

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, action, authentication_classes, permission_classes
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

from restapi.models import *
from restapi.serializers import *
from restapi.custom_exception import *
from restapi.utils import *
from restapi.constants import *


def index(_request):
    return HttpResponse("Hello, world. You're at Rest.")

class ExpenseViewSet(ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user = self.request.user
        expenses = Expense.objects.filter(users__in=user.expenses.all())
        if self.request.query_params.get('q', None) is not None:
            expenses = expenses.filter(description__icontains=self.request.query_params['q'])
        return expenses


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = [ActionConstants.GET.value, ActionConstants.POST.value]

class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = [ActionConstants.GET.value, ActionConstants.POST.value]

    def get_queryset(self):
        user = self.request.user
        groups = user.members.all()
        if self.request.query_params.get('q', None) is not None:
            groups = groups.filter(name__icontains=self.request.query_params['q'])
        return groups

    def create(self, request, *args, **kwargs):
        user = self.request.user
        data = self.request.data
        if data.get('name', None) is None:
            raise KeyNotFoundException()
        members = [] if data.get('members', None) is None else data['members']
        group = Group(name = data['name'], members = members)
        group.save()
        group.members.add(user)
        serializer = self.get_serializer(group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=[ActionConstants.PUT.value], detail=True)
    def members(self, request, pk=None):
        group = Group.objects.get(id=pk)
        if group not in self.get_queryset():
            raise UnauthorizedUserException()
        body = request.data
        if body.get('add', None) is not None and body['add'].get('user_ids', None) is not None:
            added_ids = body['add']['user_ids']
            for user_id in added_ids:
                group.members.add(user_id)
        if body.get('remove', None) is not None and body['remove'].get('user_ids', None) is not None:
            removed_ids = body['remove']['user_ids']
            for user_id in removed_ids:
                group.members.remove(user_id)
        group.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=[ActionConstants.GET.value], detail=True)
    def expenses(self, _request, pk=None):
        group = Group.objects.get(id=pk)
        if group not in self.get_queryset():
            raise UnauthorizedUserException()
        expenses = group.expenses_set
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=[ActionConstants.GET.value], detail=True)
    def balances(self, _request, pk=None):
        group = Group.objects.get(id=pk)
        if group not in self.get_queryset():
            raise UnauthorizedUserException()
        expenses = Expense.objects.filter(group=group)
        dues = {}
        for expense in expenses:
            userBalances = UserExpense.objects.filter(expense=expense)
            for userBalance in userBalances:
                dues[userBalance.user] = dues.get(userBalance.user, 0) + userBalance.amount_lent - userBalance.amount_owed
        balances = UtilityService.getBalancesFromDues(dues)

        return Response(balances, status=status.HTTP_200_OK)

@api_view([APIConstants.POST.value])
def logout(request):
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view([APIConstants.GET.value])
def balance(request):
    user = request.user
    expenses = Expense.objects.filter(users__in=user.expenses.all())
    final_balance = {}
    for expense in expenses:
        user_balances = expense.users.all()
        dues = {}
        for user_balance in user_balances:
            dues[user_balance.user] = dues.get(user_balance.user, 0) + user_balance.amount_lent - user_balance.amount_owed
        expense_balances = UtilityService.getBalancesFromDues(dues)
        for eb in expense_balances:
            from_user = eb['from_user']
            to_user = eb['to_user']
            if from_user == user.id:
                final_balance[to_user] = final_balance.get(to_user, 0) - eb['amount']
            if to_user == user.id:
                final_balance[from_user] = final_balance.get(from_user, 0) + eb['amount']
    final_balance = {k: v for k, v in final_balance.items() if v != 0}

    response = [{"user": k, "amount": int(v)} for k, v in final_balance.items()]
    return Response(response, status=status.HTTP_200_OK)

@api_view([APIConstants.POST.value])
@authentication_classes([])
@permission_classes([])
def logProcessor(request):
    data = request.data
    numThreads = data['parallelFileProcessingCount']
    logFiles = data['logFiles']
    if numThreads <= 0 or numThreads > 30:
        return Response(
            {
                "status": "failure",
                "reason": "Parallel Processing Count out of expected bounds"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    if len(logFiles) == 0:
        return Response(
            {
                "status": "failure",
                "reason": "No log files provided in request"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    logsCollector = LogsCollector()
    logs = logsCollector.loopedReader(urls=data['logFiles'], numThreads=data['parallelFileProcessingCount'])
    sortedLogs = logsCollector.sortByTimeStamp(logs)
    cleaned = logsCollector.transform(sortedLogs)
    data = logsCollector.aggregate(cleaned)
    response = logsCollector.responseFormat(data)

    return Response({"response":response}, status=status.HTTP_200_OK)


@api_view([APIConstants.POST.value])
@permission_classes([])
def startCollection(request):
    data = request.data
    collection_resource = data['collection_resource']
    export_to = data['export_to']

    if collection_resource == "metrics":
        metricsCollector = MetricsCollector()
        metrics = metricsCollector.getMetricsDataFromS3()
        transformedMetrics = metricsCollector.transformMetrics(metrics)
        if export_to == "local":
            metricsCollector.writeMetricsDataToFile(transformedMetrics)
        else:
            metricsCollector.writeMetricsDataToS3(transformedMetrics)
    else:
        signalsCollector = SignalsCollector()
        signals = signalsCollector.fetchSignalsData()
        convertedSignals = signalsCollector.processSignal(signals)
        if export_to == "local":
            signalsCollector.saveSignalsToPickle(convertedSignals)
        else:
            signalsCollector.saveSignalsToS3(convertedSignals)

