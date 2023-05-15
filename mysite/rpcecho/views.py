# rpcecho/views.py
from django.shortcuts import render
from channels.layers import get_channel_layer
from django.http import JsonResponse


def room(request):
    return render(request, "rpcecho/room.html", {"room_name": "nameko"})


async def rpc_call(request):
    channel_layer = get_channel_layer(alias="nameko")
    retval = channel_layer.call("sq_website_service", "hello", "Hello there!")
    return JsonResponse(retval, safe=False)


async def rpc_call2(request):
    channel_layer = get_channel_layer(alias="nameko")
    retval = channel_layer.ampq()
    return JsonResponse(retval, safe=False)
