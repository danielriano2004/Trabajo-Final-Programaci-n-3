# ── Base de datos vectorial ──────────────────────────────────
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

COLLECTION_NAME = "monit_rag_collection"
VECTOR_SIZE = 768

# ── Modelos Ollama ───────────────────────────────────────────
EMBED_MODEL = "nomic-embed-text"

LLM_MODEL = "gemma2:2b"   # cambiar si no lo tienes

# ── Chunking ─────────────────────────────────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# ── Recuperación ─────────────────────────────────────────────
RETRIEVAL_LIMIT = 6
SCORE_THRESHOLD = 0.55
LEXICAL_BONUS = 0.03
