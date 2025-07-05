from turtle import distance
import uuid
import requests
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
import stripe
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

#crree une demande de depannage################"
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
    location = data.get('location', '')
    client_lat = data.get('client_latitude')
    client_long = data.get('client_longitude')

    try:
        depanneur = Depanneur.objects.get(id=depanneur_id, disponibilite=True)
    except Depanneur.DoesNotExist:
        return Response({"error": "Dépanneur introuvable ou indisponible."}, status=404)

    # Définir les prix fixes par type de panne
    prix_type = {
        'pneu': 2500,
        'batterie': 3000,
        'moteur': 35000,
        'autre': 40000,  # prix fixe pour "autre"
    }

    prix_base = prix_type.get(type_depannage.lower(), 1500)  # si type inconnu, 1500
    distance_km = None

    # Calculer la distance si position fournie
    if client_lat is not None and client_long is not None:
        try:
            client_lat = float(client_lat)
            client_long = float(client_long)

            def haversine(lat1, lon1, lat2, lon2):
                from math import radians, cos, sin, asin, sqrt
                R = 6371
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                return R * c

            distance_km = haversine(client_lat, client_long, depanneur.latitude, depanneur.longitude)
            prix_distance = distance_km * 600
            prix_base = max(prix_base, prix_distance)
        except ValueError:
            return Response({"error": "Latitude/longitude invalide."}, status=400)

    # Ajouter les 10 % de frais dans le prix final
    prix_total = round(prix_base * 1.10)

    # Créer la demande
    depannage = Depannage.objects.create(
        client=client,
        depanneur=depanneur,
        type_depannage=type_depannage,
        description=description,
        location=location,
        prix=prix_total,
        client_latitude=client_lat,
        client_longitude=client_long,
        status='en_attente'
    )

    return Response({
        "message": "Demande envoyée",
        "depannage_id": depannage.id,
        "prix": prix_total,
        "distance_km": round(distance_km, 2) if distance_km else None,
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

    # Récupération du type de remorquage à partir du frontend
    type_remorquage = data.get('type_remorquage', 'remorquage')  # 'simple', 'avec_reparation' ou 'remorquage'

    if type_remorquage not in ['remorquage', 'simple', 'avec_reparation']:
        return Response({"error": "Type de remorquage invalide."}, status=400)

    # Récupérer le dépanneur disponible
    try:
        depanneur = Depanneur.objects.get(
            id=depanneur_id,
            disponibilite=True,
            expertise__icontains="remorquage"
        )
    except Depanneur.DoesNotExist:
        return Response({"error": "Dépanneur remorquage introuvable ou indisponible."}, status=404)

    # Tarification selon le type
    if type_remorquage == "avec_reparation":
        prix_fixe = 15500
    elif type_remorquage == "simple":
        prix_fixe = 8500
    else:  # par défaut "remorquage" général
        prix_fixe = 8500

    prix_km = 700
    distance_km = None
    prix_base = prix_fixe

    # Calcul distance
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
            prix_base += distance_km * prix_km

        except ValueError:
            return Response({"error": "Latitude/longitude invalide."}, status=400)

    # Commission ou frais de service
    frais_service = prix_base * 0.20
    prix_total = prix_base + frais_service

    # Enregistrement cohérent dans le champ `type_depannage`
    depannage = Depannage.objects.create(
        client=client,
        depanneur=depanneur,
        type_depannage=type_remorquage,  # ← correspond aux choix du modèle
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
        "type_remorquage": type_remorquage,
        "prix_fixe": prix_fixe,
        "distance_km": round(distance_km, 2) if distance_km else None,
        "tarif_distance": round(distance_km * prix_km, 2) if distance_km else None,
        "frais_service": round(frais_service, 2),
        "prix_total": round(prix_total, 2),
        "depanneur": DepanneurSerializer(depanneur).data
    }, status=status.HTTP_201_CREATED)





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

#>>>>>>>>>>>>>>>>>>>>>>>>>> # payement # # #<<<<<<<<<<<<<<<<<<<<<<<<<#
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enregistrer_paiement(request):
    user = request.user
    depannage_id = request.data.get('depannage_id')
    montant = request.data.get('montant')
    payment_intent_id = request.data.get('payment_intent_id')  # ID du PaymentIntent Stripe

    try:
        depannage = Depannage.objects.get(id=depannage_id, client__user=user)
    except Depannage.DoesNotExist:
        return Response({"error": "Demande introuvable."}, status=404)

    if Paiement.objects.filter(depannage=depannage).exists():
        return Response({"error": "Paiement déjà effectué."}, status=400)

    # Vérifier le paiement avec Stripe
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status != 'succeeded':
            return Response({"error": "Paiement non confirmé."}, status=400)
    except Exception as e:
        return Response({"error": "Erreur de vérification du paiement."}, status=400)

    Paiement.objects.create(
        depannage=depannage,
        montant=montant,
        statut="payé",
        transaction=payment_intent_id  # Utiliser l'ID du PaymentIntent
    )

    depannage.status = "en_cours"
    depannage.save()

    return Response({"message": "Paiement validé, le dépanneur peut être informé."})


#>>>>>>>>>>>>>>>>>><>>>>> les deux sytem se paiment stripe et cinetpaye<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 
# Config stripe : 
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    user = request.user
    depannage_id = request.data.get('depannage_id')
    montant = request.data.get('montant')

    try:
        depannage = Depannage.objects.get(id=depannage_id, client__user=user)
    except Depannage.DoesNotExist:
        return Response({"error": "Demande introuvable."}, status=404)

    intent = stripe.PaymentIntent.create(
        amount=int(montant * 100),  # En centimes
        currency='xof',
        metadata={
            'depannage_id': depannage_id,
            'user_id': user.id
        }
    )

    return Response({
        'client_secret': intent.client_secret,
        'payment_intent_id': intent.id
    })



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initier_paiement_cinetpay(request):
    site_id = "105900028"
    apikey = "9085102026861085322d399.45634669"

    # Récupération et validation du montant
    montant = request.data.get('montant')
    try:
        montant = int(montant)
        if montant < 100:
            return Response({"error": "Montant minimum requis : 100 XOF"}, status=400)
    except:
        return Response({"error": "Montant invalide"}, status=400)

    transaction_id = str(uuid.uuid4())  # ID unique requis

    data = {
        "apikey": apikey,
        "site_id": site_id,
        "transaction_id": transaction_id,
        "amount": montant,
        "currency": "XOF",
        "description": "Paiement dépannage",
        "return_url": "https://google.com",  # ou une vraie URL
        "notify_url": "https://google.com",
        "channels": "ALL",
        "customer_name": request.user.username,
        "customer_email": "mohameddiarrasons100@gmail.com",  # Peut venir de request.user.email si tu l'as
        "customer_phone_number": "94228138",
        "customer_address": "Kati",
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post("https://api-checkout.cinetpay.com/v2/payment", json=data, headers=headers)
        if response.status_code == 200:
            res_data = response.json()
            payment_url = res_data.get("data", {}).get("payment_url")
            if not payment_url:
                return Response({"error": "Lien de paiement non reçu."}, status=400)
            return Response({"url": payment_url, "transaction_id": transaction_id})
        else:
            return Response({
                "error": "Erreur de CinetPay",
                "details": response.json()
            }, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)























@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suivi_depanneur(request, depannage_id):
    try:
        depannage = Depannage.objects.get(id=depannage_id)
        depanneur = depannage.depanneur
        return Response({
            'latitude': depanneur.latitude,
            'longitude': depanneur.longitude
        })
    except Depannage.DoesNotExist:
        return Response({"error": "Demande introuvable."}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mon_dernier_depannage(request):
    try:
        client = Client.objects.get(user=request.user)
        dernier_depannage = Depannage.objects.filter(
            client=client, status__in=['en_attente', 'en_cours']
        ).latest('id')

        return Response({
            "depannage_id": dernier_depannage.id,
            "client_latitude": dernier_depannage.client_latitude,
            "client_longitude": dernier_depannage.client_longitude,
        })
    except Depannage.DoesNotExist:
        return Response({"error": "Aucune demande en cours."}, status=404)




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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def poster_avis(request):
    user = request.user

    # 1. Récupérer le client connecté
    try:
        client = Client.objects.get(user=user)
    except Client.DoesNotExist:
        return Response({"error": "Client introuvable."}, status=404)

    # 2. Récupérer les données
    depannage_id = request.data.get('depannage_id')
    note = request.data.get('note')
    commentaire = request.data.get('commentaire', '')

    # 3. Vérification des champs requis
    if not depannage_id or not note:
        return Response({"error": "Tous les champs requis."}, status=400)

    # 4. Vérification que le dépannage appartient au client
    try:
        depannage = Depannage.objects.get(id=depannage_id, client=client)
    except Depannage.DoesNotExist:
        return Response({"error": "Dépannage introuvable."}, status=404)

    # 5. Vérifier que le dépannage est terminé
    if depannage.status != "terminé":
        return Response({"error": "Vous ne pouvez donner un avis que sur les dépannages terminés."}, status=400)

    # 6. Vérifier si un avis a déjà été donné
    if Avis.objects.filter(depannage=depannage, client=client).exists():
        return Response({"error": "Avis déjà soumis pour ce dépannage."}, status=400)

    # 7. Créer l'avis
    avis = Avis.objects.create(
        depannage=depannage,
        client=client,
        note=note,
        commentaire=commentaire
    )

    return Response(AvisSerializer(avis).data, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_avis(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return Response({"error": "Client introuvable."}, status=404)

    avis = Avis.objects.filter(client=client).order_by('-date_avis')
    serializer = AvisSerializer(avis, many=True)
    return Response(serializer.data)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def depannages_non_avis(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return Response({"error": "Client introuvable."}, status=404)

    depannages = Depannage.objects.filter(
        client=client,
        status="terminé"  # ⚠️ avec accent
    ).exclude(avis__isnull=False)

    data = []
    for d in depannages:
        data.append({
            "id": d.id,
            "type": d.type_depannage,
            "date": d.date_depannage.strftime("%Y-%m-%d %H:%M"),  # ✅ bon champ
            "prix": float(d.prix) if d.prix else 0,
            "depanneur": {
                "nom": d.depanneur.nom if d.depanneur else "Inconnu",
                "expertise": d.depanneur.expertise if d.depanneur else "N/A",
            }
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tous_les_avis(request):
    avis = Avis.objects.all().order_by('-date_avis')  # Tous les avis
    serializer = AvisSerializer(avis, many=True)
    return Response(serializer.data)
