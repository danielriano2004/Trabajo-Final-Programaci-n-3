import time
import json
import urllib.request
import urllib.error
import rag_test

# 🔑 TU TOKEN DE TELEGRAM
TOKEN = "8901909584:AAEp79Bs1PsNa4EvZ3AR-jbQ7fjQfI1t5qI"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def telegram_post(method_name: str, payload: dict):
    """Envía peticiones HTTP POST seguras a la API de Telegram."""
    url = f"{BASE_URL}/{method_name}"
    req = urllib.request.Request(url, method="POST")
    req.add_header('Content-Type', 'application/json')
    jsondata = json.dumps(payload).encode('utf-8')
    try:
        with urllib.request.urlopen(req, data=jsondata) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[!] Error en la API de Telegram: {e}")
        return None

def send_message(chat_id: int, text: str):
    """Envía un mensaje de texto de vuelta al usuario en Telegram."""
    payload = {"chat_id": chat_id, "text": text}
    telegram_post("sendMessage", payload)

def send_chat_action(chat_id: int, action: str = "typing"):
    """Envía el estado visual 'Escribiendo...' a la app de Telegram."""
    payload = {"chat_id": chat_id, "action": action}
    telegram_post("sendChatAction", payload)

def main():
    if TOKEN == "TU_TOKEN_DE_TELEGRAM_AQUI":
        print("[!] ERROR crítico: Debes poner tu Token de Telegram.")
        return

    print("====================================================")
    print("[✓] BOT DE TELEGRAM ULTRA-ROBUSTO v3 (INDESTRUCTIBLE)")
    print("Escuchando mensajes en tiempo real de forma local...")
    print("====================================================")

    offset = 0
    
    PALABRAS_FUNCIONES = ["que haces", "que puedes hacer", "cuales son tus funciones", "como funcionas", "ayuda", "funciones", "comandos", "help", "commands", "info"]
    CHARLA_COLOQUIAL = ["como estas", "cómo estás", "como va", "cómo va", "todo bien", "quien eres", "quién eres", "que cuentas", "qué cuentas"]
    CORTESIAS = {"gracias", "muchas gracias", "excelente", "buenisimo", "buenísimo", "ok", "listo", "perfecto", "thank you", "thanks", "awesome", "perfect", "great", "ty"}
    
    # Lista ampliada de conceptos clave para capturar cualquier pregunta de recursos de forma universal
    PALABRAS_CLAVE_JUEGO = [
        "subnautica", "leviathan", "fauna", "historia", "teoria", "guia", "planeta", "4546b", 
        "criatura", "huevo", "bacteria", "kharaa", "precursor", "supervivencia", "reaper", 
        "titanio", "recurso", "mineral", "platino", "oro", "plata", "cobre", "diamante", 
        "litio", "magnetita", "azufre", "niquel", "cianita", "plomo", "receta", "crafteo", "donde"
    ]

    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=5"
            req = urllib.request.urlopen(url, timeout=60)
            
            response = json.loads(req.read().decode('utf-8'))
            updates = response.get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_text = update["message"]["text"]
                    user_name = update["message"]["from"].get("first_name", "Usuario")
                    
                    print(f"\n[+] Mensaje recibido de {user_name}: '{user_text}'")
                    
                    texto_limpio = user_text.lower().strip()
                    for car in ["?", "!", "¡", "¿", ".", ",", ";", "-", "═", "(", ")", "[", "]", "_", "*"]:
                        texto_limpio = texto_limpio.replace(car, "")
                    
                    if user_text == "/start":
                        bienvenida = (
                            f"¡Hola {user_name}! 🌊🤖\n\n"
                            f"Bienvenido a tu asistente experto en Subnautica.\n"
                            f"He procesado con éxito 5 documentos sobre el Planeta 4546B.\n\n"
                            f"Escribe 'funciones' o 'help' si quieres saber qué puedo hacer, o hazme una pregunta directamente."
                        )
                        send_message(chat_id, bienvenida)
                        
                    elif any(func in texto_limpio for func in PALABRAS_FUNCIONES):
                        menu_funciones = (
                            f"🤖 *Funciones de este Asistente Local*:\n\n"
                            f"1️⃣ *Responder sobre Subnautica*: Tengo cargada la información de tus PDFs sobre historia, fauna, teorías y supervivencia.\n"
                            f"2️⃣ *Entendimiento mixto*: Puedes saludar y preguntar todo junto (ej: 'Hola, ¿dónde encuentro al Reaper Leviathan?').\n"
                            f"3️⃣ *Filtro inteligente*: Respondo saludos y preguntas de cortesía al instante sin consumir recursos de IA.\n\n"
                            f"¿Qué deseas consultar ahora, {user_name}?"
                        )
                        send_message(chat_id, menu_funciones)
                        
                    elif any(charla in texto_limpio for charla in CHARLA_COLOQUIAL):
                        respuesta_cortes = (
                            f"¡Yo estoy excelente, {user_name}! 🤖 Súper optimizado y corriendo de forma 100% local.\n"
                            f"Listo para buscar en los archivos de Subnautica lo que necesites saber. ¿De qué criatura o misterio quieres hablar?"
                        )
                        send_message(chat_id, respuesta_cortes)

                    elif texto_limpio in CORTESIAS:
                        send_message(chat_id, "¡Con muchísimo gusto! Aquí sigo atento en segundo plano por si necesitas más datos. 🦑")

                    elif texto_limpio.startswith(("hol", "hi", "hey", "hell", "gree", "buen", "alo", "aló", "epa", "épa")) and not any(kw in texto_limpio for kw in PALABRAS_CLAVE_JUEGO):
                        respuesta_amable = (
                            f"¡Hola de nuevo, {user_name}! 👋 Aquí estoy listo.\n"
                            f"Dime, ¿qué te gustaría saber o consultar en los documentos de Subnautica?"
                        )
                        send_message(chat_id, respuesta_amable)
                        
                    else:
                        send_chat_action(chat_id, "typing")
                        print(f"[-] Consultando al modelo local 'gemma2:2b'...")
                        respuesta_rag = rag_test.ask(user_text)
                        send_message(chat_id, respuesta_rag)
                        print("[✓] Respuesta RAG enviada con éxito.")
                        
        except urllib.error.URLError:
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n[!] Bot apagado manualmente por el usuario.")
            break
        except Exception as e:
            print(f"[!] Aviso controlado en el bucle: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()