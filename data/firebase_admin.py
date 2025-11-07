import firebase_admin
from firebase_admin import credentials, auth
import os

# --- Configuración ---

# 1. Esta es la URL de tu base de datos (de tu archivo firebase_config.py)
DATABASE_URL = 'https://greenway-450aa-default-rtdb.firebaseio.com'

# 2. Construye la ruta al archivo de clave que debe estar en esta misma carpeta ('data/')
#    os.path.abspath(__file__) -> Obtiene la ruta de este archivo (firebase_admin.py)
#    os.path.dirname(...)       -> Obtiene la carpeta que lo contiene ('data/')
#    os.path.join(...)          -> Une 'data/' + 'serviceAccountKey.json'
CRED_PATH = 'data/serviceAccountKey.json'

# --- Fin Configuración ---

try:
    # Intenta cargar la "llave maestra" desde la ruta
    cred = credentials.Certificate(CRED_PATH)
    
    # Inicializa la aplicación de Admin
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })
    
    # Exportamos solo el módulo 'auth' del SDK de Admin
    # Lo llamamos 'admin_auth' para no confundirlo con el 'auth' de pyrebase
    admin_auth = auth
    print("SDK de Admin de Firebase inicializado con éxito.")
    
except FileNotFoundError:
    print("="*50)
    print(f"ERROR: No se encontró el archivo '{CRED_PATH}'.")
    print("Por favor, descarga tu 'serviceAccountKey.json' desde la Consola de Firebase")
    print("y colócalo en tu carpeta 'data/'.")
    print("="*50)
    admin_auth = None # Asigna None para que la app falle y sepas qué pasó
    
except Exception as e:
    print(f"Error inicializando el SDK de Admin: {e}")
    admin_auth = None