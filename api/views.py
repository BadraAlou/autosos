from turtle import distance
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.generics import ListCreateAPIView,CreateAPIView
from .utils import calculer_prix_par_distance,haversine_distance
from math import radians, cos, sin, asin, sqrt
from.serializers import *
from.models import *
from rest_framework.generics import ListAPIView
# Create your views here.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_client_info(request):
    try:
        client = Client.objects.get(user=request.user)
        serializer = ClientSerializer(client)
        return Response(serializer.data)
    except Client.DoesNotExist:
        return Response({"error": "Client not found"}, status=404)
###################inscription de l'utilisateur:depuis fronted flutter #################
@api_view(['POST'])
@permission_classes([])
def register_user(request):
    username = request.data.get('username') 
    password = request.data.get('password')
    telephone = request.data.get('telephone')
    adresse = request.data.get('adresse')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    # Vérifie si un User avec ce nom existe déjà
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Ce nom d\'utilisateur est déjà pris.'}, status=status.HTTP_400_BAD_REQUEST)

    # Crée le User
    user = User.objects.create_user(username=username, password=password)

    # Vérifie s'il est déjà lié à un autre profil (ceinture de sécurité)
    if DepanneurExterne.objects.filter(user=user).exists():
        user.delete()  # rollback
        return Response({'error': 'Ce compte est déjà enregistré comme dépanneur.'}, status=status.HTTP_400_BAD_REQUEST)

    # Création du profil Client
    client = Client.objects.create(
        user=user,
        telephone=telephone,
        adresse=adresse,
        latitude=latitude if latitude else None,
        longitude=longitude if longitude else None
    )

    return Response({'message': 'Client inscrit avec succès'}, status=status.HTTP_201_CREATED)



