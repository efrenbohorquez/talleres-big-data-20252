"""
Módulo para extraer y procesar archivos ZIP
Maneja la extracción de archivos ZIP y preparación para carga a MongoDB
"""

import os
import zipfile
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime
import tempfile
import shutil

class ZipExtractor:
    """Clase para extraer y procesar archivos ZIP"""
    
    def __init__(self, extract_path: Optional[str] = None, max_file_size_mb: int = 50):
        """
        Inicializa el extractor de ZIP
        
        Args:
            extract_path (Optional[str]): Ruta donde extraer archivos
            max_file_size_mb (int): Tamaño máximo de archivo en MB
        """
        self.extract_path = extract_path or os.getenv('EXTRACT_FOLDER_PATH', './extracted_files')
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)
        
        # Crear directorio de extracción si no existe
        Path(self.extract_path).mkdir(parents=True, exist_ok=True)
    
    def validate_zip_file(self, zip_path: str) -> bool:
        """
        Valida si el archivo ZIP es válido y accesible
        
        Args:
            zip_path (str): Ruta al archivo ZIP
            
        Returns:
            bool: True si el ZIP es válido, False en caso contrario
        """
        try:
            if not os.path.exists(zip_path):
                self.logger.error(f"El archivo ZIP no existe: {zip_path}")
                return False
            
            if not zipfile.is_zipfile(zip_path):
                self.logger.error(f"El archivo no es un ZIP válido: {zip_path}")
                return False
            
            # Verificar que el ZIP no esté corrupto
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.testzip()
            
            self.logger.info(f"Archivo ZIP válido: {zip_path}")
            return True
            
        except zipfile.BadZipFile as e:
            self.logger.error(f"Archivo ZIP corrupto: {zip_path} - {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error al validar ZIP: {zip_path} - {e}")
            return False
    
    def get_zip_info(self, zip_path: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del archivo ZIP
        
        Args:
            zip_path (str): Ruta al archivo ZIP
            
        Returns:
            Optional[Dict[str, Any]]: Información del ZIP o None si falla
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                info_list = zip_ref.infolist()
                
                total_files = len([info for info in info_list if not info.is_dir()])
                total_size = sum(info.file_size for info in info_list if not info.is_dir())
                compressed_size = sum(info.compress_size for info in info_list if not info.is_dir())
                
                return {
                    "zip_path": zip_path,
                    "zip_name": os.path.basename(zip_path),
                    "zip_size_bytes": os.path.getsize(zip_path),
                    "total_files": total_files,
                    "total_uncompressed_size": total_size,
                    "total_compressed_size": compressed_size,
                    "compression_ratio": round((1 - compressed_size / total_size) * 100, 2) if total_size > 0 else 0,
                    "file_list": [info.filename for info in info_list if not info.is_dir()]
                }
                
        except Exception as e:
            self.logger.error(f"Error al obtener información del ZIP: {e}")
            return None
    
    def extract_zip(self, zip_path: str, specific_folder: Optional[str] = None) -> Optional[str]:
        """
        Extrae el archivo ZIP
        
        Args:
            zip_path (str): Ruta al archivo ZIP
            specific_folder (Optional[str]): Carpeta específica dentro del ZIP para extraer
            
        Returns:
            Optional[str]: Ruta de la carpeta extraída o None si falla
        """
        try:
            if not self.validate_zip_file(zip_path):
                return None
            
            # Crear carpeta única para esta extracción
            zip_name = Path(zip_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extract_folder = os.path.join(self.extract_path, f"{zip_name}_{timestamp}")
            
            Path(extract_folder).mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if specific_folder:
                    # Extraer solo archivos de una carpeta específica
                    members = [member for member in zip_ref.namelist() 
                             if member.startswith(specific_folder) and not member.endswith('/')]
                    zip_ref.extractall(extract_folder, members)
                else:
                    # Extraer todo el ZIP
                    zip_ref.extractall(extract_folder)
            
            self.logger.info(f"ZIP extraído exitosamente a: {extract_folder}")
            return extract_folder
            
        except Exception as e:
            self.logger.error(f"Error al extraer ZIP: {e}")
            return None
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calcula el hash SHA256 de un archivo
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            Optional[str]: Hash SHA256 o None si falla
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error al calcular hash del archivo {file_path}: {e}")
            return None
    
    def get_file_metadata(self, file_path: str, relative_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene metadatos de un archivo
        
        Args:
            file_path (str): Ruta completa al archivo
            relative_path (Optional[str]): Ruta relativa del archivo
            
        Returns:
            Optional[Dict[str, Any]]: Metadatos del archivo o None si falla
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            
            # Determinar tipo MIME
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Leer contenido si es un archivo de texto pequeño
            content = None
            if mime_type and mime_type.startswith('text/') and stat.st_size < 1024 * 1024:  # 1MB límite
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except:
                    # Si no se puede leer como texto, dejarlo como None
                    pass
            
            return {
                "file_name": os.path.basename(file_path),
                "file_path": relative_path or file_path,
                "file_size_bytes": stat.st_size,
                "file_extension": Path(file_path).suffix.lower(),
                "mime_type": mime_type,
                "file_hash": self.calculate_file_hash(file_path),
                "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "processed_date": datetime.now().isoformat(),
                "content": content,
                "is_text_file": mime_type is not None and mime_type.startswith('text/'),
                "size_mb": round(stat.st_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error al obtener metadatos del archivo {file_path}: {e}")
            return None
    
    def process_extracted_files(self, extract_folder: str) -> Generator[Dict[str, Any], None, None]:
        """
        Procesa todos los archivos extraídos y genera metadatos
        
        Args:
            extract_folder (str): Carpeta con archivos extraídos
            
        Yields:
            Dict[str, Any]: Metadatos de cada archivo procesado
        """
        try:
            for root, dirs, files in os.walk(extract_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Verificar tamaño del archivo
                    if os.path.getsize(file_path) > self.max_file_size_bytes:
                        self.logger.warning(f"Archivo demasiado grande, omitido: {file_path}")
                        continue
                    
                    # Calcular ruta relativa
                    relative_path = os.path.relpath(file_path, extract_folder)
                    
                    # Obtener metadatos
                    metadata = self.get_file_metadata(file_path, relative_path)
                    if metadata:
                        yield metadata
                    
        except Exception as e:
            self.logger.error(f"Error al procesar archivos extraídos: {e}")
    
    def cleanup_extracted_files(self, extract_folder: str) -> bool:
        """
        Limpia los archivos extraídos después del procesamiento
        
        Args:
            extract_folder (str): Carpeta a limpiar
            
        Returns:
            bool: True si se limpió exitosamente, False en caso contrario
        """
        try:
            if os.path.exists(extract_folder):
                shutil.rmtree(extract_folder)
                self.logger.info(f"Archivos extraídos limpiados: {extract_folder}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error al limpiar archivos extraídos: {e}")
            return False
    
    def process_zip_file(self, zip_path: str, cleanup: bool = True) -> Optional[Dict[str, Any]]:
        """
        Procesa completamente un archivo ZIP
        
        Args:
            zip_path (str): Ruta al archivo ZIP
            cleanup (bool): Si limpiar archivos extraídos después del procesamiento
            
        Returns:
            Optional[Dict[str, Any]]: Resultado del procesamiento o None si falla
        """
        try:
            # Obtener información del ZIP
            zip_info = self.get_zip_info(zip_path)
            if not zip_info:
                return None
            
            # Extraer archivos
            extract_folder = self.extract_zip(zip_path)
            if not extract_folder:
                return None
            
            # Procesar archivos extraídos
            processed_files = list(self.process_extracted_files(extract_folder))
            
            # Limpiar si se solicita
            if cleanup:
                self.cleanup_extracted_files(extract_folder)
            
            return {
                "zip_info": zip_info,
                "extract_folder": extract_folder if not cleanup else None,
                "processed_files": processed_files,
                "total_processed": len(processed_files),
                "processing_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error al procesar archivo ZIP: {e}")
            return None