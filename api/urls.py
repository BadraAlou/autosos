from django.urls import path
from api import views
from rest_framework.authtoken.views import obtain_auth_token

from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns=[
    path('client/',views.ClientList.as_view()),
    path('register/', register_user, name='register'),
    path('client_presence/', client_presence),



    path('depanneur/update_position/', update_position_depanneur),
    path('depanneur/',views.DepanneurList.as_view(),),
    path('depanneur_list/',views.Depanneur_List.as_view(),),#en objet
    path('depanneurs/', DepanneurList.as_view(), name='liste_depanneurs'),#sous forme de lsite 
    path('depannage/<int:depannage_id>/suivi/', views.suivi_depanneur),
    path('inscription_depanneur_externe/', DepanneurExterneInscriptionView.as_view(), name='inscription_depanneur_externe'),
    path('update_position_depanneur/', UpdateDepanneurPositionView.as_view()),
    path('messages/', MessageListCreateAPIView.as_view(), name='message-list-create'),

    




    path('depannage/',views.DepannageList.as_view(),),
    path('depannage/', views.DepannageList.as_view(), name='depannage-list'),
    path('demandeDepannge/',views.DepannageList.as_view(),),
    
    path('creer_demande_depannage/', creer_demande_remorquage),

    path('paliers_remorquage/', views.paliers_remorquage),

    
    path('remorquage/', creer_demande_remorquage, name='creer_demande_remorquage'),

    path('demandes_depannage/', DemandeDepannageList.as_view(), name='demande_depannage_list'),
    path('mes_demandes/', views.mes_demandesView.as_view()),    

    
    
    
    path('Avis/',views.AvisList.as_view(),),
    path('Paiyement/',views.PaiementList.as_view(),),
    path('estimer_prix_depannage/', estimer_prix_depannage),
    path('enregistrer_paiement/', enregistrer_paiement),


    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('client/me/', get_my_client_info),
    path('login/',CustomLoginView.as_view(),name='login' ),
    path('client/update_position/', update_position),       
]