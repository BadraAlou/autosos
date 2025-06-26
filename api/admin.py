from django.contrib import admin
from.models import *
# Register your models here.
class ClientAdmin(admin.ModelAdmin):
    list_display=['user','telephone','adresse','longitude','latitude']



class DepanneurAdmin(admin.ModelAdmin):
    list_display=['nom','tel','entreprise','expertise','disponibilite','latitude','longitude']
    

class DepanneurExterneAdmin(admin.ModelAdmin):
    list_display=['user','tel','entreprise','expertise','latitude','longitude']
    


class DepannageAdmin(admin.ModelAdmin):
    list_display=['client','depanneur','depanneur_externe','type_depannage','description','location','prix','status','date_depannage','client_longitude','client_latitude',]


class DemandeDepannageAdmin(admin.ModelAdmin):
    list_display=['depannage','depanneur_latitude','depanneur_longitude','suivi_depanneurcol','date_mise_a_jour']


class AvisAdmin(admin.ModelAdmin):
    list_display=['depannage','client','note','commentaire','date_avis']


class PaiementAdmin(admin.ModelAdmin):
    list_display=['depannage','montant','statut','transaction','date_paiement']


admin.site.register(Client,ClientAdmin)

admin.site.register(Depanneur,DepanneurAdmin)

admin.site.register(DepanneurExterne,DepanneurExterneAdmin)

admin.site.register(Depannage,DepannageAdmin)

admin.site.register(DemandeDepannage,DemandeDepannageAdmin)

admin.site.register(Avis,AvisAdmin)

admin.site.register(Paiement,PaiementAdmin)
