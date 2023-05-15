# rpcecho/consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer

from nameko.events import event_handler


class ChatConsumer(AsyncWebsocketConsumer):
    channel_layer_alias = "nameko"
    name = "chat_receiver"

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # await self.accept()

    async def disconnect(self, close_code):
        pass

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.greeting_service(
            self.room_group_name, {"type": "chat_message", "message": message}
        )
        with self.channel_layer.rpc_call() as rpc:
            data = rpc.greeting_service.hello(text_data)
        self.channel_layer.pub('emitter_service', 'echo_event', {'data': {'id': 1}, 'success': True})

    message_counter = 0
    # Receive message from room group
    async def chat_message(self, event):
        self.message_counter = self.message_counter + 1
        message = f"{event['message']} c:{self.message_counter}"

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    @event_handler('emitter_service', 'echo_event')
    def receive_message(self, payload):
        self.send(text_data=json.dumps({"payload": payload}))

    async def devnull(self, *args, **kwargs):
        print(args, kwargs)
        pass
