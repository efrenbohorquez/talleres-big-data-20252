# ZIP to MongoDB Uploader

Una aplicación Python para extraer y cargar archivos ZIP a un cluster de MongoDB de forma automática.

## 🚀 Características

- **Extracción automática**: Procesa archivos ZIP y extrae su contenido
- **Carga masiva a MongoDB**: Sube automáticamente los archivos extraídos a MongoDB
- **Metadatos completos**: Incluye información detallada de cada archivo (hash, tamaño, tipo MIME, fechas, etc.)
- **Procesamiento por lotes**: Maneja múltiples archivos ZIP en una sola ejecución
- **Logging completo**: Registra todo el proceso para debugging y auditoría
- **Interfaz colorida**: Terminal con colores para mejor experiencia de usuario
- **Validación de archivos**: Verifica la integridad de los archivos ZIP antes del procesamiento

## 📋 Requisitos

- Python 3.7 o superior
- MongoDB Atlas o cluster local de MongoDB
- Espacio en disco para extracción temporal de archivos

## 🛠 Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   git clone <repository-url>
   cd zip-mongodb-uploader
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\\Scripts\\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   
   Copia el archivo `.env.example` a `.env` y configura tus credenciales:
   ```bash
   cp .env.example .env
   ```
   
   Edita el archivo `.env` con tus datos:
   ```env
   MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
   DATABASE_NAME=zip_uploads
   COLLECTION_NAME=files
   ZIP_FOLDER_PATH=./zip_files
   EXTRACT_FOLDER_PATH=./extracted_files
   MAX_FILE_SIZE_MB=50
   LOG_LEVEL=INFO
   LOG_FILE=upload_log.txt
   ```

## 📖 Uso

### Uso básico

**Procesar un archivo ZIP específico:**
```bash
python main.py ruta/al/archivo.zip
```

**Procesar todos los ZIPs en un directorio:**
```bash
python main.py ruta/al/directorio/
```

**Búsqueda recursiva en subdirectorios:**
```bash
python main.py ruta/al/directorio/ --recursive
```

### Ejemplos de uso

```bash
# Procesar un ZIP específico
python main.py ./documentos/archivo.zip

# Procesar todos los ZIPs en la carpeta actual
python main.py .

# Buscar ZIPs recursivamente en toda la estructura
python main.py ./documentos/ -r

# Procesar con logging detallado
LOG_LEVEL=DEBUG python main.py ./archivos/
```

## 📁 Estructura del proyecto

```
proyecto/
├── src/
│   ├── mongodb_connection.py    # Módulo de conexión a MongoDB
│   └── zip_extractor.py        # Módulo de extracción de ZIP
├── main.py                     # Aplicación principal
├── requirements.txt            # Dependencias Python
├── .env.example               # Ejemplo de configuración
├── .gitignore                 # Archivos ignorados por Git
└── README.md                  # Este archivo
```

## 🔧 Configuración detallada

### Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `MONGODB_URI` | URI de conexión a MongoDB | - |
| `DATABASE_NAME` | Nombre de la base de datos | `zip_uploads` |
| `COLLECTION_NAME` | Nombre de la colección | `files` |
| `ZIP_FOLDER_PATH` | Directorio para archivos ZIP | `./zip_files` |
| `EXTRACT_FOLDER_PATH` | Directorio temporal de extracción | `./extracted_files` |
| `MAX_FILE_SIZE_MB` | Tamaño máximo por archivo (MB) | `50` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `LOG_FILE` | Archivo de log | `upload_log.txt` |

### Estructura de documentos en MongoDB

Cada archivo procesado se guarda como un documento con la siguiente estructura:

```json
{
  "_id": "ObjectId",
  "file_name": "documento.txt",
  "file_path": "carpeta/documento.txt",
  "file_size_bytes": 1024,
  "file_extension": ".txt",
  "mime_type": "text/plain",
  "file_hash": "sha256_hash",
  "created_date": "2023-10-15T10:30:00",
  "modified_date": "2023-10-15T10:30:00",
  "processed_date": "2023-10-15T12:00:00",
  "content": "contenido del archivo (si es texto)",
  "is_text_file": true,
  "size_mb": 0.001,
  "zip_name": "archivo.zip",
  "zip_path": "/ruta/completa/archivo.zip",
  "zip_size_bytes": 2048,
  "total_files": 5,
  "upload_batch_id": "batch_20231015_120000",
  "upload_date": "2023-10-15T12:00:00"
}
```

## 🔍 Características técnicas

### Procesamiento de archivos

- **Validación de ZIP**: Verifica integridad antes del procesamiento
- **Detección de tipo MIME**: Identifica automáticamente el tipo de archivo
- **Cálculo de hash**: Genera SHA256 para verificación de integridad
- **Contenido de texto**: Lee y almacena contenido de archivos de texto
- **Límite de tamaño**: Configurable para evitar archivos demasiado grandes

### Seguridad y rendimiento

- **Limpieza automática**: Elimina archivos temporales después del procesamiento
- **Logging detallado**: Registra todas las operaciones para auditoría
- **Manejo de errores**: Continúa procesando aunque algunos archivos fallen
- **Progreso visual**: Barras de progreso para operaciones largas

### Base de datos

- **Inserción por lotes**: Optimizada para grandes volúmenes de datos
- **Verificación de duplicados**: Evita subir el mismo archivo varias veces
- **Estadísticas**: Muestra información de la colección

## 🐛 Solución de problemas

### Error de conexión a MongoDB

```
Error: No se pudo conectar a MongoDB
```

**Solución**: Verifica que:
- La URI de MongoDB sea correcta
- Las credenciales estén bien configuradas
- El cluster esté activo y accesible
- Las IPs estén en la whitelist (MongoDB Atlas)

### Error al procesar ZIP

```
Archivo ZIP inválido o corrupto
```

**Solución**: Verifica que:
- El archivo sea un ZIP válido
- No esté corrupto
- Tengas permisos de lectura

### Error de espacio en disco

```
Error al extraer archivos
```

**Solución**: Verifica que:
- Haya suficiente espacio en disco
- Tengas permisos de escritura en el directorio de extracción

## 📊 Logs y monitoreo

Los logs se guardan en el archivo especificado en `LOG_FILE` (por defecto `upload_log.txt`) e incluyen:

- Intentos de conexión a MongoDB
- Procesamiento de cada archivo ZIP
- Errores y advertencias
- Estadísticas de carga
- Tiempo de procesamiento

### Ejemplo de log

```
2023-10-15 12:00:00,000 - __main__ - INFO - Conectando a MongoDB...
2023-10-15 12:00:01,000 - src.mongodb_connection - INFO - Conexión exitosa a MongoDB
2023-10-15 12:00:02,000 - src.zip_extractor - INFO - Archivo ZIP válido: archivo.zip
2023-10-15 12:00:03,000 - src.zip_extractor - INFO - ZIP extraído exitosamente
2023-10-15 12:00:04,000 - src.mongodb_connection - INFO - Se insertaron 5 documentos
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Si encuentras algún problema o tienes preguntas:

1. Revisa la sección de solución de problemas
2. Consulta los logs para más detalles
3. Abre un issue en el repositorio

---

**¡Disfruta procesando tus archivos ZIP con MongoDB! 🎉**