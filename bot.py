import time
import json
import urllib.request
import os
from qdrant_client.http import models

import config
import intake
import cerebro_rag

TOKEN = ""
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

DICCIONARIO_SALUDOS = {
    "hola", "hello", "hi", "bonjour", "hallo", "ciao", "ola", "oi",
    "buenos dias", "buenas tardes", "buenas noches", "saludos", "que tal"
}

DICCIONARIO_AYUDA = {
    "ayuda", "help", "que puedes hacer", "que haces", "cuales son tus funciones",
    "funciones", "comandos", "instrucciones", "como funcionas", "manual"
}

def make_request(url, data=None):
    try:
        req = urllib.request.Request(url)
        if data:
            req.add_header('Content-Type', 'application/json')
            data_bytes = json.dumps(data).encode('utf-8')
            res = urllib.request.urlopen(req, data=data_bytes)
        else:
            res = urllib.request.urlopen(req)
        return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"Error de red en peticion: {e}")
        return None

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    make_request(url, payload)

def send_chat_action(chat_id, action="typing"):
    url = f"{BASE_URL}/sendChatAction"
    payload = {"chat_id": chat_id, "action": action}
    make_request(url, payload)

def descargar_archivo_telegram(file_id, nombre_destino):
    url_info = f"{BASE_URL}/getFile?file_id={file_id}"
    res_data = make_request(url_info)
    
    if res_data and res_data.get("ok"):
        file_path = res_data["result"]["file_path"]
        url_descarga = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        ruta_local = os.path.join(config.TEMP_DIR, nombre_destino)
        urllib.request.urlretrieve(url_descarga, ruta_local)
        return ruta_local
    return None

def obtener_mensaje_ayuda():
    return (
        "CONSOLA DE ADMINISTRACION Y CONSULTA - ENCICLOPEDIA IA\n"
        "A continuacion se detallan las funciones operativas del sistema:\n\n"
        "1. CONSULTA SEMANTICA (RAG):\n"
        "Escriba cualquier consulta libre en el chat. La IA localizara la informacion en la base vectorial Qdrant y generara una respuesta adaptada.\n\n"
        "2. INGESTA DE DOCUMENTOS:\n"
        "Adjunte y envie un archivo con extension .txt o .pdf. El sistema lo procesara, segmentara e indexara en caliente de forma automatica.\n\n"
        "3. LISTAR REPOSITORIO (/archivos):\n"
        "Escriba el comando /archivos para obtener la lista de documentos que residen actualmente en la base de datos.\n\n"
        "4. INSPECCIONAR CONTENIDO (/contenido):\n"
        "Sintaxis: /contenido nombre_archivo\n"
        "Muestra el texto plano guardado dentro de un documento especifico.\n\n"
        "5. MODIFICAR REGISTRO (/editar):\n"
        "Sintaxis: /editar nombre_archivo | TITULO \\n Contenido nuevo\n"
        "Elimina los vectores anteriores, reescribe el archivo fisico e indexa los nuevos datos.\n\n"
        "6. PURGAR REGISTRO (/eliminar):\n"
        "Sintaxis: /eliminar nombre_archivo\n"
        "Elimina el documento del disco y remueve permanentemente sus vectores de Qdrant."
    )

