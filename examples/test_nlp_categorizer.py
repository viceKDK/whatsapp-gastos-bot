"""
Ejemplo de uso del Categorizador NLP

Este script demuestra cómo usar el sistema de categorización
automática de gastos usando NLP y machine learning.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.nlp_categorizer import get_nlp_categorizer, categorize_gasto
from app.services.interpretar_mensaje import InterpretarMensajeService
from domain.models.gasto import Gasto
from shared.logger import get_logger
from datetime import datetime


def main():
    """Función principal de ejemplo."""
    logger = get_logger(__name__)
    
    print("🧠 Ejemplo de Categorizador NLP")
    print("=" * 50)
    
    # Verificar dependencias
    try:
        import sklearn
        import pandas as pd
        print("✅ Dependencias ML verificadas")
        print(f"   scikit-learn: {sklearn.__version__}")
        print(f"   pandas: {pd.__version__}")
    except ImportError as e:
        print(f"❌ Error: Dependencia faltante: {e}")
        print("\n📦 Instala las dependencias ML con:")
        print("   pip install scikit-learn pandas")
        print("\n🚀 O instala todas las dependencias:")
        print("   pip install -r requirements.txt")
        return
    
    # Crear datos de ejemplo para entrenamiento
    gastos_ejemplo = [
        # Comida
        Gasto(500, "comida", datetime.now(), "almuerzo restaurant centro"),
        Gasto(300, "comida", datetime.now(), "pizza delivery casa"),
        Gasto(150, "comida", datetime.now(), "hamburguesa mcdonalds"),
        Gasto(800, "comida", datetime.now(), "cena restaurant parrilla"),
        Gasto(250, "comida", datetime.now(), "desayuno cafe tostado"),
        
        # Transporte
        Gasto(1200, "transporte", datetime.now(), "nafta ancap estacion"),
        Gasto(180, "transporte", datetime.now(), "taxi centro pocitos"),
        Gasto(1500, "transporte", datetime.now(), "combustible diesel camioneta"),
        Gasto(250, "transporte", datetime.now(), "uber aeropuerto casa"),
        Gasto(80, "transporte", datetime.now(), "bus omnibus cutcsa"),
        
        # Servicios
        Gasto(2500, "servicios", datetime.now(), "ute luz electricidad casa"),
        Gasto(1800, "servicios", datetime.now(), "ose agua potable"),
        Gasto(1200, "servicios", datetime.now(), "antel internet fibra"),
        Gasto(3200, "servicios", datetime.now(), "directv cable television"),
        Gasto(900, "servicios", datetime.now(), "celular plan antel"),
        
        # Supermercado
        Gasto(2200, "supermercado", datetime.now(), "compras disco supermercado"),
        Gasto(1800, "supermercado", datetime.now(), "tienda inglesa verduras"),
        Gasto(900, "supermercado", datetime.now(), "devoto limpieza hogar"),
        Gasto(1500, "supermercado", datetime.now(), "ta-ta compras semana"),
        
        # Salud
        Gasto(450, "salud", datetime.now(), "farmacia medicamentos gripe"),
        Gasto(1200, "salud", datetime.now(), "doctor consulta medico"),
        Gasto(800, "salud", datetime.now(), "farmahorro vitaminas"),
        
        # Entretenimiento
        Gasto(320, "entretenimiento", datetime.now(), "cine movie pelicula"),
        Gasto(150, "entretenimiento", datetime.now(), "netflix suscripcion mensual"),
        Gasto(600, "entretenimiento", datetime.now(), "bar copas amigos"),
    ]
    
    print(f"\n🎯 Datos de entrenamiento: {len(gastos_ejemplo)} gastos")
    
    # Mostrar distribución por categorías
    categorias = {}
    for gasto in gastos_ejemplo:
        categorias[gasto.categoria] = categorias.get(gasto.categoria, 0) + 1
    
    print("   📊 Distribución por categorías:")
    for categoria, count in categorias.items():
        print(f"      {categoria}: {count} gastos")
    
    # Obtener categorizador
    print("\n🔧 Inicializando categorizador NLP...")
    categorizer = get_nlp_categorizer()
    
    # Mostrar información del sistema
    info = categorizer.get_info()
    print(f"   ✅ ML disponible: {info['sklearn_available']}")
    print(f"   🔧 ML habilitado: {info['ml_enabled']}")
    print(f"   🎯 Modelo entrenado: {info['model_trained']}")
    
    # Entrenar modelo si es necesario
    if not info['model_trained']:
        print("\n🎓 Entrenando modelo...")
        try:
            stats = categorizer.ml_categorizer.train_from_gastos(gastos_ejemplo)
            print(f"   ✅ Entrenamiento completado!")
            print(f"      📊 Ejemplos: {stats.total_ejemplos}")
            print(f"      🎯 Accuracy: {stats.accuracy:.1%}")
            print(f"      📈 Features: {stats.features_count}")
            print(f"      ⏱️  Fecha: {stats.fecha_entrenamiento.strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            print(f"   ❌ Error entrenando: {e}")
            return
    else:
        stats = categorizer.get_training_stats()
        print(f"\n📊 Modelo ya entrenado:")
        print(f"   📊 Ejemplos: {stats.total_ejemplos}")
        print(f"   🎯 Accuracy: {stats.accuracy:.1%}")
    
    # Probar categorización con ejemplos nuevos
    print("\n" + "=" * 50)
    print("🧪 PROBANDO CATEGORIZACIÓN AUTOMÁTICA")
    print("=" * 50)
    
    ejemplos_prueba = [
        ("pizza napoletana delivery", 400),
        ("gasolina shell estacion", 1100),
        ("supermercado fresh market", 1800),
        ("consulta traumatologo", 1500),
        ("netflix prime video", 300),
        ("electricidad ute", 2800),
        ("taxi uber centro", 200),
        ("hamburguesa burger king", 350),
        ("farmacia antibioticos", 550),
        ("compras disco", 2100),
        ("antel fibra internet", 1400),
        ("cine hoyts peliculas", 280),
        ("nafta ancap ruta", 1300),
        ("restaurant sushi", 900),
    ]
    
    print("Probando con ejemplos nuevos:")
    print()
    
    aciertos = 0
    total = 0
    
    for descripcion, monto in ejemplos_prueba:
        resultado = categorizer.categorize(descripcion, monto)
        
        # Determinar categoría "correcta" manualmente para validación
        categoria_esperada = determinar_categoria_esperada(descripcion)
        es_correcto = resultado.categoria_predicha == categoria_esperada
        
        if es_correcto:
            aciertos += 1
        total += 1
        
        print(f"📝 '{descripcion}' (${monto})")
        print(f"   🎯 Predicho: {resultado.categoria_predicha} ({resultado.confianza:.1%})")
        print(f"   🔧 Método: {resultado.metodo}")
        print(f"   {'✅' if es_correcto else '❌'} Esperado: {categoria_esperada}")
        print(f"   ⏱️  Tiempo: {resultado.tiempo_procesamiento:.3f}s")
        
        if resultado.alternativas:
            print(f"   💡 Alternativas: {', '.join([f'{alt[0]} ({alt[1]:.1%})' for alt in resultado.alternativas[:2]])}")
        
        print()
    
    accuracy_manual = aciertos / total if total > 0 else 0
    print(f"🎯 Accuracy en ejemplos de prueba: {accuracy_manual:.1%} ({aciertos}/{total})")
    
    # Mostrar estadísticas de uso
    print("\n📊 Estadísticas de uso:")
    usage_stats = categorizer.get_usage_stats()
    print(f"   📈 Total predicciones: {usage_stats['total_predictions']}")
    print(f"   🔧 Uso por método:")
    for method, count in usage_stats['method_usage'].items():
        percentage = (count / usage_stats['total_predictions'] * 100) if usage_stats['total_predictions'] > 0 else 0
        print(f"      {method}: {count} ({percentage:.1f}%)")
    
    # Probar integración con InterpretarMensajeService
    print("\n" + "=" * 50)
    print("🔗 INTEGRACIÓN CON MENSAJE PROCESSOR")
    print("=" * 50)
    
    mensaje_service = InterpretarMensajeService(enable_nlp_categorization=True)
    nlp_info = mensaje_service.get_nlp_info()
    
    print(f"NLP en Message Processor:")
    print(f"   ✅ Habilitado: {nlp_info['enabled']}")
    print(f"   🔧 Disponible: {nlp_info['available']}")
    
    if nlp_info['enabled']:
        mensajes_prueba = [
            "gasté 400 pizza delivery",
            "1200 nafta ancap",
            "pagué 2500 luz ute",
            "compré 1800 super disco",
            "500 doctor consulta",
        ]
        
        print("\nProbando mensajes con NLP:")
        for mensaje in mensajes_prueba:
            gasto = mensaje_service.procesar_mensaje(mensaje)
            if gasto:
                print(f"📱 '{mensaje}'")
                print(f"   💰 ${gasto.monto} - {gasto.categoria}")
                print(f"   📝 {gasto.descripcion or 'Sin descripción'}")
            else:
                print(f"❌ No se pudo procesar: '{mensaje}'")
            print()
    
    print("\n🎉 Ejemplo completado exitosamente!")
    print("\n💡 Consejos para mejorar el modelo:")
    print("   • Agrega más datos de entrenamiento con gastos reales")
    print("   • Usa descripciones más variadas y naturales")
    print("   • El modelo mejora automáticamente con más datos")


def determinar_categoria_esperada(descripcion: str) -> str:
    """Determina la categoría esperada manualmente para validación."""
    desc_lower = descripcion.lower()
    
    if any(word in desc_lower for word in ['pizza', 'hamburguesa', 'restaurant', 'sushi']):
        return 'comida'
    elif any(word in desc_lower for word in ['gasolina', 'nafta', 'taxi', 'uber']):
        return 'transporte'
    elif any(word in desc_lower for word in ['supermercado', 'disco', 'fresh', 'compras']):
        return 'supermercado'
    elif any(word in desc_lower for word in ['doctor', 'consulta', 'farmacia']):
        return 'salud'
    elif any(word in desc_lower for word in ['netflix', 'cine', 'hoyts']):
        return 'entretenimiento'
    elif any(word in desc_lower for word in ['ute', 'electricidad', 'antel', 'internet']):
        return 'servicios'
    else:
        return 'otros'


if __name__ == "__main__":
    main()