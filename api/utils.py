import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance entre deux points GPS (en km) en utilisant la formule de Haversine.
    """
    R = 6371  # Rayon de la terre en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c  # en kilomètres
    return round(distance, 2)


def calculer_prix_par_distance(lat1, lon1, lat2, lon2):
    """
    Retourne un prix en fonction de la distance (en km).
    Par exemple : 1000 FCFA par km avec un minimum de 2000 FCFA
    
    """
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    prix_par_km = 1000  # FCFA par km
    prix_minimum = 1000  # Prix minimum 
    prix = max(distance * prix_par_km, prix_minimum)
    return round(prix), distance


from math import radians, sin, cos, sqrt, atan2

def calcul_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Rayon de la Terre en km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return round(distance, 2)