def manejar_actualizacion(update):
    if "message" not in update: return
    message = update["message"]
    chat_id = message["chat"]["id"]
    
    # --- INGESTA ---
    if "document" in message:
        doc = message["document"]
        file_id = doc["file_id"]
        file_name = doc["file_name"]
        
        if file_name.lower().endswith(('.pdf', '.txt')):
            send_message(chat_id, f"Procesando archivo recibido: '{file_name}'...")
            send_chat_action(chat_id, "upload_document")
            
            ruta_temp = descargar_archivo_telegram(file_id, file_name)
            if ruta_temp:
                nombre_txt, texto_extraido = intake.procesar_y_convertir_a_txt(ruta_temp)
                exito = intake.indexar_texto_en_qdrant(cerebro_rag.qdrant_client, nombre_txt, texto_extraido)
                
                if exito:
                    send_message(chat_id, f"Procesamiento completado. Archivo indexado y guardado como '{nombre_txt}'.")
                else:
                    send_message(chat_id, "Error: Estructura de documento invalida o vacia.")
                
                if os.path.exists(ruta_temp): os.remove(ruta_temp)
        else:
            send_message(chat_id, "Formato denegado. Solo se permite el procesamiento de archivos .txt y .pdf.")
        return

    # --- TEXTO Y COMANDOS ---
    if "text" in message:
        user_text = message["text"].strip()
        user_text_lower = user_text.lower()
        
        if user_text_lower in DICCIONARIO_SALUDOS or user_text_lower == "/start":
            send_message(chat_id, "Hola, soy tu asistente de la Enciclopedia Inteligente. Para saber que puedo hacer, como operar los datos o conocer mis comandos, por favor escribe la palabra: ayuda")
            return
            
        if any(frase in user_text_lower for frase in DICCIONARIO_AYUDA):
            ayuda_texto = obtener_mensaje_ayuda()
            send_message(chat_id, ayuda_texto)
            return

        if user_text_lower == "/archivos":
            try:
                response = cerebro_rag.qdrant_client.scroll(
                    collection_name=config.COLLECTION_NAME,
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
                puntos = response[0]
                archivos_unicos = set()
                for p in puntos:
                    payload_nodo = p.payload if hasattr(p, 'payload') else p.get('payload', {})
                    if payload_nodo and "source" in payload_nodo:
                        archivos_unicos.add(payload_nodo["source"])
                
                if archivos_unicos:
                    lista_texto = "Documentos actualmente indexados en la Base de Datos:\n\n"
                    for idx, arch in enumerate(sorted(archivos_unicos), 1):
                        lista_texto += f"{idx}. {arch}\n"
                    lista_texto += "\nPuede usar /contenido nombre_archivo para revisar el texto de cualquiera."
                    send_message(chat_id, lista_texto)
                else:
                    send_message(chat_id, "La base de datos vectorial se encuentra vacia actualmente.")
            except Exception as e:
                send_message(chat_id, f"Error al interrogar el repositorio de Qdrant: {str(e)}")
            return

        if user_text_lower.startswith("/contenido"):
            nombre_doc = user_text.replace("/contenido", "").strip()
            if not nombre_doc:
                send_message(chat_id, "Error de sintaxis. Escriba: /contenido nombre_del_archivo.txt")
                return
            if not nombre_doc.endswith(".txt"): nombre_doc += ".txt"
            
            ruta_txt = os.path.join(config.CONOCIMIENTO_DIR, nombre_doc)
            if os.path.exists(ruta_txt):
                try:
                    with open(ruta_txt, "r", encoding="utf-8") as f:
                        cuerpo_archivo = f.read()
                    send_message(chat_id, f"Contenido del archivo '{nombre_doc}':\n\n{cuerpo_archivo}")
                except Exception as e:
                    send_message(chat_id, f"Error en lectura de disco: {str(e)}")
            else:
                send_message(chat_id, f"El archivo '{nombre_doc}' no existe en el almacenamiento del servidor.")
            return

        if user_text_lower.startswith("/eliminar"):
            nombre_doc = user_text.replace("/eliminar", "").strip()
            if not nombre_doc:
                send_message(chat_id, "Error de sintaxis. Escriba: /eliminar nombre_archivo")
                return
            if not nombre_doc.endswith(".txt"): nombre_doc += ".txt"
            
            ruta_txt = os.path.join(config.CONOCIMIENTO_DIR, nombre_doc)
            if os.path.exists(ruta_txt):
                os.remove(ruta_txt)
                cerebro_rag.qdrant_client.delete(
                    collection_name=config.COLLECTION_NAME,
                    points_selector=models.Filter(
                        must=[models.FieldCondition(key="source", match=models.MatchValue(value=nombre_doc))]
                    )
                )
                send_message(chat_id, f"El documento '{nombre_doc}' ha sido removido del almacenamiento y de la base vectorial.")
            else:
                send_message(chat_id, f"No se encontro el registro de '{nombre_doc}'.")
            return

        # --- REGLA CORREGIDA DE EDICION ---
        if user_text_lower.startswith("/editar"):
            try:
                datos = user_text.replace("/editar", "").strip().split("|")
                nombre_doc = datos[0].strip()
                nuevo_contenido = datos[1].strip()
                
                # Saneamiento: Si el usuario escribe /n o \n explicitos, los convertimos a saltos fisicos reales
                nuevo_contenido = nuevo_contenido.replace("/n", "\n").replace("\\n", "\n")
                
                if not nombre_doc.endswith(".txt"): nombre_doc += ".txt"
                ruta_txt = os.path.join(config.CONOCIMIENTO_DIR, nombre_doc)
                
                if os.path.exists(ruta_txt):
                    cerebro_rag.qdrant_client.delete(
                        collection_name=config.COLLECTION_NAME,
                        points_selector=models.Filter(
                            must=[models.FieldCondition(key="source", match=models.MatchValue(value=nombre_doc))]
                        )
                    )
                    with open(ruta_txt, "w", encoding="utf-8") as f:
                        f.write(nuevo_contenido)
                    intake.indexar_texto_en_qdrant(cerebro_rag.qdrant_client, nombre_doc, nuevo_contenido)
                    send_message(chat_id, f"Documento '{nombre_doc}' modificado e indexado correctamente.")
                else:
                    send_message(chat_id, f"No se encontro el archivo '{nombre_doc}' para su edicion.")
            except Exception:
                send_message(chat_id, "Estructura de edicion incorrecta. Use: /editar nombre_archivo | TITULO \\n Contenido")
            return

        # --- EJECUCION POR DEFECTO: CONSULTA RAG ---
        send_chat_action(chat_id, "typing")
        
        tiempo_inicio = time.time()
        respuesta_ia = cerebro_rag.ask(user_text)
        tiempo_final = time.time()
        
        segundos_transcurridos = round(tiempo_final - tiempo_inicio, 4)
        
        send_message(chat_id, respuesta_ia)
        print(f"[TELEMETRIA] Consulta: '{user_text}' -> Procesada con exito en {segundos_transcurridos} segundos.")

def main():
    print("Iniciando pruebas de conexion del sistema...")
    try:
        cerebro_rag.qdrant_client.get_collection(config.COLLECTION_NAME)
        print("Estado Qdrant: Activo y Conectado.")
    except Exception:
        print("Estado Qdrant: Coleccion no detectada. Creando repositorio inicial...")
        cerebro_rag.qdrant_client.recreate_collection(
            collection_name=config.COLLECTION_NAME,
            vectors_config={"size": 768, "distance": "Cosine"}
        )
        print("Estado Qdrant: Coleccion generada exitosamente.")

    url_test = f"{BASE_URL}/getMe"
    req_test = make_request(url_test)
    if req_test and req_test.get("ok"):
        print(f"Estado Telegram: Activo. Bot detectado como: @{req_test['result']['username']}")
    else:
        print("Estado Telegram: Error Critico. Verifique la validez del Token.")
        return

    print("Servidor en linea de forma controlada. Escuchando peticiones...")
    offset = None
    
    while True:
        url = f"{BASE_URL}/getUpdates?timeout=20"
        if offset: url += f"&offset={offset}"
        
        res = make_request(url)
        if res and res.get("ok"):
            for update in res["result"]:
                manejar_actualizacion(update)
                offset = update["update_id"] + 1
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServidor apagado de forma limpia por el usuario.")
