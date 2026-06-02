"""
Flujo:
  1. retrieve  — embed query + búsqueda Qdrant + reranking híbrido + filtro
  2. generate  — construye prompt con contexto e invoca el LLM
  3. ask       — orquesta ambas fases y devuelve la respuesta final
"""

import re
import time

import ollama
from qdrant_client import QdrantClient

import config


# ─────────────────────────────────────────────────────────────
# 1. RETRIEVAL
# ─────────────────────────────────────────────────────────────

def embed_query(query: str) -> list[float]:
    """Vectoriza la consulta."""
    resp = ollama.embeddings(
        model=config.EMBED_MODEL,
        prompt=query
    )
    return resp["embedding"]


def search_qdrant(vector: list[float], collection: str) -> list:
    """Busca los fragmentos más similares."""
    client = QdrantClient(
        host=config.QDRANT_HOST,
        port=config.QDRANT_PORT
    )

    result = client.query_points(
        collection_name=collection,
        query=vector,
        limit=config.RETRIEVAL_LIMIT
    )

    return result.points


def hybrid_rerank(hits: list, query: str) -> list[dict]:
    """
    Score semántico + bonus lexical.
    """

    terms = [
        w for w in re.findall(r"\w+", query.lower())
        if len(w) > 3
    ]

    scored = []

    for hit in hits:

        content = hit.payload.get("content", "")

        bonus = sum(
            config.LEXICAL_BONUS
            for term in terms
            if term in content.lower()
        )

        scored.append(
            {
                "source": hit.payload.get("source", "?"),
                "content": content,
                "similarity": hit.score + bonus
            }
        )

    scored.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return [
        chunk
        for chunk in scored
        if chunk["similarity"] >= config.SCORE_THRESHOLD
    ]


def retrieve(
    query: str,
    collection: str = config.COLLECTION_NAME
) -> list[dict]:

    t0 = time.perf_counter()

    vector = embed_query(query)

    hits = search_qdrant(
        vector,
        collection
    )

    chunks = hybrid_rerank(
        hits,
        query
    )

    print(
        f"[RETRIEVAL] "
        f"{len(chunks)} chunks relevantes "
        f"({time.perf_counter() - t0:.2f}s)"
    )

    return chunks


# ─────────────────────────────────────────────────────────────
# 2. GENERATION
# ─────────────────────────────────────────────────────────────

def build_context(chunks: list[dict]) -> str:
    """Construye el contexto para el LLM."""

    lines = []

    for i, chunk in enumerate(chunks, start=1):

        lines.append(
            f"--- Fragmento {i} "
            f"(fuente: {chunk['source']}) ---"
        )

        lines.append(chunk["content"])

    return "\n".join(lines)


def generate(
    query: str,
    chunks: list[dict]
) -> str:

    system = (
        "Eres un asistente de recuperación documental. "
        "Responde únicamente usando el contexto proporcionado. "
        "Si la respuesta no está en el contexto responde: "
        "'No encontré esa información en los documentos.'"
    )

    user = (
        f"Contexto:\n{build_context(chunks)}\n\n"
        f"Pregunta: {query}\n\n"
        f"Respuesta:"
    )

    t0 = time.perf_counter()

    response = ollama.chat(
        model=config.LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": user
            }
        ]
    )

    print(
        f"[GENERATION] "
        f"{time.perf_counter() - t0:.2f}s"
    )

    return response["message"]["content"]


# ─────────────────────────────────────────────────────────────
# 3. PIPELINE COMPLETO
# ─────────────────────────────────────────────────────────────

def ask(
    query: str,
    collection: str = config.COLLECTION_NAME
) -> str:

    chunks = retrieve(
        query,
        collection
    )

    if not chunks:
        return (
            "No se encontraron fragmentos "
            "relevantes para esa pregunta."
        )

    return generate(
        query,
        chunks
    )


# ─────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    pregunta = input("Pregunta: ")

    print("\nBuscando...\n")

    respuesta = ask(pregunta)

    print("\n" + "=" * 60)
    print(respuesta)
    print("=" * 60)
