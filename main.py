"""
Módulo principal para procesamiento y carga de archivos ZIP a MongoDB
Orquesta todo el proceso desde la extracción hasta la carga en la base de datos
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse
from tqdm import tqdm
import colorama
from colorama import Fore, Style

# Agregar el directorio src al path para importar módulos locales
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.mongodb_connection import mongo_connection
from src.zip_extractor import ZipExtractor

# Inicializar colorama para colores en terminal
colorama.init(autoreset=True)

class ZipToMongoProcessor:
    """Clase principal para procesar archivos ZIP y cargarlos a MongoDB"""
    
    def __init__(self):
        """Inicializa el procesador"""
        self.setup_logging()
        self.zip_extractor = ZipExtractor()
        self.logger = logging.getLogger(__name__)
        
        # Estadísticas del procesamiento
        self.stats = {
            "total_zips_processed": 0,
            "total_files_uploaded": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None,
            "failed_zips": [],
            "uploaded_files": []
        }
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', 'upload_log.txt')
        
        # Configurar formato de logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Logger para archivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        
        # Logger para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        
        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def print_banner(self):
        """Imprime banner de la aplicación"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    ZIP TO MONGODB UPLOADER                   ║
║                                                              ║
║           Procesador de archivos ZIP para MongoDB           ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
    
    def validate_zip_files(self, zip_paths: List[str]) -> List[str]:
        """
        Valida una lista de archivos ZIP
        
        Args:
            zip_paths (List[str]): Lista de rutas a archivos ZIP
            
        Returns:
            List[str]: Lista de archivos ZIP válidos
        """
        valid_zips = []
        
        print(f"{Fore.YELLOW}Validando archivos ZIP...{Style.RESET_ALL}")
        
        for zip_path in tqdm(zip_paths, desc="Validando ZIPs"):
            if self.zip_extractor.validate_zip_file(zip_path):
                valid_zips.append(zip_path)
                print(f"{Fore.GREEN}✓ Válido: {os.path.basename(zip_path)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Inválido: {os.path.basename(zip_path)}{Style.RESET_ALL}")
                self.stats["failed_zips"].append({
                    "zip_path": zip_path,
                    "error": "Archivo ZIP inválido o corrupto"
                })
        
        return valid_zips
    
    def process_single_zip(self, zip_path: str) -> Optional[Dict[str, Any]]:
        """
        Procesa un archivo ZIP individual
        
        Args:
            zip_path (str): Ruta al archivo ZIP
            
        Returns:
            Optional[Dict[str, Any]]: Resultado del procesamiento
        """
        try:
            print(f"{Fore.CYAN}Procesando: {os.path.basename(zip_path)}{Style.RESET_ALL}")
            
            # Procesar el archivo ZIP
            result = self.zip_extractor.process_zip_file(zip_path, cleanup=True)
            
            if not result:
                self.logger.error(f"Error al procesar ZIP: {zip_path}")
                return None
            
            # Preparar documentos para MongoDB
            documents = []
            zip_metadata = {
                "zip_name": result["zip_info"]["zip_name"],
                "zip_path": zip_path,
                "zip_size_bytes": result["zip_info"]["zip_size_bytes"],
                "total_files": result["zip_info"]["total_files"],
                "upload_batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "upload_date": datetime.now().isoformat()
            }
            
            for file_data in result["processed_files"]:
                # Agregar metadatos del ZIP a cada archivo
                file_data.update(zip_metadata)
                documents.append(file_data)
            
            # Insertar en MongoDB
            if documents:
                inserted_ids = mongo_connection.insert_multiple_files(documents)
                if inserted_ids:
                    self.stats["total_files_uploaded"] += len(inserted_ids)
                    self.stats["uploaded_files"].extend(inserted_ids)
                    print(f"{Fore.GREEN}✓ Cargados {len(inserted_ids)} archivos de {os.path.basename(zip_path)}{Style.RESET_ALL}")
                    return {
                        "zip_path": zip_path,
                        "files_uploaded": len(inserted_ids),
                        "inserted_ids": inserted_ids
                    }
                else:
                    self.logger.error(f"Error al insertar archivos de {zip_path} en MongoDB")
                    return None
            else:
                self.logger.warning(f"No se encontraron archivos válidos en {zip_path}")
                return {"zip_path": zip_path, "files_uploaded": 0, "inserted_ids": []}
            
        except Exception as e:
            self.logger.error(f"Error procesando {zip_path}: {e}")
            self.stats["failed_zips"].append({
                "zip_path": zip_path,
                "error": str(e)
            })
            return None
    
    def process_zip_files(self, zip_paths: List[str]) -> Dict[str, Any]:
        """
        Procesa múltiples archivos ZIP
        
        Args:
            zip_paths (List[str]): Lista de rutas a archivos ZIP
            
        Returns:
            Dict[str, Any]: Resumen del procesamiento
        """
        self.stats["start_time"] = datetime.now()
        
        # Validar archivos ZIP
        valid_zips = self.validate_zip_files(zip_paths)
        
        if not valid_zips:
            print(f"{Fore.RED}No se encontraron archivos ZIP válidos para procesar{Style.RESET_ALL}")
            return self.get_processing_summary()
        
        print(f"{Fore.CYAN}Procesando {len(valid_zips)} archivos ZIP...{Style.RESET_ALL}")
        
        # Procesar cada ZIP
        successful_uploads = []
        for zip_path in tqdm(valid_zips, desc="Procesando ZIPs"):
            result = self.process_single_zip(zip_path)
            if result:
                successful_uploads.append(result)
                self.stats["total_zips_processed"] += 1
            else:
                self.stats["total_errors"] += 1
        
        self.stats["end_time"] = datetime.now()
        
        return self.get_processing_summary()
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Genera resumen del procesamiento
        
        Returns:
            Dict[str, Any]: Resumen detallado
        """
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        return {
            "processing_summary": {
                "total_zips_processed": self.stats["total_zips_processed"],
                "total_files_uploaded": self.stats["total_files_uploaded"],
                "total_errors": self.stats["total_errors"],
                "failed_zips": self.stats["failed_zips"],
                "duration_seconds": duration,
                "start_time": self.stats["start_time"].isoformat() if self.stats["start_time"] else None,
                "end_time": self.stats["end_time"].isoformat() if self.stats["end_time"] else None
            }
        }
    
    def print_summary(self, summary: Dict[str, Any]):
        """
        Imprime resumen del procesamiento
        
        Args:
            summary (Dict[str, Any]): Resumen del procesamiento
        """
        data = summary["processing_summary"]
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"                    RESUMEN DEL PROCESAMIENTO")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}✓ ZIPs procesados exitosamente: {data['total_zips_processed']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Archivos cargados a MongoDB: {data['total_files_uploaded']}{Style.RESET_ALL}")
        
        if data['total_errors'] > 0:
            print(f"{Fore.RED}✗ Errores encontrados: {data['total_errors']}{Style.RESET_ALL}")
            
            if data['failed_zips']:
                print(f"\n{Fore.YELLOW}Archivos con errores:{Style.RESET_ALL}")
                for failed in data['failed_zips']:
                    print(f"  • {os.path.basename(failed['zip_path'])}: {failed['error']}")
        
        if data['duration_seconds']:
            print(f"\n{Fore.BLUE}⏱  Tiempo total: {data['duration_seconds']:.2f} segundos{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    def run(self, zip_paths: List[str]) -> bool:
        """
        Ejecuta el procesamiento completo
        
        Args:
            zip_paths (List[str]): Lista de rutas a archivos ZIP
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            self.print_banner()
            
            # Conectar a MongoDB
            print(f"{Fore.YELLOW}Conectando a MongoDB...{Style.RESET_ALL}")
            if not mongo_connection.connect():
                print(f"{Fore.RED}Error: No se pudo conectar a MongoDB{Style.RESET_ALL}")
                return False
            
            print(f"{Fore.GREEN}✓ Conectado a MongoDB exitosamente{Style.RESET_ALL}")
            
            # Mostrar estadísticas de la base de datos
            stats = mongo_connection.get_collection_stats()
            if stats:
                print(f"{Fore.BLUE}📊 Documentos en la colección: {stats['document_count']}{Style.RESET_ALL}")
            
            # Procesar archivos ZIP
            summary = self.process_zip_files(zip_paths)
            
            # Mostrar resumen
            self.print_summary(summary)
            
            return self.stats["total_zips_processed"] > 0
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Procesamiento interrumpido por el usuario{Style.RESET_ALL}")
            return False
        except Exception as e:
            self.logger.error(f"Error general en el procesamiento: {e}")
            print(f"{Fore.RED}Error general: {e}{Style.RESET_ALL}")
            return False
        finally:
            # Cerrar conexión a MongoDB
            mongo_connection.disconnect()

