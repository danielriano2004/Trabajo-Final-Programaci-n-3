import os

# Configuracion de Red y Modelos
QDRANT_HOST = "http://localhost:6333"
COLLECTION_NAME = "enciclopedia_subnautica"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma2:2b"

# Configuracion de Filtros RAG
SCORE_THRESHOLD = 0.35
LEXICAL_BONUS = 0.15

# Gestion Fisica de Archivos de la Enciclopedia
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONOCIMIENTO_DIR = os.path.join(BASE_DIR, "alimento_rag")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Asegurar que las carpetas existan al arrancar
os.makedirs(CONOCIMIENTO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)