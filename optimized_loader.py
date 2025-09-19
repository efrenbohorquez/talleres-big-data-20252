"""
Módulo optimizado para cargas masivas de JSON a MongoDB
Implementa mejores prácticas para grandes volúmenes de datos
"""

import os
import sys
import logging
from typing import List, Dict, Any, Generator
from datetime import datetime
import json
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from tqdm import tqdm
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from src.mongodb_connection import mongo_connection

class OptimizedBulkLoader:
    """Cargador optimizado para grandes volúmenes de datos JSON"""
    
    def __init__(self, batch_size: int = 1000):
        """
        Inicializa el cargador optimizado
        
        Args:
            batch_size (int): Tamaño de lote para inserción bulk (default: 1000)
        """
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
        self.stats = {
            "total_processed": 0,
            "total_inserted": 0,
            "total_errors": 0,
            "batches_processed": 0,
            "start_time": None,
            "end_time": None
        }
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Divide una lista de documentos en lotes
        
        Args:
            documents: Lista de documentos a dividir
            
        Yields:
            Lotes de documentos del tamaño especificado
        """
        for i in range(0, len(documents), self.batch_size):
            yield documents[i:i + self.batch_size]
    
    def bulk_insert_optimized(self, documents: List[Dict[str, Any]], 
                            ordered: bool = False, 
                            bypass_validation: bool = True) -> Dict[str, Any]:
        """
        Inserta documentos en lotes optimizados
        
        Args:
            documents: Lista de documentos a insertar
            ordered: Si mantener el orden (False = más rápido)
            bypass_validation: Saltar validación de esquema (más rápido)
            
        Returns:
            Resultado de la operación bulk
        """
        if not documents:
            return {"inserted_count": 0, "errors": []}
        
        self.stats["start_time"] = datetime.now()
        
        try:
            if mongo_connection.collection is None:
                raise Exception("No hay conexión a MongoDB")
            
            total_inserted = 0
            errors = []
            
            # Procesar en lotes
            for batch in tqdm(self.chunk_documents(documents), 
                            desc="Insertando lotes", 
                            total=(len(documents) + self.batch_size - 1) // self.batch_size):
                
                try:
                    # Configurar opciones de inserción optimizada
                    options = {
                        "ordered": ordered,
                        "bypass_document_validation": bypass_validation
                    }
                    
                    result = mongo_connection.collection.insert_many(batch, **options)
                    total_inserted += len(result.inserted_ids)
                    self.stats["batches_processed"] += 1
                    
                    self.logger.info(f"Lote insertado: {len(result.inserted_ids)} documentos")
                    
                except BulkWriteError as bwe:
                    # Manejar errores parciales
                    total_inserted += bwe.details.get('nInserted', 0)
                    errors.extend(bwe.details.get('writeErrors', []))
                    self.logger.warning(f"Errores en lote: {len(bwe.details.get('writeErrors', []))}")
                
                except Exception as e:
                    errors.append({"error": str(e), "batch_size": len(batch)})
                    self.logger.error(f"Error en lote: {e}")
            
            self.stats["total_inserted"] = total_inserted
            self.stats["total_errors"] = len(errors)
            self.stats["end_time"] = datetime.now()
            
            return {
                "inserted_count": total_inserted,
                "errors": errors,
                "batches_processed": self.stats["batches_processed"]
            }
            
        except Exception as e:
            self.logger.error(f"Error en bulk insert: {e}")
            return {"inserted_count": 0, "errors": [str(e)]}
    
    def load_json_files_optimized(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Carga múltiples archivos JSON de forma optimizada
        
        Args:
            file_paths: Lista de rutas a archivos JSON
            
        Returns:
            Resultado de la carga
        """
        documents = []
        
        print(f"🔄 Cargando {len(file_paths)} archivos JSON...")
        
        for file_path in tqdm(file_paths, desc="Leyendo archivos"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Intentar cargar como JSON
                    try:
                        data = json.load(f)
                        
                        # Si es una lista de objetos JSON
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    item.update({
                                        "source_file": os.path.basename(file_path),
                                        "loaded_at": datetime.now().isoformat(),
                                        "file_size_bytes": os.path.getsize(file_path)
                                    })
                                    documents.append(item)
                        
                        # Si es un objeto JSON único
                        elif isinstance(data, dict):
                            data.update({
                                "source_file": os.path.basename(file_path),
                                "loaded_at": datetime.now().isoformat(),
                                "file_size_bytes": os.path.getsize(file_path)
                            })
                            documents.append(data)
                    
                    except json.JSONDecodeError:
                        # Si no es JSON válido, cargar como texto
                        f.seek(0)
                        content = f.read()
                        documents.append({
                            "raw_content": content,
                            "source_file": os.path.basename(file_path),
                            "loaded_at": datetime.now().isoformat(),
                            "file_size_bytes": os.path.getsize(file_path),
                            "content_type": "raw_text"
                        })
                        
            except Exception as e:
                self.logger.error(f"Error leyendo archivo {file_path}: {e}")
        
        print(f"✅ Cargados {len(documents)} documentos desde {len(file_paths)} archivos")
        
        # Insertar en MongoDB
        if documents:
            return self.bulk_insert_optimized(documents)
        else:
            return {"inserted_count": 0, "errors": ["No se encontraron documentos válidos"]}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de rendimiento
        
        Returns:
            Estadísticas detalladas
        """
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            docs_per_second = self.stats["total_inserted"] / duration if duration > 0 else 0
            
            return {
                "total_inserted": self.stats["total_inserted"],
                "total_errors": self.stats["total_errors"],
                "batches_processed": self.stats["batches_processed"],
                "duration_seconds": duration,
                "documents_per_second": round(docs_per_second, 2),
                "batch_size_used": self.batch_size,
                "average_batch_time": round(duration / self.stats["batches_processed"], 3) if self.stats["batches_processed"] > 0 else 0
            }
        
        return self.stats

def benchmark_different_strategies():
    """Función para comparar diferentes estrategias de carga"""
    
    strategies = [
        {"name": "Lotes pequeños", "batch_size": 100},
        {"name": "Lotes medianos", "batch_size": 1000},
        {"name": "Lotes grandes", "batch_size": 5000},
        {"name": "Lotes muy grandes", "batch_size": 10000}
    ]
    
    print("🧪 BENCHMARK DE ESTRATEGIAS DE CARGA")
    print("=" * 50)
    
    for strategy in strategies:
        print(f"\n🔄 Probando: {strategy['name']} (batch_size: {strategy['batch_size']})")
        
        loader = OptimizedBulkLoader(batch_size=strategy['batch_size'])
        
        # Simular documentos para prueba
        test_documents = [
            {"test_id": i, "data": f"documento_{i}", "timestamp": datetime.now().isoformat()}
            for i in range(1000)  # 1000 documentos de prueba
        ]
        
        start_time = time.time()
        result = loader.bulk_insert_optimized(test_documents)
        end_time = time.time()
        
        print(f"   ✅ Insertados: {result['inserted_count']} documentos")
        print(f"   ⏱  Tiempo: {end_time - start_time:.3f} segundos")
        print(f"   🚀 Velocidad: {result['inserted_count'] / (end_time - start_time):.2f} docs/seg")

if __name__ == "__main__":
    # Conectar a MongoDB
    if mongo_connection.connect():
        print("✅ Conectado a MongoDB")
        
        # Ejecutar benchmark
        benchmark_different_strategies()
        
        mongo_connection.disconnect()
    else:
        print("❌ Error conectando a MongoDB")