def find_zip_files(directory: str) -> List[str]:
    """
    Busca archivos ZIP en un directorio
    
    Args:
        directory (str): Directorio donde buscar
        
    Returns:
        List[str]: Lista de rutas a archivos ZIP
    """
    zip_files = []
    directory_path = Path(directory)
    
    if directory_path.is_file() and directory_path.suffix.lower() == '.zip':
        return [str(directory_path)]
    
    if directory_path.is_dir():
        zip_files = list(directory_path.glob('**/*.zip'))
        return [str(f) for f in zip_files]
    
    return zip_files

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Procesa archivos ZIP y carga su contenido a MongoDB'
    )
    parser.add_argument(
        'path',
        help='Ruta al archivo ZIP o directorio con archivos ZIP'
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Buscar archivos ZIP recursivamente en subdirectorios'
    )
    
    args = parser.parse_args()
    
    # Buscar archivos ZIP
    if os.path.isfile(args.path):
        zip_files = [args.path] if args.path.endswith('.zip') else []
    else:
        pattern = '**/*.zip' if args.recursive else '*.zip'
        zip_files = [str(f) for f in Path(args.path).glob(pattern)]
    
    if not zip_files:
        print(f"{Fore.RED}No se encontraron archivos ZIP en: {args.path}{Style.RESET_ALL}")
        return 1
    
    print(f"{Fore.BLUE}Encontrados {len(zip_files)} archivo(s) ZIP{Style.RESET_ALL}")
    
    # Ejecutar procesamiento
    processor = ZipToMongoProcessor()
    success = processor.run(zip_files)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())