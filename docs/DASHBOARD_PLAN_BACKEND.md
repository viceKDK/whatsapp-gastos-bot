# Plan de Implementación: Dashboard Backend (API Flask)

## Objetivo
Extender la API Flask existente con endpoints avanzados para soportar el dashboard moderno de gastos.

---

## Stack Tecnológico

- **Framework**: Flask + Flask-CORS
- **Storage**: SQLite + Excel (híbrido)
- **Caché**: Flask-Caching (opcional)
- **Validación**: Pydantic o Marshmallow (opcional)

---

## Estructura de Archivos

```
interface/web/
├── dashboard_app.py           # Flask app principal (actualizar)
│
app/services/
├── dashboard_analytics.py     # Análisis y métricas avanzadas (NUEVO)
├── data_aggregator.py         # Agregación de datos (NUEVO)
└── export_service.py          # Exportación de datos (NUEVO)

infrastructure/storage/
├── sqlite_writer.py           # Ya existe
├── excel_writer.py            # Ya existe
└── hybrid_storage.py          # Ya existe
```

---

## Endpoints API Existentes

### ✅ Ya Implementados (dashboard_app.py:276-400)

```python
GET /api/summary
- Retorna: estadísticas resumidas
- Response: {
    'total_gastos': int,
    'total_monto': float,
    'gastos_este_mes': int,
    'monto_este_mes': float,
    'promedio_diario': float,
    'categoria_mas_comun': str,
    'gasto_mas_alto': float,
    'ultima_actualizacion': str (ISO)
  }

GET /api/categories?days=30
- Retorna: gastos agrupados por categoría
- Response: {
    'categories': [str],
    'amounts': [float],
    'total_categories': int,
    'period_days': int
  }

GET /api/timeline?days=30
- Retorna: serie temporal de gastos
- Response: {
    'dates': [str],
    'amounts': [float],
    'period_days': int,
    'total_days': int
  }

GET /api/recent?limit=10
- Retorna: gastos más recientes
- Response: [{
    'id': int,
    'monto': float,
    'categoria': str,
    'descripcion': str,
    'fecha': str,
    'fecha_iso': str (ISO)
  }]

GET /api/metrics
- Retorna: métricas del sistema
- Response: {
    'health': {...},
    'operations': {...},
    'timestamp': str (ISO)
  }

GET /api/refresh
- Refresca los datos del dashboard
- Response: {
    'success': bool,
    'message': str,
    'timestamp': str (ISO)
  }
```

---

## Fase 1: Extender Endpoints Existentes

### 1.1 Mejorar GET /api/summary
**Archivo**: `interface/web/dashboard_app.py`
**Línea**: Actualizar método `get_summary_stats()` (línea 69-114)

