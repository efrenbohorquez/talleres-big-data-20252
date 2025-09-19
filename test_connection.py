"""
Script de prueba para validar la conexión a MongoDB
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.mongodb_connection import mongo_connection
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_connection():
    print("🔗 Probando conexión a MongoDB Atlas...")
    
    if mongo_connection.connect():
        print("✅ ¡Conexión exitosa!")
        
        # Mostrar estadísticas
        stats = mongo_connection.get_collection_stats()
        if stats:
            print(f"📊 Documentos en la colección: {stats['document_count']}")
            print(f"📏 Tamaño de la colección: {stats['size_bytes']} bytes")
        
        # Cerrar conexión
        mongo_connection.disconnect()
        return True
    else:
        print("❌ Error de conexión. Verifica:")
        print("   - URI de MongoDB en .env")
        print("   - Credenciales de usuario")
        print("   - Configuración de red en Atlas")
        return False

if __name__ == "__main__":
    test_connection()