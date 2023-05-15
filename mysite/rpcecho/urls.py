# rpcecho/urls.py
from django.urls import path

from . import views


urlpatterns = [
    path("", views.room, name="room"),
    path("rpccall", views.rpc_call, name="rpc_call"),
    path("rpccall2", views.rpc_call2, name="rpc_call2"),
]
