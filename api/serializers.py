from rest_framework import serializers
from rest_framework import serializers
from .models import Client, Depanneur, Depannage, DemandeDepannage, Avis, DepanneurExterne, Paiement,Message
from django.contrib.auth.models import User


    


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username','email']

class ClientSerializer(serializers.ModelSerializer):
        username = serializers.CharField(source='user.username')  # 
        
        class Meta:
            model = Client
            fields = ['username', 'telephone', 'adresse', 'longitude', 'latitude']


class DepanneurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depanneur
        fields = ['id', 'nom', 'tel', 'entreprise', 'expertise', 'disponibilite', 'latitude', 'longitude']



class DepanneurExterneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepanneurExterne
        fields = '__all__'


class DemandeExterneSerializer(serializers.Serializer):
    depanneur_externe_id = serializers.IntegerField()
    type_depannage = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    location = serializers.CharField(allow_blank=True, required=False)


class DepannageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depannage
        fields = ['id', 'type_depannage', 'description', 'client_latitude', 'client_longitude']



class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'demande', 'sender', 'sender_username', 'content', 'timestamp']



class DepannageSerializer(serializers.ModelSerializer):
    depanneur = DepanneurSerializer()  # Imbriqué
    depanneur_externe = DepanneurExterneSerializer(read_only=True)
    created_at = serializers.DateTimeField(source='date_depannage', format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = Depannage
        fields = '__all__'

        

class DemandeDepannageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeDepannage
        fields = '__all__'


        

class AvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avis
        fields = '__all__'

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'
