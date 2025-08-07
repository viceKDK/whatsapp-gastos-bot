"""
WhatsApp Selenium Integration

Implementación real del conector WhatsApp usando Selenium WebDriver.
Automatiza WhatsApp Web para leer mensajes de un chat específico.
"""

import time
import re
import subprocess
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

from shared.logger import get_logger


class WhatsAppSeleniumConnector:
    """
    Conector de WhatsApp Web usando Selenium WebDriver.
    
    Funcionalidades:
    - Conexión automatizada a WhatsApp Web
    - Detección y selección de chat específico
    - Lectura de mensajes nuevos
    - Manejo de errores y reconexión automática
    """
    
    def __init__(self, config):
        """
        Inicializa el conector WhatsApp.
        
        Args:
            config: Configuración de WhatsApp desde settings
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.driver = None
        self.connected = False
        self.chat_selected = False
        self.last_message_time = None  # Inicializar timestamp del último mensaje
        self.cached_selector = None  # Cachear el selector exitoso

        # === PERFIL DEDICADO DEL BOT ===
        self.user_data_dir = self._get_user_data_dir()

        # Configuración de Selenium
        self.chrome_options = self._setup_chrome_options()
        
    def _get_user_data_dir(self) -> Path:
        """
        Devuelve el directorio de perfil a usar. Crea la carpeta si no existe.
        Lee de config.chrome_user_data_dir o usa C:\\Chrome\\WABot por defecto.
        """
        try:
            base = getattr(self.config, "chrome_user_data_dir", r"C:\Chrome\WABot")
        except Exception:
            base = r"C:\Chrome\WABot"
        p = Path(base)
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"No se pudo crear el directorio de perfil {p}: {e}")
        return p
        
    def connect(self) -> bool:
        """
        Conecta a WhatsApp Web y selecciona el chat objetivo.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            self.logger.info("🚀 === INICIANDO CONEXIÓN A WHATSAPP WEB ===")
            
            # Paso 1: Inicializar driver usando método de debugging (más confiable)
            self.logger.info("📋 PASO 1: Inicializando Chrome con método de debugging...")
            
            # Lanzar Chrome con debugging
            if not self._launch_chrome_with_debugging(port=9222):
                self.logger.error("❌ No se pudo lanzar Chrome con debugging")
                return False
                
            # Adjuntarse al Chrome con debugging
            if not self._attach_to_running_chrome(port=9222):
                self.logger.error("❌ No se pudo adjuntar a Chrome con debugging")
                return False
                
            self.logger.info("✅ PASO 1 COMPLETADO: Chrome listo")
            
            # Paso 2: Verificar navegación a WhatsApp Web
            self.logger.info("📋 PASO 2: Verificando navegación a WhatsApp Web...")
            current_url = self.driver.current_url
            self.logger.info(f"📍 URL actual: {current_url}")
            
            if "whatsapp.com" not in current_url.lower():
                self.logger.info("🌐 Navegando a WhatsApp Web...")
                if not self._navigate_to_whatsapp():
                    self.logger.error("❌ FALLO EN PASO 2: No se pudo navegar a WhatsApp")
                    return False
            self.logger.info("✅ PASO 2 COMPLETADO: En WhatsApp Web")
            
            # Paso 3: Esperar código QR y login
            self.logger.info("📋 PASO 3: Esperando login de usuario...")
            if not self._wait_for_login():
                self.logger.error("❌ FALLO EN PASO 3: Usuario no hizo login")
                return False
            self.logger.info("✅ PASO 3 COMPLETADO: Usuario logueado")
            
            # Paso 4: Seleccionar chat objetivo
            self.logger.info("📋 PASO 4: Seleccionando chat objetivo...")
            if not self._select_target_chat():
                self.logger.error("❌ FALLO EN PASO 4: No se pudo seleccionar chat")
                return False
            self.logger.info("✅ PASO 4 COMPLETADO: Chat seleccionado")
            
            self.connected = True
            self.logger.info("🎉 === CONEXIÓN A WHATSAPP WEB EXITOSA ===")
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERROR GENERAL en connect(): {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            self._cleanup_driver()
            return False
    
    def disconnect(self) -> None:
        """Desconecta y limpia recursos."""
        self.logger.info("Desconectando de WhatsApp Web...")
        self.connected = False
        self.chat_selected = False
        self.cached_selector = None  # Resetear cache al desconectar
        self._cleanup_driver()
    
    def get_new_messages(self) -> List[Tuple[str, datetime]]:
        """
        Obtiene mensajes nuevos del chat seleccionado con detección en tiempo real.
        
        Returns:
            Lista de tuplas (mensaje_texto, fecha_mensaje)
        """
        if not self.connected or not self.chat_selected:
            self.logger.warning("❌ ESTADO: WhatsApp no conectado o chat no seleccionado")
            self.logger.warning(f"   Connected: {self.connected}, Chat selected: {self.chat_selected}")
            return []
        
        try:
            self.logger.info("🔍 INICIANDO BÚSQUEDA DE MENSAJES NUEVOS...")
            self.logger.info(f"📊 Estado inicial - Último mensaje: {self.last_message_time}")
            messages = []
            
            # Obtener elementos de mensajes
            self.logger.info("🎯 PASO 1: Obteniendo elementos de mensajes...")
            message_elements = self._get_message_elements()
            
            if not message_elements:
                self.logger.error("🚨 PASO 1 FALLIDO: No se encontraron elementos de mensaje")
                return []
            
            self.logger.info(f"✅ PASO 1 EXITOSO: {len(message_elements)} elementos de mensaje encontrados")
            
            # Procesar cada mensaje
            self.logger.info("🎯 PASO 2: Procesando elementos de mensajes...")
            new_messages_count = 0
            
            for i, element in enumerate(message_elements):
                try:
                    self.logger.info(f"🔸 PROCESANDO ELEMENTO {i+1}/{len(message_elements)}...")
                    
                    message_data = self._parse_message_element(element)
                    if message_data:
                        message_text, message_time = message_data
                        self.logger.info(f"✅ ELEMENTO {i+1} PARSEADO: '{message_text[:50]}...' (Tiempo: {message_time.strftime('%H:%M:%S')})")
                        
                        # Verificar si es mensaje nuevo
                        is_new = self._is_new_message(message_time)
                        self.logger.info(f"   🔍 ¿Es nuevo?: {is_new} (último conocido: {self.last_message_time})")
                        
                        if is_new:
                            messages.append(message_data)
                            new_messages_count += 1
                            self.logger.info(f"🎉 NUEVO MENSAJE #{new_messages_count} AGREGADO!")
                        else:
                            self.logger.info(f"   ⏸️ Mensaje ya conocido, ignorado")
                    else:
                        self.logger.warning(f"❌ ELEMENTO {i+1} NO SE PUDO PARSEAR (devolvió None)")
                        
                except Exception as e:
                    self.logger.error(f"❌ ERROR procesando elemento {i+1}: {e}")
                    continue
            
            self.logger.info("🎯 PASO 3: Finalizando procesamiento...")
            
            if messages:
                # Actualizar timestamp del último mensaje
                self.last_message_time = max(msg[1] for msg in messages)
                self.logger.info(f"🎉 ÉXITO! {len(messages)} MENSAJES NUEVOS PROCESADOS")
                self.logger.info(f"📅 Último timestamp actualizado: {self.last_message_time.strftime('%H:%M:%S')}")
                
                # Mostrar resumen de mensajes nuevos
                for i, (text, time) in enumerate(messages):
                    self.logger.info(f"   📩 Mensaje #{i+1}: '{text[:100]}...' ({time.strftime('%H:%M:%S')})")
            else:
                self.logger.info("ℹ️ RESULTADO: No hay mensajes nuevos")
                if message_elements:
                    self.logger.info(f"   📊 Se procesaron {len(message_elements)} elementos pero ninguno era nuevo")
                    
                    # Si es la primera vez, inicializar last_message_time con el mensaje más reciente
                    if self.last_message_time is None and message_elements:
                        try:
                            # Obtener el timestamp del último mensaje existente para futuros filtros
                            latest_element = message_elements[-1]
                            latest_message_data = self._parse_message_element(latest_element)
                            if latest_message_data:
                                self.last_message_time = latest_message_data[1]
                                self.logger.info(f"🕐 Inicializando último timestamp: {self.last_message_time.strftime('%H:%M:%S')}")
                        except Exception as e:
                            self.logger.warning(f"⚠️ No se pudo inicializar timestamp: {e}")
                            self.last_message_time = datetime.now()
            
            self.logger.info(f"🏁 BÚSQUEDA COMPLETADA - Retornando {len(messages)} mensajes")
            return messages
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo mensajes: {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            
            # Intentar reconectar si hay problemas
            if not self._verify_connection():
                self.logger.warning("Conexión perdida, intentando reconectar...")
                self.connected = False
                self.chat_selected = False
            return []
    
    def wait_for_new_message(self, timeout_seconds: int = 30) -> List[Tuple[str, datetime]]:
        """
        Espera activamente por nuevos mensajes usando WebDriverWait.
        
        Args:
            timeout_seconds: Tiempo máximo a esperar por un mensaje nuevo
            
        Returns:
            Lista de tuplas (mensaje_texto, fecha_mensaje) de mensajes nuevos
        """
        if not self.connected or not self.chat_selected:
            self.logger.warning("WhatsApp no conectado o chat no seleccionado")
            return []
        
        try:
            # Contar mensajes actuales como baseline
            initial_message_elements = self._get_message_elements()
            initial_count = len(initial_message_elements) if initial_message_elements else 0
            
            self.logger.info(f"⏳ Esperando nuevos mensajes... (actual: {initial_count} mensajes, timeout: {timeout_seconds}s)")
            
            # Esperar a que aparezcan nuevos mensajes
            wait = WebDriverWait(self.driver, timeout_seconds)
            
            def check_for_new_messages(driver):
                """Función para detectar si llegaron mensajes nuevos."""
                try:
                    current_elements = self._get_message_elements()
                    current_count = len(current_elements) if current_elements else 0
                    
                    if current_count > initial_count:
                        self.logger.info(f"🆕 NUEVO MENSAJE DETECTADO! Mensajes: {initial_count} → {current_count}")
                        return True
                    
                    # Verificar también por cambios en el último mensaje
                    if current_elements and initial_message_elements:
                        try:
                            # Comparar el último mensaje
                            last_current = self._parse_message_element(current_elements[-1])
                            last_initial = self._parse_message_element(initial_message_elements[-1])
                            
                            if last_current and last_initial:
                                if last_current[1] > last_initial[1]:  # Comparar timestamps
                                    self.logger.info(f"🕐 MENSAJE ACTUALIZADO DETECTADO! Nuevo timestamp: {last_current[1]}")
                                    return True
                        except:
                            pass
                    
                    return False
                except Exception as e:
                    self.logger.debug(f"Error verificando mensajes: {e}")
                    return False
            
            # Esperar por cambios
            wait.until(check_for_new_messages)
            
            # Obtener los mensajes nuevos
            self.logger.info("🔍 Obteniendo mensajes nuevos después de detectar cambios...")
            new_messages = self.get_new_messages()
            
            if new_messages:
                self.logger.info(f"✅ DETECCIÓN COMPLETADA: {len(new_messages)} mensajes nuevos encontrados")
                for i, (msg_text, msg_time) in enumerate(new_messages):
                    self.logger.info(f"📩 MENSAJE NUEVO #{i+1}: '{msg_text}' (Tiempo: {msg_time.strftime('%H:%M:%S')})")
            else:
                self.logger.warning("⚠️ PROBLEMA: Se detectaron cambios pero get_new_messages() devolvió lista vacía")
                # Intentar un enfoque más directo
                self.logger.info("🔧 Intentando enfoque alternativo para obtener mensajes...")
                current_elements = self._get_message_elements()
                self.logger.info(f"📱 Elementos actuales encontrados: {len(current_elements)}")
            
            return new_messages
            
        except TimeoutException:
            self.logger.debug(f"⏰ Timeout después de {timeout_seconds}s - No llegaron mensajes nuevos")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error esperando mensajes: {e}")
            return []
    
    def _setup_chrome_options(self) -> Options:
        """Configura opciones de Chrome para WhatsApp Web usando perfil dedicado."""
        options = Options()

        # Headless solo si ya tenés la sesión guardada (no recomendado para el primer login)
        if getattr(self.config, "chrome_headless", False):
            # headless "nuevo" evita algunos problemas
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-allow-origins=*")

        # === PERFIL DEL BOT (NO el Default) ===
        # MUY IMPORTANTE: NO agregar --profile-directory cuando se usa un user-data-dir exclusivo
        options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # Cosas menores de automatización
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        return options
    
    def _attach_to_running_chrome(self, port: int = 9222) -> bool:
        """Intenta adjuntarse a un Chrome ya corriendo con remote debugging."""
        try:
            self.logger.info(f"🔌 Intentando adjuntarse a Chrome en puerto {port}...")
            
            # Verificar si hay Chrome con debugging disponible
            import requests
            try:
                response = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=3)
                if response.status_code == 200:
                    self.logger.info(f"✅ Chrome detectado en puerto {port}")
                    version_info = response.json()
                    self.logger.info(f"🌐 Versión: {version_info.get('Browser', 'Unknown')}")
                else:
                    return False
            except:
                self.logger.info(f"❌ No hay Chrome en puerto {port}")
                return False
            
            # Obtener pestañas disponibles
            try:
                tabs_response = requests.get(f"http://127.0.0.1:{port}/json", timeout=3)
                if tabs_response.status_code == 200:
                    tabs = tabs_response.json()
                    self.logger.info(f"📂 Pestañas encontradas: {len(tabs)}")
                    
                    # Buscar pestaña de WhatsApp existente
                    whatsapp_tab = None
                    for tab in tabs:
                        url = tab.get('url', '').lower()
                        title = tab.get('title', '').lower()
                        self.logger.info(f"  - 📄 {title}: {url}")
                        if 'whatsapp.com' in url:
                            whatsapp_tab = tab
                            self.logger.info(f"✅ Pestaña WhatsApp encontrada!")
                            break
                    
                    if whatsapp_tab:
                        self.logger.info("🎯 Conectando a pestaña WhatsApp existente...")
                    else:
                        self.logger.info("📝 No hay pestaña WhatsApp, se creará una nueva")
            except Exception as e:
                self.logger.warning(f"⚠️ Error obteniendo pestañas: {e}")
            
            # Crear opciones minimalistas para adjuntar
            opts = Options()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            
            self.driver = webdriver.Chrome(options=opts)
            self.driver.implicitly_wait(2)  # Reducir timeout para detectar desconexiones más rápido
            
            # Verificar que estamos conectados
            current_url = self.driver.current_url
            self.logger.info(f"📍 Conectado! URL actual: {current_url}")
            
            # Si no está en WhatsApp, buscar pestaña existente o crear nueva
            if "whatsapp.com" not in current_url.lower():
                self.logger.info("🔍 Buscando pestaña de WhatsApp...")
                
                # Intentar cambiar a una pestaña existente de WhatsApp
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    if "whatsapp.com" in self.driver.current_url.lower():
                        self.logger.info(f"✅ Cambiado a pestaña WhatsApp existente: {self.driver.current_url}")
                        return True
                
                # Si no hay pestaña de WhatsApp, navegar en la pestaña actual
                self.logger.info("🌐 Navegando a WhatsApp Web en pestaña actual...")
                self.driver.get("https://web.whatsapp.com")
                time.sleep(3)
                self.logger.info(f"📍 Nueva URL: {self.driver.current_url}")
            
            self.logger.info("✅ Adjuntado exitosamente a Chrome existente!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error adjuntándose a Chrome: {e}")
            return False

    def _launch_chrome_with_debugging(self, port: int = 9222) -> bool:
        """Lanza Chrome con remote debugging usando el perfil predeterminado."""
        try:
            self.logger.info(f"🚀 Lanzando Chrome COMO PROCESO DUEÑO del perfil con debugging...")
            
            import subprocess
            import time
            
            # Cerrar Chrome existente y limpiar locks
            self._close_existing_chrome()
            
            # Verificar que el puerto esté libre
            self.logger.info(f"🔍 Verificando que puerto {port} esté libre...")
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            if f":{port}" in result.stdout:
                self.logger.warning(f"⚠️ Puerto {port} ya está en uso, intentando liberar...")
                time.sleep(2)
            
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            profile_path = self.user_data_dir  # PERFIL DEL BOT

            cmd = [
                chrome_path,
                "--remote-debugging-address=127.0.0.1",
                f"--remote-debugging-port={port}",
                f"--user-data-dir={profile_path}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-mode",
                "https://web.whatsapp.com",
            ]
            
            self.logger.info(f"📋 Comando mejorado:")
            for arg in cmd:
                self.logger.info(f"  {arg}")
            
            # Lanzar Chrome como proceso principal (no background)
            self.chrome_process = subprocess.Popen(cmd, 
                                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Esperar que Chrome se inicie y verificar debugging
            self.logger.info("⏳ Esperando que Chrome HABILITE remote debugging...")
            max_wait = 15  # Reducido para ser más rápido
            
            for i in range(max_wait):
                try:
                    # Verificación de puerto con netstat primero
                    if i % 3 == 0:  # Cada 3 intentos
                        netstat_result = subprocess.run(["netstat", "-ano"], 
                                                       capture_output=True, text=True)
                        listening_ports = [line for line in netstat_result.stdout.split('\n') 
                                         if 'LISTENING' in line and f':{port}' in line]
                        
                        if listening_ports:
                            self.logger.info(f"🎯 Puerto {port} detectado en LISTENING:")
                            for line in listening_ports:
                                self.logger.info(f"  {line.strip()}")
                        else:
                            self.logger.info(f"⏳ Puerto {port} aún no está en LISTENING...")
                    
                    # Verificación HTTP
                    import requests
                    self.logger.info(f"🔍 Intento {i+1}/{max_wait}: HTTP check puerto {port}...")
                    
                    # Intentar con localhost también por si acaso
                    for host in ['127.0.0.1', 'localhost']:
                        try:
                            response = requests.get(f"http://{host}:{port}/json/version", timeout=1)
                            if response.status_code == 200:
                                version_info = response.json()
                                self.logger.info(f"✅ Chrome debugging activo en {host}:{port}!")
                                self.logger.info(f"🌐 Versión: {version_info.get('Browser', 'Unknown')}")
                                self.logger.info(f"⏱️ Listo después de {i+1} segundos")
                                return True
                        except:
                            continue
                            
                except requests.exceptions.ConnectionError:
                    pass
                except Exception as e:
                    self.logger.warning(f"❌ Error verificando: {e}")
                
                time.sleep(1)
            
            # Diagnóstico completo si falla
            self.logger.error(f"💥 Chrome debugging NO SE ACTIVÓ después de {max_wait} segundos")
            
            # Verificar procesos Chrome
            import psutil
            chrome_processes = []
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'chrome' in p.info['name'].lower():
                    chrome_processes.append(p)
            
            self.logger.info(f"🔍 Procesos Chrome activos: {len(chrome_processes)}")
            for proc in chrome_processes:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else 'N/A'
                has_debug = '--remote-debugging-port' in cmdline
                self.logger.info(f"  - PID {proc.info['pid']}: {proc.info['name']} | Debug: {'✅' if has_debug else '❌'}")
                if has_debug:
                    self.logger.info(f"    CMD: ...{cmdline[-100:]}")  # Últimos 100 chars
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error lanzando Chrome: {e}")
            return False


    
    def _close_existing_chrome(self):
        """Cierra cualquier instancia de Chrome existente y limpia locks."""
        try:
            import subprocess
            import time
            import os
            
            self.logger.info("🔄 Cerrando todas las instancias de Chrome...")
            
            # Cerrar Chrome usando taskkill con Tree para procesos hijo
            result = subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                self.logger.info("✅ Chrome cerrado exitosamente")
            else:
                self.logger.info("ℹ️ No había instancias de Chrome corriendo")
            
            # Esperar que se cierren completamente
            time.sleep(3)
            
            # Limpiar locks del perfil
            self.logger.info("🧹 Limpiando locks del perfil...")
            profile_dir = Path.home() / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data'
            
            # Eliminar archivos Singleton que pueden causar problemas
            singleton_patterns = ['Singleton*', 'SingletonSocket', 'SingletonLock', 'SingletonCookie']
            for pattern in singleton_patterns:
                for lock_file in profile_dir.glob(pattern):
                    try:
                        lock_file.unlink(missing_ok=True)
                        self.logger.info(f"🗑️ Eliminado: {lock_file.name}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ No se pudo eliminar {lock_file}: {e}")
            
            self.logger.info("✅ Limpieza de Chrome completada")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en limpieza de Chrome: {e}")
    
    def _navigate_to_whatsapp(self) -> bool:
        """Navega a WhatsApp Web."""
        try:
            self.logger.info("Navegando a WhatsApp Web...")
            
            # Usar execute_script en lugar de get para mejor control
            self.driver.execute_script("window.location.href = 'https://web.whatsapp.com';")
            
            # Esperar a que cargue completamente
            wait = WebDriverWait(self.driver, 30)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error navegando a WhatsApp: {e}")
            return False
    
    def _wait_for_login(self) -> bool:
        """Espera a que el usuario haga login con código QR."""
        try:
            self.logger.info("Esperando login de usuario...")
            
            # Timeout más largo para login
            wait = WebDriverWait(self.driver, 120)  # 2 minutos
            
            # Verificar si ya está logueado
            self.logger.info("🔍 Verificando estado actual de WhatsApp Web...")
            
            try:
                # Primero verificar si ya está logueado (sin QR)
                chat_list = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list']")
                if chat_list:
                    self.logger.info("✅ Ya está logueado - encontrada lista de chats")
                    return True
            except NoSuchElementException:
                pass
                
            try:
                # Si hay QR, informar al usuario
                qr_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='qr-code'], canvas[aria-label*='QR']")
                if qr_element:
                    self.logger.info("📱 QR encontrado - escanea el código QR para continuar...")
                    print("📱 Escanea el código QR en WhatsApp Web para continuar...")
                    
            except NoSuchElementException:
                self.logger.info("🔍 No se encontró QR - quizás ya está cargando...")
                
            # Esperar múltiples indicadores de login exitoso
            login_indicators = [
                "[data-testid='chat-list']",
                "[data-testid='side']",
                "div[data-testid='app']",
                "#pane-side",
                "div._3OvU8"  # Selector alternativo para la barra lateral
            ]
            
            self.logger.info(f"⏳ Esperando login (timeout: 120s)...")
            
            for attempt in range(120):  # Verificar cada segundo
                for selector in login_indicators:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element and element.is_displayed():
                            self.logger.info(f"✅ Login exitoso detectado con selector: {selector}")
                            time.sleep(3)  # Dar tiempo extra para que cargue
                            return True
                    except NoSuchElementException:
                        continue
                
                # Log de progreso cada 10 segundos
                if attempt % 10 == 0 and attempt > 0:
                    self.logger.info(f"⏳ Esperando login... ({attempt}/120 segundos)")
                    
                    # Debug: mostrar elementos actuales
                    try:
                        page_source = self.driver.page_source
                        if "qr-code" in page_source.lower():
                            self.logger.debug("🔍 QR aún presente")
                        if "loading" in page_source.lower():
                            self.logger.debug("🔍 Página cargando...")
                    except:
                        pass
                        
                time.sleep(1)
            
            self.logger.error("❌ Timeout esperando login después de 120 segundos")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error en login: {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            return False
    
    def _select_target_chat(self) -> bool:
        """Selecciona el chat objetivo configurado."""
        try:
            self.logger.info(f"Buscando chat: {self.config.target_chat_name}")
            
            # Buscar el chat en la lista
            chat_element = self._find_chat_by_name(self.config.target_chat_name)
            
            if not chat_element:
                self.logger.error(f"No se encontró el chat: {self.config.target_chat_name}")
                return False
            
            # Hacer click en el chat con scroll si es necesario
            try:
                self.logger.info("📱 Haciendo click en el chat...")
                
                # Asegurar que el elemento está visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", chat_element)
                time.sleep(1)
                
                # Intentar click normal primero
                chat_element.click()
                self.logger.info("✅ Click realizado")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Click normal falló, intentando JavaScript: {e}")
                # Fallback: usar JavaScript
                self.driver.execute_script("arguments[0].click();", chat_element)
            
            # Esperar más tiempo para que cargue el chat
            self.logger.info("⏳ Esperando que cargue el chat...")
            time.sleep(5)  # Tiempo aumentado
            
            # Verificar múltiples veces con pausa
            max_attempts = 3
            for attempt in range(max_attempts):
                self.logger.info(f"🔍 Verificación de chat seleccionado (intento {attempt + 1}/{max_attempts})...")
                
                if self._verify_chat_selected():
                    self.chat_selected = True
                    self.logger.info(f"✅ Chat seleccionado exitosamente: {self.config.target_chat_name}")
                    return True
                
                if attempt < max_attempts - 1:  # No esperar en el último intento
                    self.logger.info("⏳ Esperando antes del siguiente intento...")
                    time.sleep(3)
            
            self.logger.error("❌ No se pudo verificar la selección del chat después de múltiples intentos")
            return False
            
        except Exception as e:
            self.logger.error(f"Error seleccionando chat: {e}")
            return False
    
    def _find_chat_by_name(self, chat_name: str) -> Optional[object]:
        """Busca un chat por nombre en la lista de chats."""
        try:
            # Selectores alternativos para la lista de chats
            chat_list_selectors = [
                "[data-testid='chat-list']",
                "#pane-side",
                "div[data-testid='side']",
                "div._3OvU8",  # Selector clásico
                "div[role='application'] > div > div",  # Selector genérico
                "div._2_1wd",  # Otro selector posible
                "#side"
            ]
            
            self.logger.info("🔍 Esperando que cargue la interfaz de chats...")
            
            # Intentar con múltiples selectores
            chat_list_found = False
            for selector in chat_list_selectors:
                try:
                    wait = WebDriverWait(self.driver, 5)  # Timeout corto por selector
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    self.logger.info(f"✅ Lista de chats encontrada con: {selector}")
                    chat_list_found = True
                    break
                except:
                    self.logger.debug(f"Selector {selector} no funcionó")
                    continue
            
            if not chat_list_found:
                self.logger.warning("⚠️ No se encontró lista de chats con selectores conocidos, continuando...")
            
            # Dar tiempo para que carguen los chats
            self.logger.info("📋 Esperando que carguen los chats...")
            time.sleep(3)
            
            # Múltiples selectores para elementos de chat (más robustos)
            chat_selectors = [
                "[data-testid='cell-frame-container']",
                "[data-testid='chat']", 
                "div[role='listitem']",
                "div._3m_Xw",  # Selector alternativo
                "div[data-testid='conversation-info-header']",
                "div[aria-label]",  # Elementos con aria-label
                "div[title]",       # Elementos con title
                "span[title]",      # Spans con title (nombres de chat)
                "div._2nY6U",       # Otro selector clásico
                "div > div > div[tabindex='0']",  # Elementos clickeables
                "div[role='button']"  # Botones (chats son clickeables)
            ]
            
            chat_elements = []
            for selector in chat_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.logger.info(f"✅ Encontrados {len(elements)} elementos con selector: {selector}")
                        chat_elements = elements
                        break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} no funcionó: {e}")
                    continue
            
            if not chat_elements:
                self.logger.error("❌ No se encontraron elementos de chat con ningún selector")
                return None
            
            self.logger.info(f"🔍 Revisando {len(chat_elements)} chats...")
            found_chats = []
            
            for i, chat_element in enumerate(chat_elements):
                try:
                    self.logger.debug(f"🔍 Procesando elemento {i+1}/{len(chat_elements)} (índice {i})")
                    
                    # Múltiples selectores para el nombre del chat (más completos)
                    name_selectors = [
                        "[data-testid='conversation-info-header']",
                        "[data-testid='conversation-title']", 
                        "span[title]",
                        "div[title]",
                        "span._3ko75",  # Selector alternativo
                        ".ggj6brxn",    # Otro selector posible
                        "span[dir='auto']",  # Texto automático
                        "div[dir='auto']",   # Div con texto automático
                        "span.ggj6brxn",     # Span específico
                        ".zoWT4",            # Selector de nombre
                        "._21nHd",           # Otro selector común
                        "[aria-label]",      # Elementos con aria-label
                        "[role='gridcell'] span",  # Spans dentro de celdas
                    ]
                    
                    chat_text = ""
                    chat_title = ""
                    chat_aria_label = ""
                    
                    # Buscar texto con selectores específicos
                    for name_selector in name_selectors:
                        try:
                            name_element = chat_element.find_element(By.CSS_SELECTOR, name_selector)
                            if name_element:
                                text = name_element.text.strip()
                                title = name_element.get_attribute("title")
                                aria_label = name_element.get_attribute("aria-label")
                                
                                if text:
                                    chat_text = text
                                    break
                                elif title:
                                    chat_title = title
                                elif aria_label:
                                    chat_aria_label = aria_label
                        except NoSuchElementException:
                            continue
                    
                    # Usar title o aria-label si no hay texto
                    if not chat_text:
                        chat_text = chat_title or chat_aria_label
                    
                    # Si aún no hay texto, intentar atributos del elemento principal
                    if not chat_text:
                        chat_text = chat_element.get_attribute("title") or chat_element.get_attribute("aria-label") or ""
                    
                    # Si no encontramos texto con selectores, intentar texto directo
                    if not chat_text:
                        chat_text = chat_element.text.strip()
                    
                    # SIEMPRE procesar el primer chat (índice 0) incluso sin texto
                    if i == 0:
                        self.logger.info(f"  📱 Chat {i+1} (PRIMER CHAT FIJADO): '{chat_text}' [Procesando automáticamente]")
                        found_chats.append(chat_text or f"Chat #{i+1}")
                        
                        # Si contiene "Gastos" o es el primer chat sin texto claro, seleccionarlo
                        if not chat_text or chat_name.lower() in chat_text.lower():
                            self.logger.info(f"🎯 ¡PRIMER CHAT SELECCIONADO! Chat #{i+1}: '{chat_text or 'SIN_TEXTO'}' (CHAT FIJADO)")
                            return chat_element
                    elif chat_text:
                        found_chats.append(chat_text)
                        self.logger.info(f"  📱 Chat {i+1}: '{chat_text}'")
                        
                        # Buscar coincidencia exacta primero
                        if chat_name.lower() == chat_text.lower():
                            self.logger.info(f"🎯 ¡Chat encontrado (coincidencia exacta)! '{chat_text}'")
                            return chat_element
                            
                        # Buscar coincidencia parcial
                        elif chat_name.lower() in chat_text.lower():
                            self.logger.info(f"🎯 ¡Chat encontrado (coincidencia parcial)! '{chat_text}' contiene '{chat_name}'")
                            return chat_element
                    else:
                        self.logger.debug(f"  ❌ Chat {i+1}: Sin texto encontrado")
                        
                except Exception as e:
                    self.logger.debug(f"Error procesando chat {i+1}: {e}")
                    continue
            
            # Mostrar resumen de chats encontrados
            self.logger.error(f"❌ Chat '{chat_name}' no encontrado")
            self.logger.info(f"📱 Chats disponibles ({len(found_chats)}):")
            for chat in found_chats[:10]:  # Mostrar solo los primeros 10
                self.logger.info(f"  - '{chat}'")
            
            if len(found_chats) > 10:
                self.logger.info(f"  ... y {len(found_chats) - 10} chats más")
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error buscando chat: {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            return None
    
    def _verify_chat_selected(self) -> bool:
        """Verifica que un chat está seleccionado y activo."""
        try:
            self.logger.info("🔍 Verificando que el chat se seleccionó correctamente...")
            
            # Múltiples selectores para el área de mensajes/chat activo
            chat_active_selectors = [
                "[data-testid='conversation-panel-messages']",
                "[data-testid='main']",
                "#main",
                "div[data-testid='chat-main']",
                "div._2_1wd",  # Área principal de chat
                "div[role='main']",
                "div[data-tab='1']",  # Pestaña activa
                ".app-wrapper-web",   # Wrapper principal
                "div._3q4NP",         # Contenedor de mensajes
                "footer[data-testid='conversation-compose']",  # Área de escritura
                "[data-testid='compose-box-input']",  # Caja de texto
                "div[contenteditable='true']"  # Área de entrada de texto
            ]
            
            for selector in chat_active_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        self.logger.info(f"✅ Chat activo verificado con selector: {selector}")
                        return True
                except NoSuchElementException:
                    continue
            
            # Verificación adicional: buscar elementos que indican chat activo
            try:
                # Buscar cualquier área de mensajes visible
                message_areas = self.driver.find_elements(By.CSS_SELECTOR, "div[role='application'] div[role='log']")
                if message_areas:
                    self.logger.info(f"✅ Encontradas {len(message_areas)} áreas de mensajes")
                    return True
            except:
                pass
            
            # Verificar si hay elementos de entrada de texto (indica chat activo)
            try:
                input_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[contenteditable], input[type='text']")
                visible_inputs = [elem for elem in input_elements if elem.is_displayed()]
                if visible_inputs:
                    self.logger.info(f"✅ Encontrados {len(visible_inputs)} elementos de entrada visibles")
                    return True
            except:
                pass
            
            self.logger.error("❌ No se pudo verificar que el chat esté seleccionado con ningún selector")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando selección de chat: {e}")
            return False
    
    def _get_message_elements(self) -> List[object]:
        """Obtiene elementos de mensajes del chat actual con múltiples selectores."""
        try:
            self.logger.info("🔍 INICIANDO BÚSQUEDA DE ELEMENTOS DE MENSAJE...")
            
            # Verificar que estamos en un chat válido
            try:
                main_area = self.driver.find_element(By.CSS_SELECTOR, "#main")
                self.logger.info("✅ Área principal encontrada")
            except Exception as e:
                self.logger.error(f"❌ ERROR: No se puede acceder al área principal: {e}")
                return []
            
            # Múltiples selectores para mensajes (ordenados por probabilidad de éxito)
            message_selectors = [
                "div[role='row']",        # ✅ ESTE SIEMPRE FUNCIONA - ponerlo primero
                "[data-testid='msg-container']",
                "[data-testid='message']",
                "div[data-id]",           # Mensajes tienen data-id
                "div._1AOuq",             # Selector clásico de mensaje
                "div._22Msk",             # Otro selector de mensaje
                "div.message-in, div.message-out",  # Mensajes entrantes/salientes
                "div[class*='message']",  # Cualquier div con 'message' en la clase
                "div[class*='_1AOuq']",   # Variaciones del selector
                "[data-pre-plain-text]",  # Atributo de mensajes
            ]
            
            # Intentar primero con el selector cacheado si existe
            messages = []
            if self.cached_selector:
                try:
                    self.logger.debug(f"🚀 USANDO SELECTOR CACHEADO: {self.cached_selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, self.cached_selector)
                    
                    if elements:
                        self.logger.info(f"✅ SELECTOR CACHEADO EXITOSO: {len(elements)} elementos encontrados")
                        messages = elements
                    else:
                        self.logger.warning("⚠️ Selector cacheado falló, probando todos los selectores...")
                        self.cached_selector = None  # Resetear cache
                except Exception as e:
                    self.logger.warning(f"⚠️ Error con selector cacheado: {e}")
                    self.cached_selector = None  # Resetear cache
            
            # Si no hay cache o falló, probar todos los selectores
            if not messages:
                self.logger.info(f"🎯 PROBANDO {len(message_selectors)} SELECTORES DIFERENTES...")
                
                for i, selector in enumerate(message_selectors):
                    try:
                        self.logger.debug(f"🔸 SELECTOR {i+1}/{len(message_selectors)}: {selector}")
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        self.logger.debug(f"📊 RESULTADO: {len(elements)} elementos encontrados")
                        
                        if elements:
                            self.logger.info(f"✅ ÉXITO! Usando {len(elements)} elementos del selector: {selector}")
                            messages = elements
                            
                            # CACHEAR el selector exitoso para próximas veces
                            self.cached_selector = selector
                            self.logger.info(f"💾 SELECTOR CACHEADO: {selector}")
                            
                            # Debug: mostrar info del primer elemento
                            try:
                                first_elem = elements[0]
                                self.logger.debug(f"🔍 PRIMER ELEMENTO - Tag: {first_elem.tag_name}, Clases: {first_elem.get_attribute('class')}")
                            except:
                                pass
                            break
                        else:
                            self.logger.debug(f"❌ SELECTOR VACÍO: {selector}")
                            
                    except Exception as e:
                        self.logger.error(f"❌ SELECTOR FALLÓ: {selector} - Error: {e}")
                        continue
            
            if not messages:
                self.logger.error("🚨 PROBLEMA CRÍTICO: No se encontraron elementos de mensaje con ningún selector")
                
                # Intentar selectores más genéricos
                self.logger.info("🔧 INTENTANDO SELECTORES GENÉRICOS...")
                generic_selectors = [
                    "div[role='application'] div div div",  # Muy genérico
                    "#main div div div",  # Dentro del área principal
                    "div[data-testid='main'] div div",  # Área de mensajes
                    "#main div",  # Más simple
                    "div",  # Ultra genérico
                ]
                
                for i, selector in enumerate(generic_selectors):
                    try:
                        self.logger.info(f"🔸 SELECTOR GENÉRICO {i+1}: {selector}")
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        self.logger.info(f"📊 ELEMENTOS BRUTOS ENCONTRADOS: {len(elements)}")
                        
                        # Filtrar elementos que parecen mensajes
                        potential_messages = []
                        for j, elem in enumerate(elements[:50]):  # Solo revisar los primeros 50
                            try:
                                if self._looks_like_message(elem):
                                    potential_messages.append(elem)
                                    if len(potential_messages) <= 5:  # Solo mostrar los primeros 5
                                        self.logger.info(f"✅ MENSAJE POTENCIAL #{len(potential_messages)}: {elem.tag_name} - {elem.get_attribute('class')[:100]}")
                            except:
                                continue
                        
                        if potential_messages:
                            self.logger.info(f"🎯 ÉXITO CON GENÉRICO! {len(potential_messages)} mensajes potenciales con selector: {selector}")
                            messages = potential_messages
                            break
                        else:
                            self.logger.info(f"❌ GENÉRICO SIN RESULTADOS: {selector}")
                    except Exception as e:
                        self.logger.error(f"❌ SELECTOR GENÉRICO FALLÓ: {selector} - Error: {e}")
                        continue
            
            if not messages:
                self.logger.error("🚨 BÚSQUEDA FALLIDA COMPLETAMENTE: NO SE ENCONTRARON MENSAJES")
                
                # Debug extensivo del DOM
                try:
                    main_area = self.driver.find_element(By.CSS_SELECTOR, "#main")
                    self.logger.error(f"🔍 ÁREA PRINCIPAL HTML (primeros 500 chars): {main_area.get_attribute('outerHTML')[:500]}...")
                    
                    # Intentar obtener screenshot para debug
                    try:
                        screenshot_path = f"debug_no_messages_{int(time.time())}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.logger.error(f"📸 Screenshot guardado: {screenshot_path}")
                    except:
                        pass
                        
                except Exception as e:
                    self.logger.error(f"❌ ERROR ACCEDIENDO AL ÁREA PRINCIPAL: {e}")
                    
                # Verificar URL actual
                try:
                    current_url = self.driver.current_url
                    self.logger.error(f"🌐 URL ACTUAL: {current_url}")
                    if "whatsapp.com" not in current_url:
                        self.logger.error("🚨 PROBLEMA: No estamos en WhatsApp!")
                except:
                    pass
                    
                return []
            
            # Filtrar solo mensajes entrantes (no enviados por nosotros)
            self.logger.info(f"🔍 FILTRANDO {len(messages)} elementos para encontrar mensajes entrantes...")
            incoming_messages = []
            
            for i, msg in enumerate(messages):
                try:
                    self.logger.info(f"🔸 EVALUANDO MENSAJE {i+1}/{len(messages)}...")
                    
                    # Mostrar info del elemento
                    try:
                        elem_class = msg.get_attribute('class') or 'sin-clase'
                        elem_text = msg.text[:100] if msg.text else 'sin-texto'
                        self.logger.info(f"   📋 Clase: {elem_class}")
                        self.logger.info(f"   📝 Texto: {elem_text}...")
                    except:
                        self.logger.info(f"   ❌ No se pudo obtener info del elemento")
                    
                    is_incoming = self._is_incoming_message(msg)
                    self.logger.info(f"   🎯 Es mensaje entrante: {is_incoming}")
                    
                    if is_incoming:
                        incoming_messages.append(msg)
                        self.logger.info(f"✅ MENSAJE ENTRANTE #{len(incoming_messages)} AGREGADO")
                    else:
                        self.logger.info(f"⬅️ Mensaje saliente #{i+1} ignorado")
                        
                except Exception as e:
                    self.logger.error(f"❌ ERROR procesando mensaje #{i+1}: {e}")
                    continue
            
            self.logger.info(f"📊 RESULTADO FINAL: {len(incoming_messages)} mensajes entrantes de {len(messages)} totales")
            
            if not incoming_messages:
                self.logger.error("🚨 PROBLEMA: NO SE ENCONTRARON MENSAJES ENTRANTES!")
                self.logger.error("   💡 Posibles causas:")
                self.logger.error("   - Todos los mensajes son enviados por nosotros")  
                self.logger.error("   - El chat está vacío")
                self.logger.error("   - Los selectores de mensajes están mal")
                self.logger.error("   - La función _is_incoming_message() está fallando")
            
            return incoming_messages
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo mensajes: {e}")
            self.logger.error("Detalles:", exc_info=True)
            return []
    
    def _looks_like_message(self, element) -> bool:
        """Determina si un elemento parece ser un mensaje."""
        try:
            # Verificar si tiene texto
            text = element.text.strip()
            if not text:
                return False
            
            # Verificar si tiene atributos típicos de mensajes
            has_data_id = element.get_attribute("data-id") is not None
            has_message_class = "message" in (element.get_attribute("class") or "").lower()
            has_pre_text = element.get_attribute("data-pre-plain-text") is not None
            
            # Verificar si contiene elementos típicos de mensajes
            has_text_content = len([child for child in element.find_elements(By.CSS_SELECTOR, "*") 
                                   if child.text and len(child.text.strip()) > 0]) > 0
            
            return has_data_id or has_message_class or has_pre_text or (has_text_content and len(text) > 3)
            
        except:
            return False
    
    def _is_incoming_message(self, message_element) -> bool:
        """Determina si un mensaje es entrante (no enviado por nosotros)."""
        try:
            # Los mensajes propios tienen una clase específica
            classes = message_element.get_attribute("class") or ""
            return "message-out" not in classes
            
        except Exception:
            return False
    
    def _parse_message_element(self, element) -> Optional[Tuple[str, datetime]]:
        """
        Extrae texto y timestamp de un elemento de mensaje con múltiples selectores.
        
        Returns:
            Tupla (texto, fecha) o None si no se puede parsear
        """
        try:
            # Verificar que el elemento sigue siendo accesible
            try:
                _ = element.tag_name  # Test básico de accesibilidad
            except Exception as e:
                self.logger.debug(f"Elemento no accesible, posible desconexión: {e}")
                return None
                
            self.logger.debug("🔍 Parseando elemento de mensaje...")
            
            # Múltiples selectores para el texto del mensaje
            text_selectors = [
                "[data-testid='conversation-text']",
                ".selectable-text",
                "span.selectable-text",
                "div.selectable-text", 
                "[data-testid='msg-text']",
                ".copyable-text",
                "span[dir='ltr']",
                "span[dir='auto']",
                "div[dir='ltr']",
                "div[dir='auto']",
                ".message-text",
                ".quoted-mention",
                "._11JPr",  # Selector clásico
                "._12pGw",  # Otro selector común
            ]
            
            message_text = ""
            for selector in text_selectors:
                try:
                    text_element = element.find_element(By.CSS_SELECTOR, selector)
                    if text_element:
                        text = text_element.text.strip()
                        if text:
                            message_text = text
                            self.logger.debug(f"✅ Texto extraído con selector: {selector}")
                            break
                except:
                    continue
            
            # Si no encontró texto con selectores específicos, usar texto del elemento completo
            if not message_text:
                full_text = element.text.strip()
                if full_text:
                    # Filtrar solo texto del mensaje (evitar metadata)
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    if lines:
                        # Tomar la línea más larga como mensaje principal
                        message_text = max(lines, key=len)
                        self.logger.debug(f"✅ Texto extraído del elemento completo: '{message_text[:50]}...'")
            
            if not message_text:
                self.logger.debug("❌ No se pudo extraer texto del mensaje")
                return None
            
            # Múltiples selectores para timestamp
            time_selectors = [
                "[data-testid='msg-meta']",
                ".message-meta",
                "span[data-testid='msg-time']",
                "span[title]",  # Timestamps suelen estar en title
                ".copyable-text[data-testid='msg-meta']",
                "._3EFt_",  # Selector de metadata
                "span._3EFt_",
                "div._3EFt_",
            ]
            
            time_text = ""
            for selector in time_selectors:
                try:
                    time_element = element.find_element(By.CSS_SELECTOR, selector)
                    if time_element:
                        # Verificar atributo title primero
                        title_time = time_element.get_attribute("title")
                        if title_time and ':' in title_time:
                            time_text = title_time
                            self.logger.debug(f"✅ Timestamp extraído de title: {time_text}")
                            break
                        
                        # Luego verificar texto
                        text_time = time_element.text.strip()
                        if text_time and ':' in text_time:
                            time_text = text_time  
                            self.logger.debug(f"✅ Timestamp extraído de texto: {time_text}")
                            break
                except:
                    continue
            
            # Si no encuentra timestamp específico, usar tiempo actual
            if not time_text:
                self.logger.debug("⚠️ No se pudo extraer timestamp, usando tiempo actual")
                message_time = datetime.now()
            else:
                message_time = self._parse_message_timestamp(time_text)
            
            self.logger.debug(f"✅ Mensaje parseado: '{message_text[:50]}...' @ {message_time.strftime('%H:%M:%S')}")
            return (message_text, message_time)
            
        except Exception as e:
            self.logger.debug(f"❌ Error parseando mensaje: {e}")
            return None
    
    def _parse_message_timestamp(self, time_text: str) -> datetime:
        """
        Parsea el timestamp de un mensaje de WhatsApp.
        
        WhatsApp muestra timestamps en formatos como:
        - "15:30" (hoy)
        - "Ayer" 
        - "dd/mm/yyyy"
        """
        try:
            # Timestamp de hoy (formato HH:MM)
            time_pattern = r'(\d{1,2}):(\d{2})'
            match = re.search(time_pattern, time_text)
            
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                
                # Asumir que es de hoy
                now = datetime.now()
                message_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Si el tiempo es futuro, debe ser de ayer
                if message_time > now:
                    message_time -= timedelta(days=1)
                
                return message_time
            
            # Si no se puede parsear, usar tiempo actual
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def _is_new_message(self, message_time: datetime) -> bool:
        """Determina si un mensaje es nuevo basado en timestamp."""
        if not self.last_message_time:
            return True
            
        return message_time > self.last_message_time
    
    def _verify_connection(self) -> bool:
        """Verifica que la conexión a WhatsApp sigue activa."""
        try:
            # Verificar que el driver sigue activo
            if not self.driver:
                self.logger.warning("Driver no disponible")
                return False
            
            # Verificar que el driver responde
            try:
                current_url = self.driver.current_url
            except Exception as e:
                self.logger.error(f"Driver no responde: {e}")
                return False
                
            # Verificar que estamos en WhatsApp Web
            if "whatsapp.com" not in current_url.lower():
                self.logger.warning(f"No estamos en WhatsApp: {current_url}")
                return False
            if "web.whatsapp.com" not in current_url:
                return False
                
            # Verificar que la interfaz principal está presente
            chat_list = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list']")
            return chat_list is not None
            
        except Exception:
            return False
    
    def _cleanup_driver(self) -> None:
        """Limpia y cierra el driver de Chrome."""
        try:
            if self.driver:
                self.logger.info("Cerrando driver Chrome...")
                
                # Timeout más corto para evitar que se cuelgue
                try:
                    self.driver.set_page_load_timeout(2)
                    self.driver.implicitly_wait(1)
                except:
                    pass
                
                self.driver.quit()
                self.driver = None
                self.logger.info("Driver Chrome cerrado correctamente")
                
        except Exception as e:
            self.logger.warning(f"Error cerrando driver (normal si Chrome se cerró): {e}")
            self.driver = None
    
    def __del__(self):
        """Destructor para asegurar limpieza de recursos."""
        self._cleanup_driver()