**Mejoras a agregar**:
```python
def get_summary_stats(self) -> Dict[str, Any]:
    """Obtiene estadísticas resumidas con comparaciones."""
    try:
        if not self.storage:
            return self._get_empty_stats()

        # Obtener gastos del mes actual
        now = datetime.now()
        start_this_month = datetime(now.year, now.month, 1)
        end_this_month = now

        # Obtener gastos del mes anterior
        if now.month == 1:
            start_last_month = datetime(now.year - 1, 12, 1)
            end_last_month = datetime(now.year - 1, 12, 31, 23, 59, 59)
        else:
            start_last_month = datetime(now.year, now.month - 1, 1)
            last_day = (start_this_month - timedelta(days=1)).day
            end_last_month = datetime(now.year, now.month - 1, last_day, 23, 59, 59)

        # Obtener datos
        gastos_mes_actual = self.storage.obtener_gastos_por_fecha(start_this_month, end_this_month)
        gastos_mes_anterior = self.storage.obtener_gastos_por_fecha(start_last_month, end_last_month)
        all_gastos = self.storage.obtener_todos_gastos()

        # Calcular totales
        monto_mes_actual = sum(float(g.monto) for g in gastos_mes_actual)
        monto_mes_anterior = sum(float(g.monto) for g in gastos_mes_anterior)
        total_monto = sum(float(g.monto) for g in all_gastos)

        # Calcular cambio porcentual
        if monto_mes_anterior > 0:
            cambio_porcentual = ((monto_mes_actual - monto_mes_anterior) / monto_mes_anterior) * 100
        else:
            cambio_porcentual = 0

        # Promedio diario
        dias_transcurridos = (now - start_this_month).days + 1
        promedio_diario = monto_mes_actual / dias_transcurridos if dias_transcurridos > 0 else 0

        # Proyección mensual
        dias_en_mes = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day if now.month < 12 else 31
        proyeccion_mensual = promedio_diario * dias_en_mes

        # Categoría más común
        if all_gastos:
            categorias = [g.categoria for g in all_gastos]
            categoria_mas_comun = max(set(categorias), key=categorias.count)
        else:
            categoria_mas_comun = "N/A"

        # Gasto más alto este mes
        gasto_mas_alto = max((float(g.monto) for g in gastos_mes_actual), default=0)

        return {
            # Totales
            'total_gastos': len(all_gastos),
            'total_monto': total_monto,

            # Este mes
            'gastos_este_mes': len(gastos_mes_actual),
            'monto_este_mes': monto_mes_actual,
            'promedio_diario': promedio_diario,
            'proyeccion_mensual': proyeccion_mensual,

            # Comparaciones
            'monto_mes_anterior': monto_mes_anterior,
            'cambio_porcentual': cambio_porcentual,
            'cambio_absoluto': monto_mes_actual - monto_mes_anterior,

            # Estadísticas
            'categoria_mas_comun': categoria_mas_comun,
            'gasto_mas_alto': gasto_mas_alto,

            # Meta
            'ultima_actualizacion': datetime.now().isoformat(),
            'periodo': {
                'inicio': start_this_month.isoformat(),
                'fin': end_this_month.isoformat(),
                'dias_transcurridos': dias_transcurridos,
                'dias_totales': dias_en_mes
            }
        }

    except Exception as e:
        self.logger.error(f"Error obteniendo estadísticas: {e}")
        return self._get_empty_stats()
```

### 1.2 Mejorar GET /api/categories
**Archivo**: `interface/web/dashboard_app.py`
**Línea**: Actualizar método `get_gastos_por_categoria()` (línea 116-148)

**Mejoras a agregar**:
```python
def get_gastos_por_categoria(self, days: int = 30) -> Dict[str, Any]:
    """Obtiene gastos agrupados por categoría con detalles."""
    try:
        if not self.storage:
            return {'categories': [], 'amounts': [], 'details': []}

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        gastos = self.storage.obtener_gastos_por_fecha(start_date, end_date)

        # Agrupar por categoría con conteo
        categoria_data = {}
        for gasto in gastos:
            categoria = gasto.categoria
            monto = float(gasto.monto)

            if categoria not in categoria_data:
                categoria_data[categoria] = {
                    'total': 0,
                    'count': 0,
                    'promedio': 0,
                    'max': 0,
                    'min': float('inf')
                }

            categoria_data[categoria]['total'] += monto
            categoria_data[categoria]['count'] += 1
            categoria_data[categoria]['max'] = max(categoria_data[categoria]['max'], monto)
            categoria_data[categoria]['min'] = min(categoria_data[categoria]['min'], monto)

        # Calcular promedios y porcentajes
        total_amount = sum(data['total'] for data in categoria_data.values())

        for categoria in categoria_data:
            categoria_data[categoria]['promedio'] = (
                categoria_data[categoria]['total'] / categoria_data[categoria]['count']
            )
            categoria_data[categoria]['porcentaje'] = (
                (categoria_data[categoria]['total'] / total_amount * 100) if total_amount > 0 else 0
            )

        # Ordenar por monto total (mayor a menor)
        sorted_categories = sorted(
            categoria_data.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )

        # Preparar respuesta
        categories = [item[0] for item in sorted_categories]
        amounts = [item[1]['total'] for item in sorted_categories]
        details = [
            {
                'categoria': cat,
                'total': data['total'],
                'count': data['count'],
                'promedio': data['promedio'],
                'max': data['max'],
                'min': data['min'],
                'porcentaje': data['porcentaje']
            }
            for cat, data in sorted_categories
        ]

        return {
            'categories': categories,
            'amounts': amounts,
            'details': details,
            'total_categories': len(categories),
            'total_amount': total_amount,
            'period_days': days
        }

    except Exception as e:
        self.logger.error(f"Error obteniendo gastos por categoría: {e}")
        return {'categories': [], 'amounts': [], 'details': []}
```

