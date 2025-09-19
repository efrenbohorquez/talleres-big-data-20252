# 🍃 Taller MongoDB - Universidad Central

## 📋 Descripción
Taller básico sobre MongoDB optimizado para VS Code y Windows. Este notebook enseña las operaciones fundamentales de MongoDB usando Python y PyMongo.

## 🎯 Objetivos de Aprendizaje
- Instalar y configurar MongoDB en Windows
- Conectar Python con MongoDB usando PyMongo
- Realizar operaciones CRUD (Create, Read, Update, Delete)
- Procesar y cargar datos externos en MongoDB
- Gestionar bases de datos y colecciones

## 🛠️ Prerrequisitos

### Software Necesario
- **Python 3.8+** con Jupyter/VS Code
- **MongoDB** (una de estas opciones):
  - MongoDB Community Server (local)
  - MongoDB Atlas (gratuito en la nube)
  - Docker con imagen de MongoDB

### Librerías Python
```bash
pip install pymongo
pip install requests
```

## 🚀 Instrucciones de Uso

### 1. Configurar MongoDB

**Opción A: MongoDB Local**
1. Descargar MongoDB Community desde: https://www.mongodb.com/try/download/community
2. Instalar con configuración por defecto
3. El servicio se ejecuta automáticamente en puerto 27017

**Opción B: MongoDB Atlas (Recomendado)**
1. Crear cuenta gratuita en: https://www.mongodb.com/cloud/atlas
2. Crear cluster gratuito (512MB)
3. Obtener string de conexión
4. Modificar la línea de conexión en el notebook

**Opción C: Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 2. Ejecutar el Notebook
1. Abrir `4_Ucentral_2025_s2_MONGOdb_taller1.ipynb` en VS Code
2. Ejecutar las celdas secuencialmente
3. El notebook detectará automáticamente MongoDB disponible

## 📁 Estructura del Proyecto

Al ejecutar el notebook se creará automáticamente:
```
C:\Users\[usuario]\MongoDB_Taller\
├── data/           # Datos del proyecto
└── downloads/      # Archivos descargados
    └── student.txt # Dataset procesado
```

## 🗄️ Base de Datos Creada

**Base de datos:** `estudiantes_Ucentral`

**Colecciones:**
- `profesores` - Información de profesores
- `estudiantes` - Metadatos del dataset UCI
- `cursos` - Lista para uso futuro

## 📊 Operaciones Implementadas

### Funciones CRUD Disponibles
- `insertar_documento()` - Insertar documentos
- `buscar_documentos()` - Buscar con filtros
- `actualizar_un_documento()` - Actualizar documento único
- `actualizar_varios_documentos()` - Actualizar múltiples
- `eliminar_varios_documentos()` - Eliminar por criterio

### Ejemplos de Uso
```python
# Insertar
insertar_documento(db, 'profesores', {"nombre": "Juan", "apellido": "Pérez"})

# Buscar
buscar_documentos(db, 'profesores', {"nombre": "Juan"})

# Actualizar
actualizar_un_documento(db, 'profesores', {"nombre": "Juan"}, {"edad": 35})

# Eliminar
eliminar_varios_documentos(db, 'profesores', {"edad": {"$lt": 30}})
```

## 🎨 Características del Notebook

### ✅ Optimizaciones para Windows
- Detección automática de MongoDB
- Rutas de Windows con `pathlib`
- Gestión de errores robusta
- Mensajes informativos con emojis
- Sin dependencias de Linux/Google Colab

### ✅ Funcionalidades Avanzadas
- Descarga automática de datasets
- Procesamiento de archivos de texto
- Validación de conexiones
- Progreso de operaciones masivas
- Configuración de directorios automática

## 🔧 Solución de Problemas

### Error: "No se puede conectar a MongoDB"
1. Verificar que MongoDB esté ejecutándose
2. Comprobar puerto 27017 disponible
3. Revisar firewall/antivirus

### Error: "Archivo no encontrado"
1. Verificar conexión a internet
2. Comprobar permisos de escritura
3. Revisar configuración de proxy

### Error: "Módulo pymongo no encontrado"
```bash
pip install --upgrade pymongo
```

## 📚 Recursos Adicionales

- [Documentación oficial MongoDB](https://docs.mongodb.com/)
- [PyMongo Tutorial](https://pymongo.readthedocs.io/en/stable/tutorial.html)
- [MongoDB University](https://university.mongodb.com/)
- [Dataset UCI Machine Learning](https://archive.ics.uci.edu/ml/datasets.php)

## 👨‍💻 Autor
**Efren Bohorquez**
- Universidad Central
- Maestría en Analítica de Datos
- Curso: Big Data

## 📄 Licencia
Este proyecto es para fines educativos - Universidad Central 2025

---
*Última actualización: Septiembre 2025*