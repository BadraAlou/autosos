# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Depannage, Message
from django.contrib.auth.models import User
from channels.db import database_sync_to_async

class DemandeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("demandes_en_attente", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("demandes_en_attente", self.channel_name)

    # 👇 Ce nom doit correspondre à "type" dans group_send()
    async def nouvelle_demande(self, event):
        await self.send(text_data=json.dumps({
            "event": "nouvelle_demande",
            "data": event["demande"]
        }))

    # Si jamais tu veux écouter ce que le client envoie
    async def receive(self, text_data):
        print("Reçu du frontend (non utilisé pour l’instant) :", text_data)



async def receive(self, text_data):
    data = json.loads(text_data)
    # Traitement éventuel, par exemple filtrer ou loguer
    print("Message reçu du client:", data)


@database_sync_to_async
def get_user(self, user_id):
    return User.objects.get(id=user_id)



# consumers.py
class ClientNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id = self.scope["user"].id
        self.group_name = f"client_{user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def demande_acceptee(self, event):
        await self.send(text_data=json.dumps(event["demande"]))




class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.depannage_id = self.scope['url_route']['kwargs']['depannage_id']
        self.room_group_name = f'chat_{self.depannage_id}'

        # Rejoindre le groupe
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Réception d’un message
    async def receive(self, text_data):
        data = json.loads(text_data)
        user_id = data['user_id']
        message = data['message']

        await self.save_message(user_id, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user_id': user_id,
                'message': message,
            }
        )

    # Envoi du message à tous les membres du groupe
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'user_id': event['user_id'],
            'message': event['message'],
        }))

    @database_sync_to_async
    def save_message(self, user_id, message):
        user = User.objects.get(id=user_id)
        depannage = Depannage.objects.get(id=self.depannage_id)
        return Message.objects.create(sender=user, demande=depannage, content=message)