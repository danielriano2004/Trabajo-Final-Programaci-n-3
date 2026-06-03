import os
import json
import urllib.request
import urllib.error
from pypdf import PdfReader
import ollama
import config

# Configuración de la URL de Qdrant basada en tu config.py
QDRANT_URL = f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}"

def qdrant_request(endpoint: str, data: dict = None, method: str = "POST"):
    """Realiza peticiones HTTP directas a la API REST de Qdrant."""
    url = f"{QDRANT_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    jsondata = json.dumps(data).encode('utf-8') if data else None
    try:
        with urllib.request.urlopen(req, data=jsondata) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        raise Exception(f"Error HTTP Qdrant ({e.code}): {error_msg}")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae texto usando pypdf (100% nativo de Python y libre de bloqueos)."""
    reader = PdfReader(pdf_path)
    text_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "".join(text_pages)

def native_chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> list[str]:
    """Algoritmo de fragmentación propio basado en palabras."""
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1
        if current_length >= chunk_size:
            chunks.append(" ".join(current_chunk))
            overlap_count = max(1, chunk_overlap // 10)
            current_chunk = current_chunk[-overlap_count:]
            current_length = sum(len(w) + 1 for w in current_chunk)
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def process_all_pdfs(folder_path: str):
    """Escanea la carpeta, procesa todos los PDFs encontrados y los sube a Qdrant."""
    print(f"\n[1] Conectando con la API REST de Qdrant en {QDRANT_URL}...")
    
    # 1. Borramos la colección anterior para hacer una carga limpia desde cero
    print(f"[2] Reiniciando colección '{config.COLLECTION_NAME}'...")
    try:
        qdrant_request(f"/collections/{config.COLLECTION_NAME}", method="DELETE")
    except Exception:
        pass

    create_payload = {"vectors": {"size": config.VECTOR_SIZE, "distance": "Cosine"}}
    qdrant_request(f"/collections/{config.COLLECTION_NAME}", data=create_payload, method="PUT")

    # 2. Buscar todos los archivos dentro de la carpeta
    if not os.path.exists(folder_path):
        print(f"[!] ERROR: La carpeta '{folder_path}' no existe.")
        return

    all_files = os.listdir(folder_path)
    pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"[!] Advertencia: No se encontraron archivos .pdf dentro de '{folder_path}'.")
        return

    print(f"[+] Se encontraron {len(pdf_files)} archivos PDF para procesar.")
    
    global_points = []
    point_id_counter = 0

    # 3. Recorrer y procesar cada uno de los PDFs
    for pdf_name in pdf_files:
        full_path = os.path.join(folder_path, pdf_name)
        print(f"\n---> Procesando archivo: {pdf_name}")
        
        try:
            raw_text = extract_text_from_pdf(full_path)
            if not raw_text.strip():
                print(f"    [!] Advertencia: El PDF está vacío o es solo una imagen escaneada.")
                continue

            chunks = native_chunk_text(raw_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            print(f"    [+] Generados {len(chunks)} fragmentos de texto.")
            
            print(f"    [3] Creando embeddings con Ollama...")
            for chunk in chunks:
                response = ollama.embeddings(model=config.EMBED_MODEL, prompt=f"search_document: {chunk}")
                
                # Guardamos cada fragmento indexando de qué PDF proviene en el payload
                global_points.append({
                    "id": point_id_counter,
                    "vector": response["embedding"],
                    "payload": {
                        "source": pdf_name,  # <--- Guarda el nombre del archivo real
                        "content": chunk
                    }
                })
                point_id_counter += 1
                
        except Exception as e:
            print(f"    [!] Error al procesar {pdf_name}: {e}")
            continue

    # 4. Envío en lote masivo a Qdrant vía HTTP REST
    if global_points:
        print(f"\n[4] Subiendo un total de {len(global_points)} vectores acumulados a Qdrant...")
        upsert_payload = {"points": global_points}
        qdrant_request(f"/collections/{config.COLLECTION_NAME}/points", data=upsert_payload, method="PUT")
        print("\n[✓] ¡Base de datos Multi-PDF actualizada con éxito absoluto!")
    else:
        print("[!] No se generaron vectores para subir.")

if __name__ == "__main__":
    print("======================================================")
    print(" INGESTA MULTI-PDF ")
    print("======================================================")
    
    # Esta es la carpeta donde vas a meter todos tus archivos
    TARGET_FOLDER = "./alimento_rag"
    process_all_pdfs(TARGET_FOLDER)