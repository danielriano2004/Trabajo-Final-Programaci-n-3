from qdrant_client import QdrantClient
import ollama
import config

qdrant_client = QdrantClient(url=config.QDRANT_HOST)

def embed_query(query):
    response = ollama.embeddings(model=config.EMBED_MODEL, prompt=query)
    return response["embedding"]

def hybrid_rerank(hits, query):
    query_words = set(query.lower().split())
    approved_chunks = []
    
    for hit in hits:
        # Extraemos de forma segura el score y los metadatos segun el tipo de objeto retornado
        if hasattr(hit, 'score'):
            score = hit.score
            payload = hit.payload or {}
        else:
            score = hit.get('score', 0)
            payload = hit.get('payload', {})
            
        content = payload.get("content", "")
        titulo = payload.get("titulo", "")
        
        if any(word in titulo for word in query_words):
            score += config.LEXICAL_BONUS
            
        if score >= config.SCORE_THRESHOLD:
            approved_chunks.append(content)
            
    return approved_chunks

def generate(query, chunks):
    context = "\n\n---\n\n".join(chunks)
    
    system_prompt = (
        "Actuas como una Enciclopedia Automatizada de Subnautica. Tu objetivo es proveer "
        "informacion precisa, objetiva y resumida basandote UNICAMENTE en los datos provistos "
        "en el contexto. Responde de forma fluida y natural al usuario. No inventes datos. "
        "Si el contexto esta vacio o no contiene la respuesta, responde exactamente: "
        "'No poseo esa informacion en mis registros enciclopedicos actuales'."
    )
    
    user_prompt = f"REGISTROS DE LA ENCICLOPEDIA:\n{context}\n\nCONSULTA DEL USUARIO: {query}"
    
    response = ollama.chat(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response['message']['content']

def ask(query):
    try:
        query_vector = embed_query(query)
        hits = []
        
        # --- SISTEMA DE COMPATIBILIDAD TOTAL PARA QDRANT ---
        try:
            # 1. Intentar el metodo moderno de la API
            response = qdrant_client.query_points(
                collection_name=config.COLLECTION_NAME,
                query=query_vector,
                limit=5
            )
            hits = response.points
        except Exception:
            try:
                # 2. Intentar el metodo clasico si el primero falla
                hits = qdrant_client.search(
                    collection_name=config.COLLECTION_NAME,
                    query_vector=query_vector,
                    limit=5
                )
            except Exception:
                # 3. Intentar scroll si las funciones de busqueda directa fallan
                response = qdrant_client.scroll(
                    collection_name=config.COLLECTION_NAME,
                    limit=5,
                    with_payload=True,
                    with_vectors=False
                )
                hits = response[0]
            
        filtrados = hybrid_rerank(hits, query)
        
        # SALVAVIDAS: Si el re-rankeo fue muy estricto y vacio todo, pero Qdrant si encontro algo,
        # le pasamos obligatoriamente el mejor fragmento a la IA para que pueda responder un "Si" o "No" estructurado.
        if not filtrados and hits:
            if hasattr(hits[0], 'payload') and hits[0].payload:
                primera_opcion = hits[0].payload.get("content", "")
            else:
                primera_opcion = hits[0].get('payload', {}).get('content', '') if isinstance(hits[0], dict) else ""
                
            if primera_opcion:
                filtrados.append(primera_opcion)
                
        return generate(query, filtrados)
    except Exception as e:
        return f"Error en el procesamiento del Cerebro RAG: {str(e)}"