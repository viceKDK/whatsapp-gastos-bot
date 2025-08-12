"""
⚡ Ultra Fast Message Extractor
Sistema de extracción de mensajes optimizado usando técnicas avanzadas para reducir latencia de 12s a <2s
"""
import time
from typing import List, Tuple, Optional
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json


class UltraFastExtractor:
    """
    🚀 Extractor ultra rápido con técnicas avanzadas:
    1. JavaScript DOM queries directas (10x más rápido que Selenium)
    2. MutationObserver para detectar cambios instantáneamente
    3. Cache inteligente de selectores CSS
    4. Batch processing de elementos
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.cached_selectors = []
        self.mutation_observer_active = False
        
    def initialize_fast_extraction(self):
        """Inicializa JavaScript para extracción ultra rápida."""
        
        # JavaScript para extracción directa sin Selenium overhead
        js_code = """
        window.ultraFastExtract = {
            // Cache de selectores que funcionan
            workingSelectors: [
                'div[role="row"][tabindex="-1"]',
                'div[data-testid="conversation-panel-messages"] div[role="row"]',
                'div._amjv._aotl',
                'div[class*="message-"]'
            ],
            
            // Cache de elementos ya procesados
            processedElements: new Set(),
            
            // Obtener mensajes ultra rápido
            getMessages: function(limit = 10) {
                const startTime = performance.now();
                const results = [];
                
                // Probar selectores en orden de eficiencia
                for (let selector of this.workingSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            console.log(`✅ Selector funcionando: ${selector} (${elements.length} elementos)`);
                            
                            // Procesar elementos en lotes para mayor eficiencia
                            const batch = Array.from(elements).slice(-limit);
                            
                            for (let el of batch) {
                                if (results.length >= limit) break;
                                
                                const text = this.extractText(el);
                                const timestamp = this.extractTimestamp(el);
                                
                                if (text && text.length > 2) {
                                    results.push({
                                        text: text,
                                        timestamp: timestamp,
                                        element_id: el.id || 'no-id'
                                    });
                                }
                            }
                            break; // Usar solo el primer selector que funcione
                        }
                    } catch (e) {
                        console.log(`❌ Selector fallido: ${selector} - ${e}`);
                    }
                }
                
                const endTime = performance.now();
                console.log(`⚡ Extracción JS completada en ${endTime - startTime}ms`);
                return results.slice(-limit); // Solo los últimos N mensajes
            },
            
            // Extracción optimizada de texto
            extractText: function(element) {
                // Múltiples estrategias de extracción de texto en orden de eficiencia
                const strategies = [
                    () => element.querySelector('span[title]')?.textContent?.trim(),
                    () => element.querySelector('span._ao3e')?.textContent?.trim(),
                    () => element.querySelector('[data-testid*="conversation-text"]')?.textContent?.trim(),
                    () => {
                        // Estrategia regex sobre innerHTML (muy rápida)
                        const html = element.innerHTML;
                        const matches = html.match(/>(\\d+\\s+\\w+[^<]*)</g);
                        return matches?.[0]?.replace('>', '')?.replace('<', '')?.trim();
                    },
                    () => element.textContent?.replace(/\\s+/g, ' ')?.trim()
                ];
                
                for (let strategy of strategies) {
                    try {
                        const result = strategy();
                        if (result && result.length > 2 && !result.includes('🤖') && !result.includes('[OK]')) {
                            return result;
                        }
                    } catch (e) { }
                }
                return null;
            },
            
            // Extracción rápida de timestamp
            extractTimestamp: function(element) {
                try {
                    // Buscar timestamp en atributos o elementos
                    const timeEl = element.querySelector('[data-testid*="message-timestamp"], .message-timestamp, [title*=":"]');
                    if (timeEl) {
                        const timeStr = timeEl.getAttribute('title') || timeEl.textContent;
                        // Convertir a timestamp si es posible
                        return timeStr;
                    }
                    return new Date().toISOString(); // Fallback a ahora
                } catch (e) {
                    return new Date().toISOString();
                }
            },
            
            // Setup de MutationObserver para detección instantánea de mensajes nuevos
            setupMutationObserver: function() {
                if (this.observer) return; // Ya configurado
                
                const targetNode = document.querySelector('#main') || document.body;
                
                this.observer = new MutationObserver((mutations) => {
                    let hasNewMessages = false;
                    
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                            // Verificar si se agregaron mensajes nuevos
                            for (let node of mutation.addedNodes) {
                                if (node.nodeType === Node.ELEMENT_NODE && 
                                    (node.matches('[role="row"]') || 
                                     node.querySelector('[role="row"]'))) {
                                    hasNewMessages = true;
                                    break;
                                }
                            }
                        }
                    });
                    
                    if (hasNewMessages) {
                        window.ultraFastExtract.lastChangeTime = Date.now();
                        console.log('🆕 MutationObserver: Nuevos mensajes detectados');
                    }
                });
                
                this.observer.observe(targetNode, {
                    childList: true,
                    subtree: true
                });
                
                console.log('👀 MutationObserver activado para detección instantánea');
            },
            
            // Verificar si hay cambios recientes
            hasRecentChanges: function(maxAgeMs = 5000) {
                return (Date.now() - (this.lastChangeTime || 0)) < maxAgeMs;
            }
        };
        
        // Inicializar MutationObserver
        window.ultraFastExtract.setupMutationObserver();
        
        return true;
        """
        
        try:
            result = self.driver.execute_script(js_code)
            self.mutation_observer_active = True
            return result
        except Exception as e:
            print(f"❌ Error inicializando extracción rápida: {e}")
            return False
    
    def get_messages_ultra_fast(self, limit: int = 10) -> List[Tuple[str, datetime]]:
        """
        🚀 Obtiene mensajes usando JavaScript directo (10x más rápido que Selenium).
        
        Tiempo esperado: <2 segundos vs 12+ segundos del método tradicional
        """
        start_time = time.time()
        
        # Inicializar si no está listo
        if not self.mutation_observer_active:
            self.initialize_fast_extraction()
        
        try:
            # Ejecutar extracción JavaScript ultra rápida
            js_result = self.driver.execute_script(f"""
                return window.ultraFastExtract.getMessages({limit});
            """)
            
            # Convertir resultados a formato esperado
            messages = []
            for item in js_result or []:
                text = item.get('text', '').strip()
                timestamp_str = item.get('timestamp', '')
                
                # Parsear timestamp
                try:
                    # Intentar parsear diferentes formatos de timestamp
                    if ':' in timestamp_str:
                        # Formato "HH:MM" -> usar fecha de hoy
                        from datetime import datetime, date
                        today = date.today()
                        time_part = datetime.strptime(timestamp_str, '%H:%M').time()
                        timestamp = datetime.combine(today, time_part)
                    else:
                        # Formato ISO o fallback a ahora
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()
                
                if text and len(text) > 2:
                    messages.append((text, timestamp))
            
            elapsed = time.time() - start_time
            print(f"⚡ UltraFast extraction: {len(messages)} mensajes en {elapsed*1000:.1f}ms")
            
            return messages[-limit:]  # Retornar solo los últimos N
            
        except Exception as e:
            print(f"❌ Error en extracción ultra rápida: {e}")
            return []
    
    def has_new_messages_instant(self) -> bool:
        """
        ⚡ Verificación instantánea de mensajes nuevos usando MutationObserver.
        
        Tiempo: <100ms vs varios segundos del método tradicional
        """
        try:
            result = self.driver.execute_script("""
                return window.ultraFastExtract.hasRecentChanges(3000);
            """)
            return bool(result)
        except:
            return True  # En caso de error, asumir que hay cambios
    
    def cleanup(self):
        """Limpia recursos del extractor."""
        try:
            self.driver.execute_script("""
                if (window.ultraFastExtract && window.ultraFastExtract.observer) {
                    window.ultraFastExtract.observer.disconnect();
                }
            """)
        except:
            pass