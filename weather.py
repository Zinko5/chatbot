import requests
import unicodedata

# Coordenadas de las capitales de departamento de Bolivia
# Claves normalizadas: MAYÚSCULAS y SIN ACENTOS
DEPARTAMENTOS = {
    "SANTA CRUZ": {"lat": -17.7863, "lon": -63.1812, "name": "Santa Cruz"},
    "LA PAZ": {"lat": -16.5000, "lon": -68.1500, "name": "La Paz"},
    "COCHABAMBA": {"lat": -17.3895, "lon": -66.1568, "name": "Cochabamba"},
    "SUCRE": {"lat": -19.0333, "lon": -65.2627, "name": "Sucre"},
    "TARIJA": {"lat": -21.5355, "lon": -64.7296, "name": "Tarija"},
    "ORURO": {"lat": -17.9833, "lon": -67.1500, "name": "Oruro"},
    "POTOSI": {"lat": -19.5836, "lon": -65.7531, "name": "Potosí"},
    "TRINIDAD": {"lat": -14.8333, "lon": -64.9000, "name": "Trinidad"},
    "COBIJA": {"lat": -11.0267, "lon": -68.7692, "name": "Cobija"},
    # Alias
    "BENI": {"lat": -14.8333, "lon": -64.9000, "name": "Trinidad"},
    "PANDO": {"lat": -11.0267, "lon": -68.7692, "name": "Cobija"},
    "CHUQUISACA": {"lat": -19.0333, "lon": -65.2627, "name": "Sucre"}
}

def normalize_name(text):
    """Elimina acentos y convierte a mayúsculas"""
    if not text: return ""
    # Normalizar unicode (NFD separa caracteres de sus acentos)
    text = unicodedata.normalize('NFD', text)
    # Filtrar caracteres no-ASCII (acentos)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    return text.upper().strip()

def get_bolivia_weather(city_name="Santa Cruz"):
    """
    Obtiene el clima actual de una ciudad de Bolivia.
    """
    try:
        # Normalizar entrada
        city_key = normalize_name(city_name)
        if not city_key: city_key = "SANTA CRUZ"
        
        print(f"🌦️ Consultando clima para: '{city_name}' -> Key: '{city_key}'")
        
        coords = DEPARTAMENTOS.get(city_key)
        if not coords:
            print(f"⚠️ Ciudad '{city_key}' no encontrada. Usando Santa Cruz.")
            coords = DEPARTAMENTOS["SANTA CRUZ"]
        
        real_name = coords["name"]

        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true&timezone=America%2FLa_Paz"
        
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'current_weather' in data:
            cw = data['current_weather']
            temp = cw['temperature']
            code = cw['weathercode']
            
            # Mapeo de códigos WMO
            condition = "Desconocido"
            emoji = "❓"
            
            if code == 0:
                condition = "Cielo despejado"
                emoji = "☀️"
            elif code in [1, 2, 3]:
                condition = "Parcialmente nublado"
                emoji = "⛅"
            elif code in [45, 48]:
                condition = "Niebla"
                emoji = "🌫️"
            elif code in [51, 53, 55]:
                condition = "Llovizna"
                emoji = "🌦️"
            elif code in [61, 63, 65]:
                condition = "Lluvia"
                emoji = "🌧️"
            elif code in [80, 81, 82]:
                condition = "Lluvia fuerte"
                emoji = "⛈️"
            elif code in [95, 96, 99]:
                condition = "Tormenta eléctrica"
                emoji = "⚡"
                
            return {
                'temp': temp,
                'condition': condition,
                'emoji': emoji,
                'city': real_name
            }
            
    except Exception as e:
        print(f"❌ Error obteniendo clima: {e}")
        
    return None
