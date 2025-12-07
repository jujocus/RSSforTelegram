import feedparser
import requests
import os
from datetime import datetime
import pytz
import time

# Aquí puedes modificar la palabra clave para poner lo que desees: eg. madrid, o Villaverde
RSS_URL = "https://news.google.com/rss/search?q=carabanchel+when:1d&hl=es&gl=ES&ceid=ES:es&ned=es&nocache=1"

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Ventana configurable: por defecto 24 horas (para pillar noticias de ayer noche)
MAX_HOURS = int(os.environ.get("NEWS_MAX_HOURS", "24"))

def send_telegram_message(title, link, date_str):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERROR: Faltan tokens de Telegram.")
        return

    # Escapamos caracteres especiales de Markdown si fuera necesario, 
    # pero para simplificar usamos HTML o Markdown simple.
    msg = f"🗞 **Noticia Carabanchel**\n\n{title}\n📅 {date_str}\n🔗 {link}"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        r = requests.post(url, json=data, timeout=15)
        if r.status_code == 200:
            print(f" -> [Telegram] Mensaje enviado: {title}")
        else:
            print(f" -> [Telegram] Error ({r.status_code}): {r.text}")
    except Exception as e:
        print(f" -> [Telegram] Excepción: {e}")

def main():
    print("--- Iniciando Bot de Noticias Carabanchel ---")
    
    # Parsear el feed
    feed = feedparser.parse(RSS_URL)
    
    # Configurar zonas horarias
    madrid_tz = pytz.timezone('Europe/Madrid')
    now_madrid = datetime.now(madrid_tz)
    
    print(f"Ahora (Madrid): {now_madrid.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Buscando noticias de las últimas {MAX_HOURS} horas.")

    noticias_enviadas = 0
    noticias_totales = len(feed.entries)
    print(f"Entradas totales en el RSS: {noticias_totales}")

    # Recorremos las noticias con un bucle for, pero creo que hay alguna manera más limpia
    for entry in feed.entries:
        title = entry.get("title", "<sin título>")
        link = entry.get("link", "")
        
        try:
            # Obtener fecha de publicación
            published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            
            if not published_struct:
                # Si no hay fecha, saltamos para evitar errores
                continue

            # Convertir a datetime con zona horaria UTC y luego a Madrid
            pub_datetime_utc = datetime(*published_struct[:6], tzinfo=pytz.utc)
            pub_datetime_madrid = pub_datetime_utc.astimezone(madrid_tz)
            
            # Calcular antigüedad en horas
            age_hours = (now_madrid - pub_datetime_madrid).total_seconds() / 3600
            
            # Si la noticia tiene menos horas que el máximo permitido (ej. 24h), se envía
            if 0 <= age_hours <= MAX_HOURS:
                print(f"✅ ACEPTADA (Hace {age_hours:.2f} h): {title}")
                
                send_telegram_message(
                    title, 
                    link, 
                    pub_datetime_madrid.strftime("%d/%m/%Y %H:%M")
                )
                noticias_enviadas += 1
                time.sleep(1) # Pequeña pausa para no saturar la API
            else:
                # Opcional: imprimir las descartadas para depurar (no se envían)
                # print(f"❌ DESCARTADA (Hace {age_hours:.2f} h): {title}")
                pass

        except Exception as e:
            print(f"Error procesando entrada '{title}': {e}")

    print(f"--- Fin. Noticias enviadas: {noticias_enviadas} ---")

if __name__ == "__main__":
    main()
