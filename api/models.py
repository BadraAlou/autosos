from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.db import models

# Client
class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=255)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.user.username

# Depanneur
class Depanneur(models.Model):
    nom=models.CharField(max_length=100)
    tel=models.CharField(max_length=20)
    entreprise = models.CharField(max_length=100)
    expertise = models.CharField(max_length=100)  # Exemple: mécanique, batterie, pneu, etc.
    disponibilite = models.BooleanField(default=True)   # Zone d'intervention
    latitude = models.FloatField(null=True, blank=True)  # Position actuelle
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nom} - {self.expertise}"
    



class DepanneurExterne(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    entreprise = models.CharField(max_length=100)
    expertise = models.CharField(max_length=100)
    tel = models.CharField(max_length=20)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.entreprise}"



# Depannage
class Depannage(models.Model):
    TYPE_DEPANNAGE_CHOICES = [
        ('batterie', 'Batterie'),
        ('pneu', 'Pneu'),
        ('moteur', 'Moteur'),
        ('remorquage', 'Remorquage'),
        ('simple', 'Simple'),
        ('avec_reparation', 'Avec réparation'),
        ('autre', 'Autre'),
    
    ]

    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminé', 'Terminé'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    depanneur = models.ForeignKey(Depanneur, on_delete=models.SET_NULL, null=True, blank=True)
    depanneur_externe = models.ForeignKey('DepanneurExterne', on_delete=models.SET_NULL, null=True, blank=True)
    type_depannage = models.CharField(max_length=50, choices=TYPE_DEPANNAGE_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=255,null=True,blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_cours')
    date_depannage = models.DateTimeField(auto_now_add=True)
    client_longitude = models.FloatField(null=True, blank=True)
    client_latitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.client.user.username} - {self.type_depannage}"





class Message(models.Model):
    demande = models.ForeignKey('Depannage', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_envoyes")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_recus")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']


# Suivi / DemandeDepannage
class DemandeDepannage(models.Model):
    depannage = models.OneToOneField(Depannage, on_delete=models.CASCADE)
    depanneur_latitude = models.FloatField(null=True, blank=True)
    depanneur_longitude = models.FloatField(null=True, blank=True)
    suivi_depanneurcol = models.CharField(max_length=100)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Suivi du {self.depannage}"





# Avis
class Avis(models.Model):
    depannage = models.ForeignKey(Depannage, on_delete=models.CASCADE,related_name="avis")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    note = models.IntegerField()
    commentaire = models.TextField(blank=True)
    date_avis = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avis de {self.client.user.username} pour {self.depannage}"

# Paiement
class Paiement(models.Model):
    depannage = models.ForeignKey(Depannage, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=50)  # payé, en attente
    transaction = models.CharField(max_length=100)
    date_paiement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement de {self.depannage.client.user.username} - {self.montant} FCFA"