### 1.3 Agregar Métodos al Storage
**Archivo**: `infrastructure/storage/excel_writer.py`
**Agregar método**: `obtener_gastos_por_fecha()`

```python
def obtener_gastos_por_fecha(self, fecha_desde: datetime, fecha_hasta: datetime) -> List[Gasto]:
    """
    Obtiene gastos en un rango de fechas (con datetime).

    Args:
        fecha_desde: Fecha y hora de inicio
        fecha_hasta: Fecha y hora de fin

    Returns:
        Lista de gastos en el rango
    """
    return self.obtener_gastos(fecha_desde.date(), fecha_hasta.date())

def obtener_todos_gastos(self) -> List[Gasto]:
    """
    Obtiene todos los gastos registrados.

    Returns:
        Lista de todos los gastos
    """
    fecha_inicio = date(2000, 1, 1)
    fecha_fin = date(2100, 12, 31)
    return self.obtener_gastos(fecha_inicio, fecha_fin)
```

**Archivo**: `infrastructure/storage/sqlite_writer.py`
**Verificar que existan métodos similares**

---

## Fase 2: Nuevos Endpoints API

### 2.1 GET /api/v2/balance
**Endpoint para balance consolidado**

**Archivo**: `interface/web/dashboard_app.py`
**Agregar en `setup_routes()`** (después de línea 400):

