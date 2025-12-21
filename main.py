import feedparser
import requests
import os
import json
import urllib.parse
from datetime import datetime
import pytz
import time

# --- CONFIGURACIÓN DE BARRIOS ---
KEYWORDS = [
    "Barrio Comillas Madrid",
    "Opañel", 
    "San Isidro Carabanchel",
    "Vista Alegre Carabanchel", # Cambiado a Carabanchel para evitar Vistalegres extranjeros
    "Puerta Bonita Madrid", 
    "Buenavista Carabanchel", 
    "Abrantes Carabanchel", 
    "Carabanchel Alto",
    "Carabanchel"
]

# --- PALABRAS A EXCLUIR ---
# Quitamos fútbol, apuestas y lugares de latam que coinciden
NEGATIVE_KEYWORDS = "-fútbol -soccer -apuestas -pronóstico -Colombia -Argentina -Bucaramanga -Chile"

# URL base: inyectamos la query y las negativas
RSS_BASE_URL = "https://news.google.com/rss/search?q={query}+{negatives}+when:1d&hl=es&gl=ES&ceid=ES:es&ned=es&nocache=1"

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    trimmed_history = history[-500:] 
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed_history, f, indent=2)

def send_telegram_message(neighborhood, title, link, date_str):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERROR: Faltan tokens de Telegram.")
        return False

    msg = f"🗞 *Noticia {neighborhood}*\n\n{title}\n📅 {date_str}\n🔗 {link}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    # SISTEMA DE REINTENTOS PARA ERROR 429, el error de muchos intentos en poco tiempo
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=data, timeout=15)
            
            if r.status_code == 200:
                print(f" -> [Telegram] Enviado: {title}")
                return True
            
            # Si Telegram dice "Too Many Requests" (Error 429)
            elif r.status_code == 429:
                retry_after = int(r.json().get("parameters", {}).get("retry_after", 10))
                print(f" ⏳ Rate Limit alcanzado. Esperando {retry_after} segundos...")
                time.sleep(retry_after + 2) # Esperamos lo que pide + 2 segundos extra
                continue # Reintentamos el bucle
            
            else:
                print(f" -> [Telegram] Error no recuperable ({r.status_code}): {r.text}")
                return False

        except Exception as e:
            print(f" -> [Telegram] Excepción de red: {e}")
            time.sleep(5) # Espera un poco antes de reintentar si es error de conexión
    
    return False

def main():
    print("--- Iniciando Bot de Noticias Carabanchel ---")
    
    history = load_history()
    initial_history_count = len(history)
    seen_in_this_run = set() 
    madrid_tz = pytz.timezone('Europe/Madrid')
    noticias_enviadas = 0

    # Preparamos las negativas para la URL (codificadas)
    encoded_negatives = urllib.parse.quote_plus(NEGATIVE_KEYWORDS)

    for neighborhood in KEYWORDS:
        print(f"\n🔍 Buscando: {neighborhood}...")
        
        encoded_query = urllib.parse.quote_plus(neighborhood)
        # Combinamos query + negativas
        rss_url = RSS_BASE_URL.format(query=encoded_query, negatives=encoded_negatives)
        
        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"   Error RSS: {e}")
            continue
        
        if not feed.entries:
            print("   (Sin entradas)")
            continue

        for entry in feed.entries:
            title = entry.get("title", "<sin título>")
            link = entry.get("link", "")
            guid = entry.get("id", link)
            
            if guid in history: continue
            if guid in seen_in_this_run: continue

            published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if not published_struct: continue

            pub_datetime_utc = datetime(*published_struct[:6], tzinfo=pytz.utc)
            pub_datetime_madrid = pub_datetime_utc.astimezone(madrid_tz)
            date_str = pub_datetime_madrid.strftime("%d/%m/%Y %H:%M")

            if send_telegram_message(neighborhood, title, link, date_str):
                history.append(guid)
                seen_in_this_run.add(guid)
                noticias_enviadas += 1
                # Pausa base entre mensajes normales para no forzar
                time.sleep(3) 

    if len(history) > initial_history_count:
        print(f"\nGuardando historial actualizado ({len(history)} entradas)...")
        save_history(history)
    else:
        print("\nNo hay noticias nuevas para guardar.")

    print(f"--- Fin. Noticias enviadas hoy: {noticias_enviadas} ---")

if _name_ == "_main_":
    main()