#####ma posititon GPS ####################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_position(request):
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    try:
        client = request.user.client  # Assure-toi que le modèle Client est lié en OneToOne avec User
        if latitude and longitude:
            client.latitude = latitude 
            client.longitude = longitude
            client.save()
            return Response({'message': 'Position mise à jour.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Latitude ou longitude manquante.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({'token': token.key})


#pour la presence du client dans la page depannage######"
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_presence(request):
    client = request.user.client
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if latitude and longitude:
        client.latitude = latitude if latitude else None,
        client.longitude = longitude if latitude else None,
        client.save()

        # Optionnel : envoyer une notification ou un websocket signal au dépanneur externe

        return Response({"status": "ok"}, status=200)
    return Response({"error": "latitude et longitude requis"}, status=400)











class ClientList(generics.ListAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_position_depanneur(request):
    depannage_id = request.data.get("depannage_id")
    lat = request.data.get("latitude")
    long = request.data.get("longitude")

    try:
        depannage = Depannage.objects.get(id=depannage_id)
    except Depannage.DoesNotExist:
        return Response({"error": "Demande introuvable"}, status=404)

    suivi, created = DemandeDepannage.objects.get_or_create(depannage=depannage)
    suivi.depanneur_latitude = lat
    suivi.depanneur_longitude = long
    suivi.save()

    return Response({"message": "Position du dépanneur mise à jour"})

   

class DepanneurList(APIView):#ça se presente comme au niveau de l'api avec plusieur details sur le Depanneur 
    def get(self, request):
        depanneurs = Depanneur.objects.all()
        depanneurs = Depanneur.objects.filter(disponibilite=True)
        serializer = DepanneurSerializer(depanneurs, many=True)
        return Response({"depanneurs": serializer.data})
class Depanneur_List(APIView):#pour uune liste de depanneur dans notre qui sont dans notre base de donnée en fonction de 
    def get(self, request):
        depanneurs = Depanneur.objects.filter(disponibilite=True)
        serializer = DepanneurSerializer(depanneurs, many=True)
        return Response(serializer.data)  # ✅ retourne directement une liste

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suivi_depanneur(request, depannage_id):
    try:
        depannage = Depannage.objects.get(id=depannage_id)
        depanneur = depannage.depanneur
        return Response({
            "latitude": depanneur.latitude,
            "longitude": depanneur.longitude
        })
    except:
        return Response({"error": "Suivi non disponible"}, status=404)
    




######iscrire le depanneur externe######################
class DepanneurExterneInscriptionView(APIView):
    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Ce nom d’utilisateur existe déjà.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password)

        # Sécurité : ne pas créer de dépanneur si déjà Client
        if Client.objects.filter(user=user).exists():
            user.delete()
            return Response({'error': 'Ce compte est déjà enregistré comme client.'}, status=status.HTTP_400_BAD_REQUEST)

        depanneur_data = {
            'user': user.id,
            'entreprise': data.get('entreprise'),
            'expertise': data.get('expertise'),
            'tel': data.get('tel'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
        }

        serializer = DepanneurExterneSerializer(data=depanneur_data)
        if serializer.is_valid():
            serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Inscription réussie',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'depanneur': serializer.data
            }, status=status.HTTP_201_CREATED)

        user.delete()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DepannageCreateView(CreateAPIView):
    serializer_class = DepannageSerializer

    def perform_create(self, serializer):
        # Cherche un dépanneur disponible
        depanneur_disponible = Depanneur.objects.filter(disponibilite=True).first()
        if depanneur_disponible:
            serializer.save(depanneur=depanneur_disponible, client=self.request.user.client)
            # Le dépanneur devient occupé
            depanneur_disponible.disponibilite = False
            depanneur_disponible.save()
        else:
            serializer.save(client=self.request.user.client)





#####depannage#######
class DepannageList(ListAPIView):
    queryset = Depannage.objects.all()
    serializer_class = DepannageSerializer

class DepannageViewSet(viewsets.ModelViewSet):#recuperer les champs au nivzeaux 
    queryset = Depannage.objects.all()
    serializer_class = DepannageSerializer



#==========================crree une demande de depannage===################"
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_demande_depannage(request):
    user = request.user
    try:
        client = Client.objects.get(user=user)
    except Client.DoesNotExist:
        return Response({"error": "Client introuvable."}, status=404)

    data = request.data
    depanneur_id = data.get('depanneur')
    type_depannage = data.get('type_depannage')
    description = data.get('description')
    location = data.get('location', '')  # optionnel
    client_lat = data.get('client_latitude')
    client_long = data.get('client_longitude')

    # Vérifie que le dépanneur est dispo
    try:
        depanneur = Depanneur.objects.get(id=depanneur_id, disponibilite=True)
    except Depanneur.DoesNotExist:
        return Response({"error": "Dépanneur introuvable ou indisponible."}, status=404)

    # Distance facultative (si coordonnées présentes)
    prix_total = 1000  # minimum
    distance_km = None
    if client_lat is  not None and client_long is not None:
        try:
            client_lat = float(client_lat)
            client_long = float(client_long)
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                return R * c

            distance_km = haversine(client_lat, client_long, depanneur.latitude, depanneur.longitude)
            prix_total = max(1000, distance_km * 500)
        except ValueError:
            return Response({"error": "Latitude/longitude invalide."}, status=400)

    # Création de la demande
    depannage = Depannage.objects.create(
        client=client,
        depanneur=depanneur,
        type_depannage=type_depannage,
        description=description,
        location=location,
        prix=round(prix_total, 2),
        client_latitude=client_lat if client_lat else None,
        client_longitude=client_long if client_long else None,
        status='en_attente'
    )

    return Response({
    "message": "Demande envoyée",
    "depannage_id": depannage.id,
    "prix": prix_total,
    "distance_km": round(distance_km, 2),
    "depanneur": DepanneurSerializer(depanneur).data
}, status=status.HTTP_201_CREATED)



#===== UNE DEMANDE DE REMORQUAGE AVEC 20% de frais de commission pour l'entreprise=======#


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_demande_remorquage(request):
    user = request.user
    try:
        client = Client.objects.get(user=user)
    except Client.DoesNotExist:
        return Response({"error": "Client introuvable."}, status=404)

    data = request.data
    depanneur_id = data.get('depanneur')
    description = data.get('description')
    location = data.get('location', '')
    client_lat = data.get('client_latitude')
    client_long = data.get('client_longitude')

    try:
        depanneur = Depanneur.objects.get(id=depanneur_id, disponibilite=True, expertise__icontains="remorquage")
    except Depanneur.DoesNotExist:
        return Response({"error": "Dépanneur remorquage introuvable ou indisponible."}, status=404)

    prix_base = 0
    distance_km = None

    if client_lat is not None and client_long is not None:
        try:
            client_lat = float(client_lat)
            client_long = float(client_long)

            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
                c = 2 * asin(sqrt(a))
                return R * c

            distance_km = haversine(client_lat, client_long, depanneur.latitude, depanneur.longitude)

            # Tarifs en fonction des paliers de distance
            if distance_km <= 10:
                prix_base = 5000
            elif distance_km <= 20:
                prix_base = 8000
            elif distance_km <= 30:
                prix_base = 12000
            elif distance_km <= 50:
                prix_base = 18000
            else:
                prix_base = 25000  # au-delà de 50 km

        except ValueError:
            return Response({"error": "Latitude/longitude invalide."}, status=400)

    # Ajouter les frais de service (20%)
    frais_service = prix_base * 0.20
    prix_total = prix_base + frais_service

    depannage = Depannage.objects.create(
        client=client,
        depanneur=depanneur,
        type_depannage="remorquage",
        description=description,
        location=location,
        prix=round(prix_total, 2),
        client_latitude=client_lat,
        client_longitude=client_long,
        status='en_attente'
    )

    return Response({
        "message": "Demande de remorquage envoyée",
        "depannage_id": depannage.id,
        "prix_base": round(prix_base, 2),
        "frais_service": round(frais_service, 2),
        "prix_total": round(prix_total, 2),
        "distance_km": round(distance_km, 2) if distance_km else None,
        "depanneur": DepanneurSerializer(depanneur).data
    }, status=status.HTTP_201_CREATED)
@api_view(['GET'])
def paliers_remorquage(request):
    paliers = [
        {"limite": 10, "prix": 5000},
        {"limite": 20, "prix": 8000},
        {"limite": 30, "prix": 12000},
        {"limite": 50, "prix": 18000},
        {"limite": "inf", "prix": 25000},  # Changer ici
    ]
    return Response({"paliers": paliers})








class DemandeDepannageList(ListAPIView):
    queryset = DemandeDepannage.objects.all()
    serializer_class = DemandeDepannageSerializer


class AvisList(ListAPIView):
    queryset = Avis.objects.all()
    serializer_class = AvisSerializer

#vue pour le calcule a distance 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estimer_prix_depannage(request):
    client = request.user.client
    depanneur_id = request.data.get('depanneur_id')
    
    try:
        depanneur = Depanneur.objects.get(id=depanneur_id)
    except Depanneur.DoesNotExist:
        return Response({'error': 'Dépanneur introuvable'}, status=404)

    if not (client.latitude and client.longitude and depanneur.latitude and depanneur.longitude):
        return Response({'error': 'Coordonnées GPS manquantes'}, status=400)

    prix, distance = calculer_prix_par_distance(
        client.latitude, client.longitude,
        depanneur.latitude, depanneur.longitude
    )

    return Response({
        'prix_estime': prix,
        'distance_km': distance
    })


class PaiementList(ListAPIView):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

##################### # payement # ##################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enregistrer_paiement(request):
    user = request.user
    depannage_id = request.data.get('depannage_id')
    montant = request.data.get('montant')
    transaction = request.data.get('transaction')

    try:
        depannage = Depannage.objects.get(id=depannage_id, client__user=user)
    except Depannage.DoesNotExist:
        return Response({"error": "Demande introuvable."}, status=404)

    if Paiement.objects.filter(depannage=depannage).exists():
        return Response({"error": "Paiement déjà effectué."}, status=400)

    Paiement.objects.create(
        depannage=depannage,
        montant=montant,
        statut="payé",
        transaction=transaction
    )

    depannage.status = "en_cours"
    depannage.save()

    return Response({"message": "Paiement validé, le dépanneur peut être informé."})




# views.py
class mes_demandesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        depannages = Depannage.objects.filter(client__user=request.user)
        serializer = DepannageSerializer(depannages, many=True)
        return Response(serializer.data)
    




class MessageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        demande_id = self.request.query_params.get('demande')
        if demande_id:
            return Message.objects.filter(demande_id=demande_id)
        return Message.objects.none()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)





class UpdateDepanneurPositionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if latitude is None or longitude is None:
            return Response({'error': 'Latitude et longitude requises'}, status=400)

        try:
            # On force l'utilisation d'un compte lié à DepanneurExterne uniquement
            depanneur = request.user.depanneurexterne
        except:
            return Response({'error': 'Accès réservé aux dépanneurs externes'}, status=403)

        depanneur.latitude = latitude
        depanneur.longitude = longitude
        depanneur.save()

        return Response({'message': 'Position mise à jour'}, status=200)