```python
@self.app.route('/api/v2/balance')
def api_balance():
    """API endpoint para balance consolidado."""
    try:
        data = self.data_provider.get_balance_info()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        self.logger.error(f"Error en API balance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Agregar método en `DashboardDataProvider`** (después de línea 253):

```python
def get_balance_info(self) -> Dict[str, Any]:
    """Obtiene información de balance consolidado."""
    try:
        if not self.storage:
            return {'balance': 0, 'cambio': 0}

        all_gastos = self.storage.obtener_todos_gastos()
        total_balance = sum(float(g.monto) for g in all_gastos)

        # Balance del mes anterior
        now = datetime.now()
        if now.month == 1:
            start_last_month = datetime(now.year - 1, 12, 1)
            end_last_month = datetime(now.year - 1, 12, 31, 23, 59, 59)
        else:
            start_last_month = datetime(now.year, now.month - 1, 1)
            last_day = (datetime(now.year, now.month, 1) - timedelta(days=1)).day
            end_last_month = datetime(now.year, now.month - 1, last_day, 23, 59, 59)

        gastos_mes_anterior = self.storage.obtener_gastos_por_fecha(start_last_month, end_last_month)
        balance_mes_anterior = sum(float(g.monto) for g in gastos_mes_anterior)

        # Calcular cambio
        cambio_porcentual = 0
        if balance_mes_anterior > 0:
            cambio_porcentual = ((total_balance - balance_mes_anterior) / balance_mes_anterior) * 100

        return {
            'balance_total': total_balance,
            'balance_mes_anterior': balance_mes_anterior,
            'cambio_porcentual': cambio_porcentual,
            'cambio_absoluto': total_balance - balance_mes_anterior,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        self.logger.error(f"Error obteniendo balance: {e}")
        return {'balance': 0, 'cambio': 0}
```

### 2.2 GET /api/v2/spending
**Endpoint para información de gastos y límites**

```python
@self.app.route('/api/v2/spending')
def api_spending():
    """API endpoint para información de gastos."""
    try:
        data = self.data_provider.get_spending_info()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        self.logger.error(f"Error en API spending: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Método en `DashboardDataProvider`**:

```python
def get_spending_info(self, limite_mensual: float = 50000) -> Dict[str, Any]:
    """Obtiene información de gastos y límite mensual."""
    try:
        if not self.storage:
            return self._get_empty_spending()

        # Gastos del mes actual
        now = datetime.now()
        start_month = datetime(now.year, now.month, 1)
        gastos_mes = self.storage.obtener_gastos_por_fecha(start_month, now)

        total_mes = sum(float(g.monto) for g in gastos_mes)
        porcentaje_usado = (total_mes / limite_mensual * 100) if limite_mensual > 0 else 0

        # Días restantes en el mes
        dias_en_mes = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day if now.month < 12 else 31
        dias_restantes = dias_en_mes - now.day

        # Proyección
        dias_transcurridos = now.day
        promedio_diario = total_mes / dias_transcurridos if dias_transcurridos > 0 else 0
        proyeccion = promedio_diario * dias_en_mes

        # Límite diario restante
        monto_restante = limite_mensual - total_mes
        limite_diario_restante = monto_restante / dias_restantes if dias_restantes > 0 else 0

        return {
            'total_gastado': total_mes,
            'limite_mensual': limite_mensual,
            'monto_restante': monto_restante,
            'porcentaje_usado': porcentaje_usado,
            'promedio_diario': promedio_diario,
            'limite_diario_restante': limite_diario_restante,
            'proyeccion_mes': proyeccion,
            'dias_restantes': dias_restantes,
            'alerta': {
                'nivel': 'normal' if porcentaje_usado < 80 else 'warning' if porcentaje_usado < 100 else 'danger',
                'mensaje': self._get_spending_alert_message(porcentaje_usado)
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        self.logger.error(f"Error obteniendo spending info: {e}")
        return self._get_empty_spending()

def _get_spending_alert_message(self, porcentaje: float) -> str:
    """Genera mensaje de alerta según el porcentaje usado."""
    if porcentaje < 80:
        return "Gasto dentro del límite"
    elif porcentaje < 100:
        return "Acercándote al límite de gastos"
    else:
        return "¡Límite de gastos superado!"

def _get_empty_spending(self) -> Dict[str, Any]:
    """Retorna spending info vacío."""
    return {
        'total_gastado': 0,
        'limite_mensual': 50000,
        'monto_restante': 50000,
        'porcentaje_usado': 0,
        'promedio_diario': 0,
        'limite_diario_restante': 0,
        'proyeccion_mes': 0,
        'dias_restantes': 30,
        'alerta': {'nivel': 'normal', 'mensaje': 'Sin gastos registrados'},
        'timestamp': datetime.now().isoformat()
    }
```

### 2.3 GET /api/v2/trends
**Endpoint para tendencias y predicciones**

```python
@self.app.route('/api/v2/trends')
def api_trends():
    """API endpoint para tendencias de gasto."""
    try:
        data = self.data_provider.get_spending_trends()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        self.logger.error(f"Error en API trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Método en `DashboardDataProvider`**:

```python
def get_spending_trends(self) -> Dict[str, Any]:
    """Analiza tendencias de gasto."""
    try:
        if not self.storage:
            return {'tendencia': 'neutral', 'prediccion': 0}

        # Obtener gastos de últimos 3 meses
        now = datetime.now()
        months_data = []

        for i in range(3):
            if now.month - i <= 0:
                month = 12 + (now.month - i)
                year = now.year - 1
            else:
                month = now.month - i
                year = now.year

            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year, 12, 31, 23, 59, 59)
            else:
                end = datetime(year, month + 1, 1) - timedelta(seconds=1)

            gastos = self.storage.obtener_gastos_por_fecha(start, end)
            total = sum(float(g.monto) for g in gastos)

            months_data.append({
                'mes': f"{year}-{month:02d}",
                'total': total,
                'count': len(gastos)
            })

        # Calcular tendencia (simple)
        if len(months_data) >= 2:
            cambio_1_a_2 = months_data[1]['total'] - months_data[2]['total']
            cambio_0_a_1 = months_data[0]['total'] - months_data[1]['total']

            promedio_cambio = (cambio_1_a_2 + cambio_0_a_1) / 2

            if promedio_cambio > 500:
                tendencia = 'creciente'
            elif promedio_cambio < -500:
                tendencia = 'decreciente'
            else:
                tendencia = 'estable'
        else:
            tendencia = 'insuficiente_datos'

        # Predicción simple para próximo mes
        if len(months_data) >= 2:
            promedio_ultimos_meses = sum(m['total'] for m in months_data[:2]) / 2
            prediccion_proximo_mes = promedio_ultimos_meses
        else:
            prediccion_proximo_mes = months_data[0]['total'] if months_data else 0

        return {
            'tendencia': tendencia,
            'meses': months_data,
            'prediccion_proximo_mes': prediccion_proximo_mes,
            'confianza': 'media',  # Simple, podría mejorarse con ML
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        self.logger.error(f"Error calculando tendencias: {e}")
        return {'tendencia': 'error', 'prediccion': 0}
```

### 2.4 GET /api/v2/comparison
**Endpoint para comparaciones mes a mes**

```python
@self.app.route('/api/v2/comparison')
def api_comparison():
    """API endpoint para comparación mes a mes."""
    try:
        data = self.data_provider.get_month_comparison()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        self.logger.error(f"Error en API comparison: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Método en `DashboardDataProvider`**:

```python
def get_month_comparison(self) -> Dict[str, Any]:
    """Compara mes actual con mes anterior."""
    try:
        if not self.storage:
            return {'mes_actual': {}, 'mes_anterior': {}, 'cambios': {}}

        now = datetime.now()

        # Mes actual
        start_this = datetime(now.year, now.month, 1)
        gastos_this = self.storage.obtener_gastos_por_fecha(start_this, now)

        # Mes anterior
        if now.month == 1:
            start_last = datetime(now.year - 1, 12, 1)
            end_last = datetime(now.year - 1, 12, 31, 23, 59, 59)
        else:
            start_last = datetime(now.year, now.month - 1, 1)
            last_day = (start_this - timedelta(days=1)).day
            end_last = datetime(now.year, now.month - 1, last_day, 23, 59, 59)

        gastos_last = self.storage.obtener_gastos_por_fecha(start_last, end_last)

        # Agrupar por categoría para ambos meses
        def group_by_category(gastos):
            result = {}
            for g in gastos:
                cat = g.categoria
                if cat not in result:
                    result[cat] = 0
                result[cat] += float(g.monto)
            return result

        this_by_cat = group_by_category(gastos_this)
        last_by_cat = group_by_category(gastos_last)

        # Calcular cambios por categoría
        all_categories = set(list(this_by_cat.keys()) + list(last_by_cat.keys()))
        cambios_categoria = {}

        for cat in all_categories:
            this_val = this_by_cat.get(cat, 0)
            last_val = last_by_cat.get(cat, 0)

            if last_val > 0:
                cambio_pct = ((this_val - last_val) / last_val) * 100
            else:
                cambio_pct = 100 if this_val > 0 else 0

            cambios_categoria[cat] = {
                'mes_actual': this_val,
                'mes_anterior': last_val,
                'cambio_absoluto': this_val - last_val,
                'cambio_porcentual': cambio_pct
            }

        # Totales
        total_this = sum(this_by_cat.values())
        total_last = sum(last_by_cat.values())
        cambio_total_pct = ((total_this - total_last) / total_last * 100) if total_last > 0 else 0

        return {
            'mes_actual': {
                'total': total_this,
                'count': len(gastos_this),
                'por_categoria': this_by_cat
            },
            'mes_anterior': {
                'total': total_last,
                'count': len(gastos_last),
                'por_categoria': last_by_cat
            },
            'cambios': {
                'total_absoluto': total_this - total_last,
                'total_porcentual': cambio_total_pct,
                'por_categoria': cambios_categoria,
                'categorias_nuevas': list(set(this_by_cat.keys()) - set(last_by_cat.keys())),
                'categorias_eliminadas': list(set(last_by_cat.keys()) - set(this_by_cat.keys()))
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        self.logger.error(f"Error en comparación mensual: {e}")
        return {'mes_actual': {}, 'mes_anterior': {}, 'cambios': {}}
```

### 2.5 GET /api/v2/search
**Endpoint para búsqueda avanzada**

```python
@self.app.route('/api/v2/search')
def api_search():
    """API endpoint para búsqueda de gastos."""
    try:
        # Parámetros de búsqueda
        query = request.args.get('query', '')
        categoria = request.args.get('categoria', 'all')
        fecha_desde = request.args.get('from')
        fecha_hasta = request.args.get('to')
        min_monto = request.args.get('min', type=float)
        max_monto = request.args.get('max', type=float)
        limit = request.args.get('limit', 50, type=int)

        data = self.data_provider.search_gastos(
            query=query,
            categoria=categoria if categoria != 'all' else None,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            min_monto=min_monto,
            max_monto=max_monto,
            limit=limit
        )

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        self.logger.error(f"Error en API search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Método en `DashboardDataProvider`**:

```python
def search_gastos(
    self,
    query: str = '',
    categoria: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    min_monto: Optional[float] = None,
    max_monto: Optional[float] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Búsqueda avanzada de gastos."""
    try:
        if not self.storage:
            return []

        # Fechas por defecto (último año)
        if not fecha_desde:
            fecha_desde = datetime.now() - timedelta(days=365)
        else:
            fecha_desde = datetime.fromisoformat(fecha_desde)

        if not fecha_hasta:
            fecha_hasta = datetime.now()
        else:
            fecha_hasta = datetime.fromisoformat(fecha_hasta)

        # Obtener todos los gastos en el rango
        gastos = self.storage.obtener_gastos_por_fecha(fecha_desde, fecha_hasta)

        # Filtrar por categoría
        if categoria:
            gastos = [g for g in gastos if g.categoria.lower() == categoria.lower()]

        # Filtrar por monto
        if min_monto is not None:
            gastos = [g for g in gastos if float(g.monto) >= min_monto]

        if max_monto is not None:
            gastos = [g for g in gastos if float(g.monto) <= max_monto]

        # Búsqueda por texto en descripción o categoría
        if query:
            query_lower = query.lower()
            gastos = [
                g for g in gastos
                if (g.descripcion and query_lower in g.descripcion.lower()) or
                   query_lower in g.categoria.lower()
            ]

        # Ordenar por fecha (más reciente primero)
        gastos = sorted(gastos, key=lambda g: g.fecha, reverse=True)

        # Limitar resultados
        gastos = gastos[:limit]

        # Convertir a formato JSON
        result = []
        for gasto in gastos:
            result.append({
                'id': getattr(gasto, 'id', None),
                'monto': float(gasto.monto),
                'categoria': gasto.categoria,
                'descripcion': gasto.descripcion or '',
                'fecha': gasto.fecha.strftime('%Y-%m-%d %H:%M'),
                'fecha_iso': gasto.fecha.isoformat()
            })

        return result

    except Exception as e:
        self.logger.error(f"Error en búsqueda de gastos: {e}")
        return []
```

### 2.6 GET /api/v2/export
**Endpoint para exportar datos**

```python
@self.app.route('/api/v2/export')
def api_export():
    """API endpoint para exportar datos."""
    try:
        formato = request.args.get('format', 'json')
        fecha_desde = request.args.get('from')
        fecha_hasta = request.args.get('to')

        data = self.data_provider.export_data(
            formato=formato,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if formato == 'json':
            return jsonify({
                'success': True,
                'data': data
            })
        elif formato == 'csv':
            # Implementar conversión a CSV
            return Response(
                data,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=gastos.csv'}
            )

    except Exception as e:
        self.logger.error(f"Error en API export: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## Fase 3: Optimizaciones

### 3.1 Implementar Caché
**Archivo**: `interface/web/dashboard_app.py`

```python
from flask_caching import Cache

# En __init__ de DashboardApp
self.cache = Cache(self.app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 60  # 60 segundos
})

# Decorar endpoints con caché
@self.cache.cached(timeout=60, query_string=True)
@self.app.route('/api/summary')
def api_summary():
    # ... código existente ...
```

### 3.2 Agregar Compresión
```python
from flask_compress import Compress

# En __init__ de DashboardApp
Compress(self.app)
```

### 3.3 Logging Mejorado
```python
import logging
from logging.handlers import RotatingFileHandler

# Configurar logging específico para API
api_logger = logging.getLogger('dashboard_api')
handler = RotatingFileHandler('logs/dashboard_api.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
api_logger.addHandler(handler)
api_logger.setLevel(logging.INFO)
```

---

## Fase 4: Testing del Backend

### 4.1 Script de Testing
**Archivo**: `tests/test_dashboard_api.py` (NUEVO)

```python
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000/api'

def test_summary_endpoint():
    """Test endpoint /api/summary"""
    response = requests.get(f'{BASE_URL}/summary')
    assert response.status_code == 200

    data = response.json()
    assert 'success' in data
    assert 'data' in data

    summary = data['data']
    assert 'total_gastos' in summary
    assert 'total_monto' in summary
    assert 'monto_este_mes' in summary

def test_categories_endpoint():
    """Test endpoint /api/categories"""
    response = requests.get(f'{BASE_URL}/categories?days=30')
    assert response.status_code == 200

    data = response.json()
    assert 'success' in data
    assert 'data' in data

    categories = data['data']
    assert 'categories' in categories
    assert 'amounts' in categories
    assert isinstance(categories['categories'], list)

def test_timeline_endpoint():
    """Test endpoint /api/timeline"""
    response = requests.get(f'{BASE_URL}/timeline?days=7')
    assert response.status_code == 200

    data = response.json()
    timeline = data['data']
    assert 'dates' in timeline
    assert 'amounts' in timeline

def test_recent_endpoint():
    """Test endpoint /api/recent"""
    response = requests.get(f'{BASE_URL}/recent?limit=5')
    assert response.status_code == 200

    data = response.json()
    activities = data['data']
    assert isinstance(activities, list)
    assert len(activities) <= 5

def test_balance_endpoint():
    """Test endpoint /api/v2/balance"""
    response = requests.get(f'{BASE_URL}/v2/balance')
    assert response.status_code == 200

    data = response.json()
    balance = data['data']
    assert 'balance_total' in balance
    assert 'cambio_porcentual' in balance

def test_spending_endpoint():
    """Test endpoint /api/v2/spending"""
    response = requests.get(f'{BASE_URL}/v2/spending')
    assert response.status_code == 200

    data = response.json()
    spending = data['data']
    assert 'total_gastado' in spending
    assert 'limite_mensual' in spending
    assert 'porcentaje_usado' in spending

def test_search_endpoint():
    """Test endpoint /api/v2/search"""
    response = requests.get(f'{BASE_URL}/v2/search?query=comida&limit=10')
    assert response.status_code == 200

    data = response.json()
    assert 'count' in data
    assert isinstance(data['data'], list)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

### 4.2 Script para Poblar Datos de Prueba
**Archivo**: `scripts/seed_test_data.py` (NUEVO)

```python
"""Script para poblar datos de prueba en el dashboard."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.models.gasto import Gasto
from infrastructure.storage.excel_writer import ExcelStorage

CATEGORIAS = ['comida', 'transporte', 'entretenimiento', 'salud', 'servicios',
              'ropa', 'educacion', 'hogar', 'super', 'nafta']

DESCRIPCIONES = {
    'comida': ['Almuerzo', 'Cena', 'Desayuno', 'Snacks', 'Café'],
    'transporte': ['Uber', 'Taxi', 'Nafta', 'Estacionamiento', 'Peaje'],
    'entretenimiento': ['Cine', 'Streaming', 'Juegos', 'Salidas'],
    'salud': ['Farmacia', 'Médico', 'Gimnasio'],
    'super': ['Mercado', 'Almacén', 'Verdulería'],
}

def generate_test_gastos(num_dias=90, gastos_por_dia=3):
    """Genera gastos de prueba para últimos N días."""
    gastos = []
    now = datetime.now()

    for i in range(num_dias):
        fecha_base = now - timedelta(days=i)

        for j in range(random.randint(1, gastos_por_dia)):
            categoria = random.choice(CATEGORIAS)
            monto = Decimal(str(random.uniform(50, 5000))).quantize(Decimal('0.01'))

            # Hora aleatoria del día
            hora = random.randint(7, 22)
            minuto = random.randint(0, 59)
            fecha = fecha_base.replace(hour=hora, minute=minuto, second=0)

            # Descripción
            if categoria in DESCRIPCIONES:
                descripcion = random.choice(DESCRIPCIONES[categoria])
            else:
                descripcion = f"Gasto de {categoria}"

            gasto = Gasto(
                monto=monto,
                categoria=categoria,
                fecha=fecha,
                descripcion=descripcion
            )

            gastos.append(gasto)

    return gastos

def main():
    print("Generando datos de prueba...")

    # Crear storage
    excel_path = 'data/gastos.xlsx'
    storage = ExcelStorage(excel_path)

    # Generar y guardar gastos
    gastos = generate_test_gastos(num_dias=90, gastos_por_dia=4)

    print(f"Guardando {len(gastos)} gastos de prueba...")
    for gasto in gastos:
        storage.guardar_gasto(gasto)

    print(f"✅ {len(gastos)} gastos de prueba guardados en {excel_path}")

    # Mostrar estadísticas
    stats = storage.obtener_estadisticas()
    print(f"\nEstadísticas:")
    print(f"  - Total gastos: {stats['total_gastos']}")
    print(f"  - Monto total: ${stats['monto_total']:.2f}")
    print(f"  - Categorías: {len(stats['categorias'])}")

if __name__ == '__main__':
    main()
```

---

## Instalación y Ejecución

### Paso 1: Instalar Dependencias Opcionales
```bash
pip install flask-caching flask-compress
```

### Paso 2: Ejecutar Backend
```bash
python main.py --dashboard --port 5000
```

O directamente:
```bash
python interface/web/dashboard_app.py
```

### Paso 3: Generar Datos de Prueba (opcional)
```bash
python scripts/seed_test_data.py
```

### Paso 4: Ejecutar Tests
```bash
pytest tests/test_dashboard_api.py -v
```

---

## Checklist de Implementación

### ✅ Endpoints Existentes (Ya funcionan)
- [x] GET /api/summary
- [x] GET /api/categories
- [x] GET /api/timeline
- [x] GET /api/recent
- [x] GET /api/metrics
- [x] GET /api/refresh

### 🔄 Mejoras a Endpoints Existentes
- [ ] Mejorar /api/summary con comparaciones mes a mes
- [ ] Mejorar /api/categories con detalles (count, promedio, porcentaje)
- [ ] Agregar métodos faltantes en Storage (obtener_gastos_por_fecha, etc.)

### 🆕 Nuevos Endpoints v2
- [ ] GET /api/v2/balance - Balance consolidado
- [ ] GET /api/v2/spending - Info de gastos y límite
- [ ] GET /api/v2/trends - Tendencias y predicciones
- [ ] GET /api/v2/comparison - Comparación mes a mes
- [ ] GET /api/v2/search - Búsqueda avanzada
- [ ] GET /api/v2/export - Exportación de datos

### ⚡ Optimizaciones
- [ ] Implementar Flask-Caching
- [ ] Implementar Flask-Compress
- [ ] Mejorar logging específico para API
- [ ] Agregar rate limiting (opcional)

### 🧪 Testing
- [ ] Script de testing completo
- [ ] Script para generar datos de prueba
- [ ] Testing de performance con muchos registros

---

## Integración con Frontend

El frontend React se conectará a estos endpoints vía proxy configurado en Vite:

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  },
}
```

**Flujo de trabajo:**
1. Frontend corre en `http://localhost:3000`
2. Backend corre en `http://localhost:5000`
3. Frontend hace requests a `/api/*`
4. Vite proxy redirige a `http://localhost:5000/api/*`

---

## Próximos Pasos

1. **Implementar mejoras a endpoints existentes** (Fase 1)
2. **Crear nuevos endpoints v2** (Fase 2)
3. **Agregar optimizaciones** (Fase 3)
4. **Testing completo** (Fase 4)
5. **Documentar API** con ejemplos de uso
6. **Opcional**: Agregar autenticación/autorización para producción

---

**Documento creado**: 2025-10-29
**Estado**: Plan completo - Listo para implementar
**Dependencias**: Requiere que storage tenga métodos adicionales
**Tiempo estimado**: 8-10 horas de desarrollo
