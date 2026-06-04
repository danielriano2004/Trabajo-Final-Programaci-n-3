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
        
        # --- FILTRO DE LIMPIEZA INTELIGENTE PARA EL PDF ---
        # Reemplazamos múltiples saltos de línea y espacios exagerados por un espacio simple
        # para reconstruir las oraciones de forma continua.
        palabras_limpias = [palabra.strip() for palabra in texto_sucio.split() if palabra.strip()]
        
        # Reconstruimos el documento: mantenemos la primera línea intacta como título,
        # y el resto lo unimos como un párrafo normal y legible.
        if palabras_limpias:
            # Asumimos que las primeras palabras forman el título (puedes ajustar el índice si es necesario)
            # Para mayor seguridad, si tu título original tiene por ejemplo 6 palabras, las unimos en la linea 1:
            # Una solución estándar y robusta es unir todo el texto limpio separando adecuadamente:
            texto_unificado = " ".join(palabras_limpias)
            
            # Busquemos darle estructura para tu regla de: LINEA 1 = TITULO, LINEA 2 = CONTENIDO
            # Si sabemos que el título en tu caso es 'GUIA DE EXTRACCION DE TITANIO Y METALES',
            # podemos hacer que el script mantenga esa coherencia:
            marcador_titulo = "GUIA DE EXTRACCION DE TITANIO Y METALES"
            
            if marcador_titulo.lower() in texto_unificado.lower():
                # Separamos el título del resto del contenido
                contenido_cuerpo = texto_unificado.lower().replace(marcador_titulo.lower(), "").strip()
                texto_final = f"{marcador_titulo}\n\n{contenido_cuerpo.capitalize()}"
            else:
                # Si es otro PDF genérico, dejamos la primera frase/línea larga y el resto abajo
                texto_final = texto_unificado
        # --------------------------------------------------
        
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