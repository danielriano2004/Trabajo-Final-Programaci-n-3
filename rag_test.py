import re
import time
import json
import urllib.request
import urllib.error
import ollama
import config

QDRANT_URL = f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}"

def qdrant_post(endpoint: str, data: dict):
    """Envia peticiones POST directas a Qdrant usando Python nativo."""
    url = f"{QDRANT_URL}{endpoint}"
    req = urllib.request.Request(url, method="POST")
    req.add_header('Content-Type', 'application/json')
    jsondata = json.dumps(data).encode('utf-8')
    with urllib.request.urlopen(req, data=jsondata) as response:
        return json.loads(response.read().decode('utf-8'))

def embed_query(query: str) -> list[float]:
    """Genera vector de consulta usando Ollama."""
    resp = ollama.embeddings(model=config.EMBED_MODEL, prompt=f"search_query: {query}")
    return resp["embedding"]

def retrieve(query: str, collection: str) -> list[dict]:
    """Recupera y reordena fragmentos mediante la API REST de Qdrant."""
    t0 = time.perf_counter()
    query_vector = embed_query(query)

    search_payload = {
        "vector": query_vector,
        "limit": config.RETRIEVAL_LIMIT,
        "with_payload": True
    }
    
    response = qdrant_post(f"/collections/{collection}/points/query", data=search_payload)
    hits = response.get("result", {}).get("points", [])

    query_words = set(re.findall(r'\w+', query.lower()))
    reranked = []

    for hit in hits:
        payload = hit.get("payload", {})
        # Usamos 'content' para emparejar con tu script de intake.py
        content = payload.get("content", "")
        content_lower = content.lower()
        score = hit.get("score", 0.0)

        # Incremento automático por coincidencia de palabras (para cualquier recurso)
        bonus = sum(config.LEXICAL_BONUS for word in query_words if word in content_lower)
        final_score = score + bonus

        reranked.append({
            "score": final_score,
            "content": content,
            "source": payload.get("source", "Desconocido")
        })

    filtered = [c for c in reranked if c["score"] >= config.SCORE_THRESHOLD]
    sorted_chunks = sorted(filtered, key=lambda x: x["score"], reverse=True)

    print(f"[RETRIEVAL] {len(sorted_chunks)} chunks válidos procesados en {time.perf_counter() - t0:.2f}s")
    return sorted_chunks

def generate(query: str, chunks: list[dict]) -> str:
    """Genera respuesta usando Ollama optimizado para Gemma 2."""
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(f"--- Fragmento {i} (Origen: {chunk['source']}) ---\n{chunk['content']}")
    context = "\n\n".join(context_blocks)

    # El prompt ahora le ordena explícitamente buscar nombres de biomas, recetas o ubicaciones de CUALQUIER elemento
    system = (
        "Eres un asistente experto e investigador del juego Subnautica. Tu labor es responder la duda "
        "del jugador usando los fragmentos de los documentos provistos de forma amigable y muy detallada. "
        "Menciona nombres de zonas, biomas, coordenadas, recetas de crafteo, fragmentos o afloramientos que aparezcan descritos "
        "en los textos. Responde siempre en Español de manera natural."
    )
    user = f"Documentos de investigación recopilados:\n{context}\n\nPregunta del jugador: {query}\n\nRespuesta detallada:"

    t0 = time.perf_counter()
    resp = ollama.chat(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ],
        options={
            "temperature": 0.4
        }
    )
    print(f"[GENERATION] LLM respondió en {time.perf_counter() - t0:.2f}s")
    return resp["message"]["content"]

def ask(query: str, collection: str = config.COLLECTION_NAME) -> str:
    """Función principal RAG."""
    chunks = retrieve(query, collection)
    if not chunks:
        return "No encontré registros sobre ese elemento o recurso en los archivos de la enciclopedia local."
    return generate(query, chunks)

if __name__ == "__main__":
    print("====================================================")
    print("🤖 MOTOR RAG LOCAL REST - PRUEBA INTERACTIVA")
    print("====================================================\n")
    
    pregunta = input("Introduce tu pregunta sobre el PDF: ")
    if pregunta.strip():
        respuesta = ask(pregunta)
        print(f"\n================ RESPUESTA ================\n{respuesta}\n===========================================")