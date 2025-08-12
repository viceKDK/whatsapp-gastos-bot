# 📱 Bot Gastos WhatsApp - Guía del Usuario

## 🎯 ¿Qué hace el bot?

El **Bot Gastos WhatsApp** automatiza el registro de tus gastos personales. Solo tienes que escribir tu gasto en el chat de WhatsApp y el bot:

1. ✅ **Detecta** automáticamente que es un gasto
2. 🧠 **Extrae** el monto y categoría usando IA
3. 💾 **Guarda** en Excel para tu control
4. 📊 **Responde** confirmando el registro

---

## 📝 Formatos de Mensajes Soportados

### 🔥 **Formato Básico** (más simple)
```
125 nafta
500 comida
1500 ropa
80 super
```

### 💬 **Formato Natural**
```
compre 2500 ropa
compré 150 nafta
gasté 300 en comida
pagué 800 por zapatos
gaste 120 almuerzo
pague 1000 de luz
```

### 💰 **Con Signo de Pesos**
```
$150 nafta
$ 500 comida
$1200 supermercado
```

### 📋 **Formato Estructurado**
```
gasto: 500 comida
gasto 300 delivery
gastos: 1500 servicios
```

---

## 🏷️ **Categorías Automáticas**

El bot reconoce automáticamente estas categorías según las palabras que uses:

### 🍕 **Comida**
**Palabras clave:** comida, restaurant, almuerzo, cena, pizza, burger, delivery, desayuno, merienda, snack, hamburguer, empanadas, asado, parrilla, sandwich, cafe, yogurt, frutas, verduras

**Ejemplos:**
- `150 almuerzo` → Comida
- `compré 300 pizza` → Comida  
- `500 delivery` → Comida

### 🚗 **Transporte**
**Palabras clave:** nafta, gasolina, combustible, taxi, uber, bus, bondi, colectivo, remis, metro, subte, tren, peaje, estacionamiento, parking

**Ejemplos:**
- `125 nafta` → Transporte
- `gasté 200 uber` → Transporte
- `50 bondi` → Transporte

### 🏠 **Servicios**  
**Palabras clave:** luz, agua, gas, internet, telefono, ute, ose, antel, cable, netflix, spotify, wifi, celular, movil, tv, directv

**Ejemplos:**
- `pagué 1500 luz` → Servicios
- `800 internet` → Servicios
- `netflix 299` → Servicios

### 🛒 **Supermercado**
**Palabras clave:** super, market, tienda, almacen, supermercado, mercado, compras, abarrotes, verduleria, carniceria, panaderia

**Ejemplos:**
- `2000 super` → Supermercado
- `compre 800 market` → Supermercado
- `1200 compras` → Supermercado

### 🏥 **Salud**
**Palabras clave:** farmacia, medicina, doctor, medico, consulta, remedios, pastillas, dentista, oculista, hospital, clinica, analisis

**Ejemplos:**
- `350 farmacia` → Salud
- `gasté 1200 doctor` → Salud
- `500 remedios` → Salud

### 🎭 **Entretenimiento**
**Palabras clave:** cine, bar, juego, netflix, boliche, disco, teatro, concierto, show, partido, futbol, cancha, gym, gimnasio

**Ejemplos:**
- `400 cine` → Entretenimiento
- `compré 800 gym` → Entretenimiento
- `1200 boliche` → Entretenimiento

### 👕 **Ropa**
**Palabras clave:** ropa, pantalon, camisa, remera, zapatos, zapatillas, vestido, pollera, jean, shorts, medias, ropa interior, campera, abrigo, sweater

**Ejemplos:**
- `compre 2500 ropa` → Ropa ✨
- `gasté 1800 zapatos` → Ropa
- `800 remera` → Ropa

### 🏡 **Hogar**
**Palabras clave:** casa, hogar, muebles, decoracion, limpieza, detergente, jabon, shampoo, papel higienico, toallas, sabanas, almohadas

**Ejemplos:**
- `1500 muebles` → Hogar
- `200 detergente` → Hogar
- `compré 800 decoracion` → Hogar

### 💻 **Tecnología**
**Palabras clave:** celular, computadora, laptop, tablet, auriculares, cargador, cable, tecnologia, electronico, gadget

**Ejemplos:**
- `15000 celular` → Tecnología
- `gasté 2500 laptop` → Tecnología
- `300 auriculares` → Tecnología

### 📚 **Educación**
**Palabras clave:** libro, universidad, curso, carrera, estudio, educacion, escuela, colegio, materiales, fotocopias

