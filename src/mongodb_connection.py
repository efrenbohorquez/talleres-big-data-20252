"""
Módulo de conexión a MongoDB
Maneja la conexión al cluster y operaciones básicas de la base de datos
"""

import os
import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class MongoDBConnection:
    """Clase para manejar la conexión a MongoDB"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.database_name = os.getenv('DATABASE_NAME', 'zip_uploads')
        self.collection_name = os.getenv('COLLECTION_NAME', 'files')
        
        # Configurar logging
        logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """
        Establece conexión con MongoDB
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            if not self.mongodb_uri:
                self.logger.error("MONGODB_URI no está configurada en las variables de entorno")
                return False
            
            self.logger.info("Conectando a MongoDB...")
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 segundos timeout
                connectTimeoutMS=10000,         # 10 segundos timeout de conexión
                socketTimeoutMS=20000           # 20 segundos timeout de socket
            )
            
            # Verificar la conexión
            self.client.admin.command('ping')
            
            # Obtener la base de datos y colección
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            self.logger.info(f"Conexión exitosa a MongoDB - DB: {self.database_name}, Collection: {self.collection_name}")
            return True
            
        except ConnectionFailure as e:
            self.logger.error(f"Error de conexión a MongoDB: {e}")
            return False
        except ServerSelectionTimeoutError as e:
            self.logger.error(f"Timeout al conectar a MongoDB: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error inesperado al conectar a MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión a MongoDB"""
        if self.client:
            self.client.close()
            self.logger.info("Conexión a MongoDB cerrada")
    
    def insert_file_document(self, file_data: Dict[str, Any]) -> Optional[str]:
        """
        Inserta un documento de archivo en la colección
        
        Args:
            file_data (Dict[str, Any]): Datos del archivo a insertar
            
        Returns:
            Optional[str]: ID del documento insertado o None si falla
        """
        try:
            if self.collection is None:
                self.logger.error("No hay conexión establecida con la colección")
                return None
            
            result = self.collection.insert_one(file_data)
            self.logger.info(f"Documento insertado con ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Error al insertar documento: {e}")
            return None
    
    def insert_multiple_files(self, files_data: list) -> Optional[list]:
        """
        Inserta múltiples documentos de archivos en la colección
        
        Args:
            files_data (list): Lista de documentos a insertar
            
        Returns:
            Optional[list]: Lista de IDs insertados o None si falla
        """
        try:
            if self.collection is None:
                self.logger.error("No hay conexión establecida con la colección")
                return None
            
            if not files_data:
                self.logger.warning("No hay archivos para insertar")
                return []
            
            result = self.collection.insert_many(files_data)
            inserted_ids = [str(id) for id in result.inserted_ids]
            self.logger.info(f"Se insertaron {len(inserted_ids)} documentos")
            return inserted_ids
            
        except Exception as e:
            self.logger.error(f"Error al insertar múltiples documentos: {e}")
            return None
    
    def check_file_exists(self, file_path: str, file_hash: str = None) -> bool:
        """
        Verifica si un archivo ya existe en la base de datos
        
        Args:
            file_path (str): Ruta del archivo
            file_hash (str, optional): Hash del archivo para verificación
            
        Returns:
            bool: True si el archivo existe, False en caso contrario
        """
        try:
            if self.collection is None:
                return False
            
            query = {"file_path": file_path}
            if file_hash:
                query["file_hash"] = file_hash
            
            return self.collection.find_one(query) is not None
            
        except Exception as e:
            self.logger.error(f"Error al verificar existencia del archivo: {e}")
            return False
    
    def get_collection_stats(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas de la colección
        
        Returns:
            Optional[Dict[str, Any]]: Estadísticas de la colección o None si falla
        """
        try:
            if self.collection is None:
                return None
            
            stats = self.database.command("collStats", self.collection_name)
            return {
                "document_count": stats.get("count", 0),
                "size_bytes": stats.get("size", 0),
                "average_size": stats.get("avgObjSize", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas: {e}")
            return None

# Instancia global para reutilizar la conexión
mongo_connection = MongoDBConnection()