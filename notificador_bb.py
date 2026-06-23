import time
import requests
import os
import json
import threading
from flask import Flask
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= CONFIGURACIÓN =================
# Telegram
TOKEN = "8614770021:AAF_wXat8I3QY5bwVxEYEvkHXQFI8mCIMNQ"
CHAT_ID = "8742496234"

# Servidor Web Falso para Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Blackboard activo y funcionando 24/7."

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Blackboard
URL_STREAM = "https://senati.blackboard.com/ultra/stream"
TIEMPO_REVISION = 300  # Revisar cada 5 minutos (300 segundos)

# Palabras clave a buscar
PALABRAS_CLAVE = ["URGENTE", "EXAMEN", "FINAL", "ENTREGABLE", "EVALUACIÓN", "EVALUACION", "TAREA"]
# =================================================

def enviar_alerta_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def iniciar_navegador():
    print("Iniciando navegador automatizado en modo NUBE...")
    options = webdriver.ChromeOptions()
    
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def revisar_anuncios_blackboard():
    driver = iniciar_navegador()
    anuncios_enviados = set() # Memoria para no enviar duplicados
    
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Preparando conexión con Blackboard...")
        # Ir al dominio principal para inyectar cookies
        driver.get("https://senati.blackboard.com")
        
        try:
            with open("cookies.json", "r") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    # Selenium requiere que el dominio de la cookie coincida con el dominio actual
                    if 'domain' in cookie and 'blackboard.com' in cookie['domain']:
                        driver.add_cookie(cookie)
            print("✅ Cookies inyectadas correctamente. Ya no se necesita iniciar sesión.")
        except Exception as e:
            print(f"⚠️ Error al cargar cookies.json: {e}")
            
        print("Navegando al Flujo de Actividades...")
        driver.get(URL_STREAM)
        
        print("\n⏳ Esperando a que cargue el Flujo de Actividades...")
        
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'stream-item') or contains(text(), 'Flujo de actividades')]"))
            )
            print("✅ ¡Página principal detectada! Iniciando bucle de monitoreo invisible...")
        except:
            print("⚠️ No se detectó la página completa rápidamente. Continuamos de todos modos...")
        
        print("\nEl bot está en funcionamiento en MODO NUBE (Invisible). Se revisará la página cada 5 minutos.")
        
        while True:
            hora_actual = datetime.now().strftime('%H:%M:%S')
            
            # Recargar la página para ver anuncios nuevos
            driver.refresh()
            time.sleep(10) # Esperar a que la página cargue los datos (SPA - React/Angular)
            
            # El script busca elementos que contengan texto.
            # En el Activity Stream de BB Ultra, los textos importantes suelen estar en elementos concretos
            elementos = driver.find_elements(By.XPATH, "//*[contains(@class, 'stream-item-content') or contains(@class, 'title') or contains(@class, 'description')]")
            
            # Fallback por si las clases cambian: extraer el texto de todo el body
            texto_pantalla = driver.find_element(By.TAG_NAME, "body").text.upper()
            
            anuncios_detectados = []
            
            # Opción 1: Buscamos en elementos individuales para extraer el contexto
            if elementos:
                for elem in elementos:
                    texto_elem = elem.text.strip()
                    texto_upper = texto_elem.upper()
                    
                    if texto_upper and any(palabra in texto_upper for palabra in PALABRAS_CLAVE):
                        if texto_upper not in anuncios_enviados:
                            anuncios_detectados.append(texto_elem)
                            anuncios_enviados.add(texto_upper)
            
            # Si detectó algo, enviamos
            if anuncios_detectados:
                for anuncio in anuncios_detectados:
                    print(f"[{hora_actual}] 🚨 ¡Alerta enviada!: {anuncio[:50]}...")
                    alerta_texto = (
                        f"🚨 *¡ALERTA DE SUMA IMPORTANCIA!* 🚨\n\n"
                        f"📖 *Aviso detectado en Blackboard:*\n"
                        f"📌 *Detalle:* {anuncio}\n\n"
                        f"❌ *Estado:* PENDIENTE DE REVISIÓN\n"
                        f"⚠️ Taylor, esta actividad o anuncio podría ser crítico para tu promedio. ¡Entra ya a la plataforma!"
                    )
                    enviar_alerta_telegram(alerta_texto)
            else:
                print(f"[{hora_actual}] Revisión completada. Todo en orden. Próxima revisión en {TIEMPO_REVISION // 60} minutos.")
                
            # Mantener el tamaño de la memoria controlado
            if len(anuncios_enviados) > 100:
                anuncios_enviados.clear()
            
            # Esperar hasta la próxima revisión
            time.sleep(TIEMPO_REVISION)
            
    except KeyboardInterrupt:
        print("\nBot detenido manualmente por el usuario.")
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
    finally:
        print("Cerrando navegador.")
        driver.quit()

if __name__ == "__main__":
    # Iniciar servidor Flask en un hilo separado para que Render apruebe el despliegue
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Iniciar el bot principal
    revisar_anuncios_blackboard()