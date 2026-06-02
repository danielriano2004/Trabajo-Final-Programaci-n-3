import os
import random
from typing import List

# 1. Agrupación de todas las importaciones al inicio del archivo
import fitz  # PyMuPDF
import ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# ==========================================
# CONFIGURACIÓN Y CONSTANTES
# ==========================================
COLLECTION_NAME = "monit_rag_collection"
EMBEDDING_MODEL = "nomic-embed-text"
QDRANT_HOST = "localhost"  # Cambiar a "qdrant" si corres este script DENTRO de Docker
QDRANT_PORT = 6333

# ==========================================
# PROCESAMIENTO DE DOCUMENTOS
# ==========================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae de forma limpia todo el texto de un archivo PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"No se encontró el archivo en la ruta: {pdf_path}")

    print(f"[+] Extrayendo texto de: {pdf_path}")

    document = fitz.open(pdf_path)

    # Optimización de memoria: Unir elementos de una lista es mucho más rápido
    # que concatenar strings en un bucle clásico (full_text += ...)
    text_pages = [page.get_text() for page in document]

    document.close()

    return "\n".join(text_pages)


def split_text_into_chunks(text: str) -> List[str]:
    """Divide un texto plano en fragmentos con un margen de solapamiento."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    return splitter.split_text(text)


def display_random_chunks(chunks: List[str], sample_size: int = 3) -> None:
    """Muestra una muestra aleatoria de fragmentos para depuración visual."""
    size = min(sample_size, len(chunks))
    selected_chunks = random.sample(chunks, size)

    print(f"\n--- Inspección de {size} Fragmentos Aleatorios ---")
    for i, chunk in enumerate(selected_chunks, 1):
        print(f"\n[Fragmento #{i}]")
        print(chunk[:150] + "..." if len(chunk) > 150 else chunk)
        print("-" * 50)

# ==========================================
# VALIDACIÓN DE SERVICIOS (HEALTH CHECKS)
# ==========================================

def verify_infrastructure(client: QdrantClient) -> bool:
    """Verifica que tanto la base de datos como el motor de IA respondan."""
    print("\n--- Verificando Conectividad de Infraestructura ---")

    # Test Qdrant
    try:
        client.get_collections()
        print("[✓] QDRANT: Operacional y escuchando.")
    except Exception as e:
        print(f"[!] QDRANT: Error de conexión: {e}")
        return False

    # Test Ollama
    try:
        models_response = ollama.list()
        print("[✓] OLLAMA: Operacional y escuchando.")

        available_models = [
            m['model']
            for m in models_response.get('models', [])
        ]

        print(f"    -> Modelos en contenedor: {available_models}")

    except Exception as e:
        print(f"[!] OLLAMA: Error de conexión: {e}")
        return False

    return True

# ==========================================
# INGESTA DE DATOS
# ==========================================

def upload_chunks_to_qdrant(pdf_path: str) -> None:
    """Orquesta la extracción, vectorización e ingesta masiva en Qdrant."""
    client = QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        timeout=5.0
    )

    # Cancelar operación si los servicios Docker están apagados
    if not verify_infrastructure(client):
        print("[!] Ingesta cancelada: Revisa tus contenedores de Docker.")
        return

    # 1. Procesar documento
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text_into_chunks(text)

    print(f"[+] Texto segmentado con éxito en {len(chunks)} fragmentos.")

    # Mostrar muestra de depuración
    display_random_chunks(chunks, sample_size=2)

    # 2. Inicializar colección en la base de datos de vectores
    if not client.collection_exists(COLLECTION_NAME):
        print(f"[+] Creando colección '{COLLECTION_NAME}'...")

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )

    # 3. Vectorización e Ingesta masiva
    print(f"[+] Generando embeddings y preparando puntos para Qdrant...")

    points = []

    for idx, chunk in enumerate(chunks):
        try:
            response = ollama.embeddings(
                model=EMBEDDING_MODEL,
                prompt=chunk
            )

            points.append(
                PointStruct(
                    id=idx,
                    vector=response["embedding"],
                    payload={
                        "source": os.path.basename(pdf_path),
                        "content": chunk
                    }
                )
            )

        except Exception as e:
            print(f"[!] Error procesando fragmento #{idx}: {e}")
            return

    # Optimización mayor: Subida en Batch (Fuera del bucle for)
    print(f"[+] Subiendo {len(points)} vectores a Qdrant en un único bloque...")

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print("\n[✓] ¡Proceso de ingesta completado con éxito absoluto!")

# ==========================================
# PUNTO DE ENTRADA ÚNICO (MAIN)
# ==========================================

if __name__ == "__main__":
    # Definimos las variables de ejecución aquí
    TARGET_PDF = "./single_document/test.pdf"

    print("=== INICIANDO PIPELINE DE INGESTA RAG ===")

    try:
        upload_chunks_to_qdrant(TARGET_PDF)

        print(
            f"\n[!] Verifica tus vectores en: "
            f"http://{QDRANT_HOST}:{QDRANT_PORT}/dashboard"
        )

    except Exception as e:
        print(f"\n[!] Ocurrió un error inesperado en la ejecución: {e}")
