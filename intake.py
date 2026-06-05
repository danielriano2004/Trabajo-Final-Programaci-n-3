import os
import uuid
from pypdf import PdfReader
import ollama
import config

def procesar_y_convertir_a_txt(ruta_archivo):
    nombre_base, extension = os.path.splitext(os.path.basename(ruta_archivo))
    texto_final = ""

    if extension.lower() == ".txt":
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            texto_final = f.read()
        ruta_destino = os.path.join(config.CONOCIMIENTO_DIR, f"{nombre_base}.txt")
        if ruta_archivo != ruta_destino:
            with open(ruta_destino, "w", encoding="utf-8") as f:
                f.write(texto_final)
            
    elif extension.lower() == ".pdf":
        reader = PdfReader(ruta_archivo)
        texto_sucio = ""
        for page in reader.pages:
            texto_sucio += page.extract_text() + "\n"
        
        # --- FILTRO DE LIMPIEZA PARA EL PDF ---
        # Reemplazamos múltiples saltos de línea y espacios exagerados por un espacio simple
        # para reconstruir las oraciones de forma continua.
        palabras_limpias = [palabra.strip() for palabra in texto_sucio.split() if palabra.strip()]
        

        if palabras_limpias:
            texto_unificado = " ".join(palabras_limpias)
            
            titulo_automatico = nombre_base.replace("_", " ").upper()
            
            #Línea 1 es el Título, el resto es el Contenido
            texto_final = f"{titulo_automatico}\n\n{texto_unificado}"

        
        ruta_txt = os.path.join(config.CONOCIMIENTO_DIR, f"{nombre_base}.txt")
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write(texto_final)
            
    return f"{nombre_base}.txt", texto_final

def indexar_texto_en_qdrant(qdrant_client, nombre_archivo, texto):
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    if not lineas:
        return False
        
    titulo = lineas[0]
    contenido = "\n".join(lineas[1:])
    
    chunks = []
    palabras = contenido.split()
    tamano_chunk_palabras = 120 
    
    if not palabras:
        chunks.append(f"ENCICLOPEDIA: {titulo}\nINFORMACION: Documento base sin descripcion extensa.")
    else:
        for i in range(0, len(palabras), tamano_chunk_palabras):
            fragmento = " ".join(palabras[i:i + tamano_chunk_palabras])
            texto_chunk = f"ENCICLOPEDIA TEMA: {titulo}\nDETALLE: {fragmento}"
            chunks.append(texto_chunk)
        
    for chunk in chunks:
        response = ollama.embeddings(model=config.EMBED_MODEL, prompt=chunk)
        vector = response["embedding"]
        
        point_id = str(uuid.uuid4())
        payload = {
            "content": chunk,
            "source": nombre_archivo,
            "titulo": titulo.lower()
        }
        
        qdrant_client.upsert(
            collection_name=config.COLLECTION_NAME,
            points=[{"id": point_id, "vector": vector, "payload": payload}]
        )
    return True

if __name__ == "__main__":
    from qdrant_client import QdrantClient
    client = QdrantClient(url=config.QDRANT_HOST)
    
    print("Reiniciando coleccion en Qdrant...")
    if client.collection_exists(collection_name=config.COLLECTION_NAME):
        client.delete_collection(collection_name=config.COLLECTION_NAME)
        
    client.create_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config={"size": 768, "distance": "Cosine"}
    )
    print("Base de datos Vectorial Limpia e Inicializada.")
    
    print(f"Buscando archivos locales para indexar en: {config.CONOCIMIENTO_DIR}...")
    if os.path.exists(config.CONOCIMIENTO_DIR):
        archivos = [f for f in os.listdir(config.CONOCIMIENTO_DIR) if f.lower().endswith(('.txt', '.pdf'))]
        
        if not archivos:
            print("No se encontraron archivos .txt o .pdf en la carpeta 'alimento_rag' para indexar.")
        else:
            for archivo in archivos:
                ruta_completa = os.path.join(config.CONOCIMIENTO_DIR, archivo)
                print(f"Indexando archivo local de respaldo: {archivo}...")
                
                nombre_txt, texto_extraido = procesar_y_convertir_a_txt(ruta_completa)
                exito = indexar_texto_en_qdrant(client, nombre_txt, texto_extraido)
                
                if exito:
                    print(f"OK: {archivo} vectorizado correctamente.")
                else:
                    print(f"ERROR: No se pudo procesar {archivo}.")
            print("Proceso de indexacion masiva inicial completado con exito.")
    else:
        print("La carpeta 'alimento_rag' no existia. Ha sido creada, pero esta vacia.")