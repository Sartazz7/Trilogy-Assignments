# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from constants import Modelsconstants

# Create your models here.
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=Modelsconstants.MAX_LENGTH1.value, null=False)


class Group(models.Model):
    name = models.CharField(max_length=Modelsconstants.MAX_LENGTH2.value, null=False)
    members = models.ManyToManyField(User, related_name='members', blank=True)


class Expense(models.Model):
    description = models.CharField(max_length=Modelsconstants.MAX_LENGTH1.value)
    total_amount = models.DecimalField(max_digits=Modelsconstants.MAX_DIGITS.value, decimal_places=Modelsconstants.DECIMAL_PLACES.value)
    group = models.ForeignKey(Group, null=True, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, default=Modelsconstants.FOREIGN_KEY_DEFAULT.value, on_delete=models.CASCADE)


class UserExpense(models.Model):
    expense = models.ForeignKey(Expense, default=Modelsconstants.FOREIGN_KEY_DEFAULT.value, on_delete=models.CASCADE, related_name="users")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    amount_owed = models.DecimalField(max_digits=Modelsconstants.MAX_DIGITS.value, decimal_places=Modelsconstants.DECIMAL_PLACES.value)
    amount_lent = models.DecimalField(max_digits=Modelsconstants.MAX_DIGITS.value, decimal_places=Modelsconstants.DECIMAL_PLACES.value)

    def __str__(self):
        return f"user: {self.user}, amount_owed: {self.amount_owed} amount_lent: {self.amount_lent}"
