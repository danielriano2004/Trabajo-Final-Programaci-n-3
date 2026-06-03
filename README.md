# Motor RAG Híbrido con Infraestructura Contenerizada para Asistencia de Subnautica en Telegram

Este proyecto implementa un sistema de **Generación Aumentada por Recuperación (RAG - Retrieval-Augmented Generation)** diseñado para actuar como una enciclopedia inteligente y en tiempo real sobre el videojuego *Subnautica*. La solución utiliza una arquitectura distribuida y desacoplada, combinando el procesamiento de lenguaje natural local con almacenamiento vectorial geométrico y un bot automatizado para el despliegue del servicio en Telegram.

---

## 1. Arquitectura del Sistema

El sistema está diseñado bajo un enfoque de microservicios e infraestructura como código (IaC), dividiendo el software en dos grandes capas operacionales:

* **Capa de Infraestructura (Contenerizada):** Gestionada por **Docker Desktop**, la cual aisla los entornos de ejecución a nivel de núcleo (kernel) de los servicios core: **Qdrant** (Base de datos vectorial en Rust) y **Ollama** (Servidor de inferencia local en C++). Esto garantiza la portabilidad absoluta eliminando conflictos de compatibilidad entre sistemas operativos host.
* **Capa de Control y Lógica de Negocio (Local):** Scripts de **Python** que gestionan la lectura de datos, el pipeline de transformación, la orquestación del algoritmo híbrido de búsqueda y la pasarela de red en tiempo real con la API de Telegram.

---

## 2. Tecnologías y Librerías Utilizadas

### Infraestructura (Docker)
* **`qdrant/qdrant:latest`**: Motor de persistencia vectorial de alto rendimiento. Almacena las matrices numéricas de los textos y calcula similitudes geométricas mediante la fórmula de **Distancia Coseno**.
* **`ollama/ollama:latest`**: Entorno de ejecución de raíces neuronales local optimizado mediante `llama.cpp` para el consumo eficiente de memoria RAM/VRAM.

### Código Fuente (Python - Paquetes de Terceros)
* **`pypdf`**: Biblioteca de análisis binario utilizada para decodificar y extraer cadenas de texto en bruto desde documentos PDF almacenados localmente.
* **`ollama`**: SDK oficial para orquestar la comunicación a través del puerto `11434`, abstrayendo las llamadas de generación de embeddings e inferencia de texto.
* **`qdrant-client`**: SDK oficial de integración que provee interfaces estandarizadas para interrogar el índice espacial de Qdrant a través del puerto `6333`.
* **`python-dotenv`**: Componente de seguridad encargado de inyectar variables de entorno críticas y credenciales de acceso desde un archivo protegido `.env`.
* **`requests`**: Pila de red optimizada para gestionar conexiones HTTP persistentes y asíncronas con los endpoints de la API de Telegram.
* **`standard-tokenizer` / `tiktoken`**: Herramienta de normalización lingüística encargada de segmentar el texto en "tokens" para asegurar precisión geométrica durante el corte de documentos.

### Librerías Nativas de Python (Core)
* **`os`**: Manipulación de rutas lógicas y escaneo del sistema de archivos local.
* **`re`**: Motor de Expresiones Regulares empleado para la limpieza de secuencias de texto y tokenización léxica rápida.
* **`json`**: Serialización y deserialización de estructuras de datos para transporte de red.
* **`time`**: Monitoreo y telemetría de latencias del sistema en milisegundos.

---

## 📊 3. Especificaciones del Motor RAG e Inferencia

El proyecto implementa un modelo avanzado de recuperación de conocimiento parametrizado bajo estrictas reglas matemáticas:

1.  **Representación Vectorial (Embeddings):** Se utiliza el modelo **`nomic-embed-text`**. Convierte cualquier bloque de texto en una matriz fija de **768 dimensiones**. Cada dimensión representa un concepto abstracto de semántica, permitiendo mapear el lenguaje humano en un plano espacial multi-dimensional.
2.  **Reranking Híbrido (Léxico + Semántico):** Para mitigar fallas en la búsqueda espacial con nombres propios del juego, el sistema aplica un algoritmo híbrido propio:
    * Primero, recupera los fragmentos con mayor similitud vectorial.
    * Luego, analiza el texto mediante expresiones regulares buscando coincidencias de términos exactos de la pregunta.
    * Si hay coincidencia exacta de palabras clave, el fragmento recibe un **Bono Léxico fijo de `+0.15`** a su puntuación, reordenando los resultados para priorizar datos hiper-específicos.
3.  **Filtro de Seguridad (Score Threshold):** Se define un umbral crítico de **`0.35`**. Cualquier fragmento recuperado por Qdrant que posea una confianza matemática menor a este límite es descartado automáticamente. Esto impide que si el usuario pregunta algo ajeno al juego, el sistema inyecte datos basura al modelo.
4.  **Generación de Respuesta (LLM):** Las entidades sobrevivientes al filtro se inyectan en el prompt de contexto de **`gemma2:2b`** (Modelo autorregresivo de Google con 2 mil millones de parámetros). Gemma realiza un proceso de inferencia de lenguaje condicionado, lo que significa que procesa las instrucciones del sistema y redacta un párrafo coherente en español natural basándose *únicamente* en el conocimiento verídico extraído del PDF.

---

## 4. Manual de Despliegue e Instalación

Siga estrictamente este orden de comandos en su terminal para replicar el entorno inmutable en cualquier computadora:

### Paso 1: Clonar y Preparar el Entorno de Python
Asegúrese de estar en la raíz de la carpeta del proyecto e instale el comando general de dependencias de Python:
```bash
pip install pypdf ollama qdrant-client python-dotenv requests standard-tokenizer

Paso 2: Despliegue de los Contenedores de Infraestructura Aislada
Asegúrese de encontrarse en la carpeta raíz del proyecto donde se ubica el archivo docker-compose.yml y ejecute:


Bash
# Inicialización de contenedores en segundo plano (Modo Detached)
docker compose up -d


Paso 3: Aprovisionamiento Local de los Modelos de Inteligencia Artificial
Inyecte los comandos de descarga directamente en la terminal interactiva del contenedor virtualizado de Ollama:


Bash
# Descarga e inicialización del codificador matemático de embeddings
docker exec -it ollama_container ollama run nomic-embed-text

# Descarga del modelo autorregresivo de lenguaje Gemma 2
docker exec -it ollama_container ollama run gemma2:2b

Paso 4: Carga e Indexación de Conocimiento (Pipeline ETL)
Introduzca sus documentos PDF reales de la enciclopedia de Subnautica dentro de la carpeta local ./alimento_rag/ y ejecute el poblamiento de vectores:


Bash
# Ejecución de la extracción de PDF, segmentación, cálculo vectorial y subida a Qdrant
python intake.py

Paso 5: Inicialización del Bot de Telegram (Producción Local)

Bash
# Encendido del bucle continuo de escucha activa de chats en tiempo real
python bot.py
