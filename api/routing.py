from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
     re_path(r'ws/demandes/$', consumers.DemandeConsumer.as_view()),
    re_path(r'ws/notifications-client/$', consumers.ClientNotificationConsumer.as_view()),
    re_path(r'ws/chat/(?P<depannage_id>\d+)/$', consumers.ChatConsumer.as_view()),
]
