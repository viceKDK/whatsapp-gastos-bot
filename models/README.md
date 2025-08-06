# Modelos de Machine Learning

Este directorio contiene los modelos entrenados para la categorización automática de gastos.

## Archivos generados automáticamente:

- `nlp_categorizer_model.pkl` - Modelo entrenado (Naive Bayes + TF-IDF)
- `nlp_categorizer_stats.json` - Estadísticas del entrenamiento

## Cómo entrenar el modelo:

```python
from app.services.nlp_categorizer import get_nlp_categorizer

# Obtener categorizador
categorizer = get_nlp_categorizer()

# Entrenar con gastos existentes
gastos = storage.obtener_todos_gastos()  # Desde tu storage
stats = categorizer.ml_categorizer.train_from_gastos(gastos)

print(f"Modelo entrenado con accuracy: {stats.accuracy:.1%}")
```

## Usar el modelo:

```python
from app.services.nlp_categorizer import categorize_gasto

resultado = categorize_gasto("pizza delivery casa", 400)
print(f"Categoría: {resultado.categoria_predicha}")
print(f"Confianza: {resultado.confianza:.1%}")
```

## Notas:

- Los modelos se guardan automáticamente después del entrenamiento
- Se requiere un mínimo de 10 gastos para entrenar
- El modelo mejora con más datos de entrenamiento
- Los archivos .pkl no deben ser committeados al repositorio por su tamaño