**Ejemplos:**
- `800 universidad` → Educación
- `compré 200 libro` → Educación
- `150 fotocopias` → Educación

---

## 💡 **Consejos para Mejores Resultados**

### ✅ **Sí funciona**
- `125 nafta` 
- `compre 2500 ropa`
- `gasté 300 almuerzo`
- `$150 super`
- `pagué 800 doctor`

### ❌ **No funciona bien**
- `gastamos mucho` (sin monto específico)
- `fue caro` (sin números)
- `más o menos 200` (palabras extra confunden)

### 🎯 **Tips**
1. **Incluye números claros:** `150` mejor que `ciento cincuenta`
2. **Usa palabras clave:** Incluye la categoría (`nafta`, `comida`, `ropa`)
3. **Sé específico:** `125 nafta` mejor que `125 cosas del auto`
4. **Formato consistente:** Stick to the patterns that work

---

## 📊 **Comandos Especiales**

Envía estos mensajes para funciones especiales:

- `ayuda` / `help` / `?` → Muestra ayuda
- `estadisticas` / `stats` / `resumen` → Resumen de gastos
- `categorias` → Lista de categorías válidas

---

## 🚀 **Ejemplos Completos**

### Gastos del día típico:
```
125 nafta
300 almuerzo  
80 super
compré 1500 remera
gasté 200 farmacia
$50 cafe
```

### Resultado automático:
- ✅ **125** - Transporte (nafta)
- ✅ **300** - Comida (almuerzo) 
- ✅ **80** - Supermercado (super)
- ✅ **1500** - Ropa (remera)
- ✅ **200** - Salud (farmacia)
- ✅ **50** - Comida (cafe)

**Total gastado: $2,255** 💰

---

## ⚙️ **Configuración del Bot**

### Archivo Excel
Los gastos se guardan automáticamente en: `data/gastos.xlsx`

### Columnas generadas:
- **Fecha** - Cuando se registró
- **Hora** - Hora exacta
- **Monto** - Cantidad gastada  
- **Categoría** - Categoría detectada
- **Descripción** - Descripción del gasto

### Chat objetivo
El bot escucha el chat configurado (por defecto: "Gastos")

---

## 🔧 **Solución de Problemas**

### ❓ **El bot no detecta mi gasto**
**Posibles causas:**
- No hay números claros en el mensaje
- Falta palabra clave de categoría
- Formato muy complejo

**Solución:** Usa formato simple: `monto descripcion`
- `❌ me gasté como 200 pesos en cosas` 
- `✅ 200 comida`

### ❓ **Categoría incorrecta**
**Causa:** La palabra clave no está en nuestro diccionario

**Solución:** Usa palabras más específicas:
- `❌ compré 500 cosas` → "otros"
- `✅ compré 500 remera` → "ropa"

### ❓ **No guarda en Excel**
**Verificar:**
1. ✅ Permisos de escritura en la carpeta `data/`
2. ✅ Excel no está abierto (libera el archivo)
3. ✅ Espacio disponible en disco

---

## 📈 **Mejores Prácticas**

### 🎯 **Para máxima precisión:**
1. **Sé específico:** `125 nafta` vs `125 auto`
2. **Usa categorías conocidas:** Consulta la lista de palabras clave
3. **Formato consistente:** Siempre `monto descripcion`
4. **Evita palabras extra:** `200 almuerzo` vs `hoy gasté unos 200 en almuerzo`

### 📱 **Flujo recomendado:**
1. Compras algo → Abres WhatsApp
2. Escribes: `monto descripcion` 
3. Envías mensaje
4. ✅ Bot confirma registro automáticamente
5. 📊 Revisas Excel cuando quieras

---

## 🆘 **Soporte**

**¿Problemas?**
1. Revisa esta guía primero
2. Prueba formato simple: `125 nafta`
3. Verifica que el bot esté ejecutándose
4. Chequea los logs para errores específicos

**¿Ideas de mejora?**
- Nuevas categorías
- Formatos adicionales  
- Funcionalidades extra

---

*💡 **Recuerda:** El bot aprende de tus patrones. Mientras más uses formatos consistentes, mejor será la detección automática.*

---

### 🔄 **Actualizaciones**

**v1.0** - Detección básica y guardado Excel  
**v1.1** - Formatos expandidos ("compre", "gasté", "pagué")  
**v1.2** - Categorías ampliadas (ropa, hogar, tecnología, educación)  
**v1.3** - Soporte para signo de pesos ($)

¡Disfruta automatizando tus gastos! 🚀💰