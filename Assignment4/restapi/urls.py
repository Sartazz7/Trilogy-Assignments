from django.urls import path
from django.conf.urls import include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from restapi.views import *


router = DefaultRouter()
router.register('users', UserViewSet)
router.register('categories', CategoryViewSet)
router.register('groups', GroupViewSet)
router.register('expenses', ExpenseViewSet)

urlpatterns = [
    path('', index, name='index'),
    path('auth/logout/', logout),
    path('auth/login/', views.obtain_auth_token),
    path('balances/', balance),
    path('process-logs/', logProcessor),
    path('api/', include(router.urls))
]

