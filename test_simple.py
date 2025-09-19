"""
Script alternativo para probar conexión MongoDB
"""
import pymongo
from urllib.parse import quote_plus

def test_simple_connection():
    try:
        # Configuración manual
        username = "efrenbohorquezv_db_user"
        password = "Central2025*"
        cluster_url = "cluster0.ljppvo.mongodb.net"
        
        # URL encode de la contraseña
        password_encoded = quote_plus(password)
        
        # Construir URI
        uri = f"mongodb+srv://{username}:{password_encoded}@{cluster_url}/?retryWrites=true&w=majority"
        
        print(f"🔗 Probando conexión con URI:")
        print(f"   {uri}")
        print("📍 Si falla, verifica la URL exacta del cluster en Atlas")
        
        # Probar conexión
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        print("✅ ¡Conexión exitosa!")
        
        # Listar bases de datos
        databases = client.list_database_names()
        print(f"📊 Bases de datos disponibles: {databases}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_simple_connection()