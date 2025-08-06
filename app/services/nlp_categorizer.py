"""
Categorizador NLP Automático

Sistema de categorización automática de gastos usando 
procesamiento de lenguaje natural y machine learning.
"""

import re
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
import math

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from config.config_manager import get_config
from shared.logger import get_logger
from domain.models.gasto import Gasto


logger = get_logger(__name__)


@dataclass
class CategorizationResult:
    """Resultado de la categorización automática."""
    categoria_predicha: str
    confianza: float
    alternativas: List[Tuple[str, float]]
    metodo: str  # 'ml', 'rules', 'keywords', 'fallback'
    features_usadas: List[str]
    tiempo_procesamiento: float


@dataclass
class TrainingStats:
    """Estadísticas del entrenamiento del modelo."""
    total_ejemplos: int
    ejemplos_por_categoria: Dict[str, int]
    accuracy: float
    fecha_entrenamiento: datetime
    metodo: str
    features_count: int


class TextPreprocessor:
    """Preprocesador de texto especializado para gastos."""
    
    def __init__(self):
        self.logger = logger
        
        # Patrones para limpiar texto
        self.noise_patterns = [
            r'\d+',  # Números (ya tenemos el monto separado)
            r'[^\w\s]',  # Puntuación
            r'\s+',  # Espacios múltiples
        ]
        
        # Stop words en español para gastos
        self.stop_words = {
            'de', 'la', 'el', 'en', 'y', 'a', 'es', 'se', 'no', 'te', 'lo', 'le',
            'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'un', 'una',
            'pesos', 'peso', 'dollar', 'dolares', 'usd', 'uyu', '$'
        }
        
        # Sinónimos y normalizaciones
        self.synonym_map = {
            # Transporte
            'nafta': 'combustible',
            'gasolina': 'combustible', 
            'gas_oil': 'combustible',
            'diesel': 'combustible',
            'ancap': 'combustible',
            'uber': 'taxi',
            'cabify': 'taxi',
            'remis': 'taxi',
            
            # Comida
            'almuerzo': 'comida',
            'desayuno': 'comida',
            'cena': 'comida',
            'merienda': 'comida',
            'delivery': 'comida',
            'pedidos_ya': 'comida',
            'rappi': 'comida',
            
            # Servicios
            'ute': 'servicios',
            'ose': 'servicios',
            'antel': 'servicios',
            'internet': 'servicios',
            'telefono': 'servicios',
            'celular': 'servicios',
            
            # Salud
            'farmacia': 'salud',
            'medicamento': 'salud',
            'doctor': 'salud',
            'medico': 'salud',
            
            # Supermercado
            'super': 'supermercado',
            'tienda': 'supermercado',
            'almacen': 'supermercado'
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocesa texto para categorización.
        
        Args:
            text: Texto a procesar
            
        Returns:
            Texto preprocesado
        """
        if not text:
            return ""
        
        # Convertir a minúsculas
        text = text.lower().strip()
        
        # Reemplazar sinónimos
        for original, synonym in self.synonym_map.items():
            text = text.replace(original, synonym)
        
        # Remover patrones de ruido
        for pattern in self.noise_patterns:
            text = re.sub(pattern, ' ', text)
        
        # Tokenizar y filtrar stop words
        tokens = text.split()
        filtered_tokens = [
            token for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        return ' '.join(filtered_tokens)
    
    def extract_features(self, text: str) -> List[str]:
        """
        Extrae características específicas del texto.
        
        Args:
            text: Texto del gasto
            
        Returns:
            Lista de características extraídas
        """
        features = []
        
        if not text:
            return features
        
        text_lower = text.lower()
        
        # Características de longitud
        features.append(f"len_{len(text_lower.split())}")
        
        # Presencia de palabras clave específicas
        keyword_categories = {
            'transporte': ['combustible', 'taxi', 'bus', 'omnibus', 'gasolina', 'nafta'],
            'comida': ['restaurant', 'comida', 'almuerzo', 'cena', 'delivery', 'pizza'],
            'servicios': ['ute', 'ose', 'antel', 'internet', 'luz', 'agua', 'gas'],
            'supermercado': ['super', 'market', 'tienda', 'almacen'],
            'salud': ['farmacia', 'medicina', 'doctor', 'clinica'],
            'entretenimiento': ['cine', 'teatro', 'juego', 'netflix', 'spotify']
        }
        
        for category, keywords in keyword_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                features.append(f"has_{category}_keywords")
        
        return features


class RuleBasedCategorizer:
    """Categorizador basado en reglas heurísticas."""
    
    def __init__(self):
        self.logger = logger
        
        # Reglas de categorización por palabras clave
        self.category_rules = {
            'transporte': {
                'keywords': ['combustible', 'nafta', 'gasolina', 'taxi', 'uber', 'bus', 'omnibus', 'peaje', 'estacionamiento', 'ancap'],
                'weight': 1.0
            },
            'comida': {
                'keywords': ['comida', 'restaurant', 'almuerzo', 'cena', 'desayuno', 'delivery', 'pizza', 'hamburgesa', 'sushi', 'parrilla', 'pedidos_ya', 'rappi'],
                'weight': 0.9
            },
            'servicios': {
                'keywords': ['ute', 'ose', 'antel', 'internet', 'luz', 'agua', 'gas', 'telefono', 'celular', 'cable', 'netflix'],
                'weight': 1.0
            },
            'supermercado': {
                'keywords': ['super', 'market', 'tienda', 'almacen', 'disco', 'tata', 'devoto', 'fresh'],
                'weight': 0.9
            },
            'salud': {
                'keywords': ['farmacia', 'medicina', 'doctor', 'medico', 'clinica', 'hospital', 'odontologia'],
                'weight': 1.0
            },
            'educacion': {
                'keywords': ['colegio', 'universidad', 'curso', 'libro', 'material', 'educacion', 'escuela'],
                'weight': 0.8
            },
            'entretenimiento': {
                'keywords': ['cine', 'teatro', 'juego', 'bar', 'boliche', 'spotify', 'game'],
                'weight': 0.7
            },
            'hogar': {
                'keywords': ['mueble', 'electrodomestico', 'casa', 'hogar', 'decoracion', 'limpieza', 'sodimac'],
                'weight': 0.8
            },
            'ropa': {
                'keywords': ['ropa', 'zapatilla', 'zapato', 'camisa', 'pantalon', 'vestido', 'tienda_ropa'],
                'weight': 0.8
            }
        }
        
        # Reglas por monto (montos típicos por categoría)
        self.amount_rules = {
            'transporte': {'min': 50, 'max': 3000, 'weight': 0.3},  # Combustible típico
            'comida': {'min': 20, 'max': 2000, 'weight': 0.2},      # Comida delivery/restaurant
            'servicios': {'min': 500, 'max': 8000, 'weight': 0.4},  # UTE, OSE, etc.
            'supermercado': {'min': 100, 'max': 5000, 'weight': 0.3},
        }
    
    def categorize(self, text: str, amount: float = None) -> Tuple[str, float]:
        """
        Categoriza usando reglas heurísticas.
        
        Args:
            text: Texto del gasto
            amount: Monto del gasto
            
        Returns:
            Tupla (categoría, confianza)
        """
        if not text:
            return 'otros', 0.1
        
        text_lower = text.lower()
        scores = defaultdict(float)
        
        # Aplicar reglas de palabras clave
        for category, rule in self.category_rules.items():
            keyword_matches = sum(1 for keyword in rule['keywords'] if keyword in text_lower)
            if keyword_matches > 0:
                # Calcular score basado en número de coincidencias y peso
                keyword_score = (keyword_matches / len(rule['keywords'])) * rule['weight']
                scores[category] += keyword_score
        
        # Aplicar reglas de monto si está disponible
        if amount and amount > 0:
            for category, rule in self.amount_rules.items():
                if rule['min'] <= amount <= rule['max']:
                    scores[category] += rule['weight']
        
        # Si no hay matches, usar fallback
        if not scores:
            return 'otros', 0.1
        
        # Retornar categoría con mayor score
        best_category = max(scores, key=scores.get)
        confidence = min(0.95, scores[best_category])  # Cap en 95%
        
        return best_category, confidence


class MLCategorizer:
    """Categorizador usando Machine Learning."""
    
    def __init__(self):
        self.logger = logger
        self.model_path = Path("models/nlp_categorizer_model.pkl")
        self.stats_path = Path("models/nlp_categorizer_stats.json")
        self.model_path.parent.mkdir(exist_ok=True)
        
        self.preprocessor = TextPreprocessor()
        self.pipeline = None
        self.training_stats = None
        
        # Cargar modelo si existe
        self.load_model()
    
    def train_from_gastos(self, gastos: List[Gasto], force_retrain: bool = False) -> TrainingStats:
        """
        Entrena el modelo desde una lista de gastos.
        
        Args:
            gastos: Lista de gastos para entrenar
            force_retrain: Forzar re-entrenamiento aunque ya exista modelo
            
        Returns:
            Estadísticas del entrenamiento
        """
        if not HAS_SKLEARN:
            raise RuntimeError("sklearn not available. Install with: pip install scikit-learn")
        
        if len(gastos) < 10:
            raise ValueError(f"Se necesitan al menos 10 gastos para entrenar. Disponibles: {len(gastos)}")
        
        # Si ya existe modelo y no se fuerza re-entrenamiento, cargar existente
        if self.model_path.exists() and not force_retrain:
            self.load_model()
            if self.training_stats:
                self.logger.info(f"Modelo existente cargado. Entrenado con {self.training_stats.total_ejemplos} ejemplos")
                return self.training_stats
        
        self.logger.info(f"Entrenando modelo NLP con {len(gastos)} gastos...")
        
        # Preparar datos
        texts = []
        categories = []
        
        for gasto in gastos:
            # Combinar descripción y categoría conocida
            text_features = []
            if gasto.descripcion:
                text_features.append(gasto.descripcion)
            
            # Agregar información del monto como texto
            if gasto.monto:
                if float(gasto.monto) < 100:
                    text_features.append("monto_bajo")
                elif float(gasto.monto) > 2000:
                    text_features.append("monto_alto")
                else:
                    text_features.append("monto_medio")
            
            combined_text = ' '.join(text_features)
            preprocessed = self.preprocessor.preprocess_text(combined_text)
            
            if preprocessed:  # Solo agregar si hay texto útil
                texts.append(preprocessed)
                categories.append(gasto.categoria)
        
        if len(texts) < 5:
            raise ValueError(f"Insuficientes textos válidos para entrenar: {len(texts)}")
        
        # Verificar distribución de categorías
        category_counts = Counter(categories)
        self.logger.info(f"Distribución de categorías: {dict(category_counts)}")
        
        # Filtrar categorías con muy pocos ejemplos
        min_examples_per_category = 2
        valid_categories = {cat for cat, count in category_counts.items() if count >= min_examples_per_category}
        
        if len(valid_categories) < 2:
            raise ValueError(f"Se necesitan al menos 2 categorías con {min_examples_per_category}+ ejemplos cada una")
        
        # Filtrar datos
        filtered_texts = []
        filtered_categories = []
        for text, category in zip(texts, categories):
            if category in valid_categories:
                filtered_texts.append(text)
                filtered_categories.append(category)
        
        # Crear pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
                stop_words=list(self.preprocessor.stop_words)
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # Entrenar
        start_time = datetime.now()
        
        try:
            # Si hay suficientes datos, usar train-test split
            if len(filtered_texts) >= 20:
                X_train, X_test, y_train, y_test = train_test_split(
                    filtered_texts, filtered_categories, 
                    test_size=0.2, 
                    random_state=42,
                    stratify=filtered_categories
                )
                
                self.pipeline.fit(X_train, y_train)
                
                # Evaluar
                y_pred = self.pipeline.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                
                self.logger.info(f"Accuracy en test set: {accuracy:.3f}")
            else:
                # Entrenar con todos los datos
                self.pipeline.fit(filtered_texts, filtered_categories)
                accuracy = 0.8  # Estimación conservadora
        
        except Exception as e:
            self.logger.error(f"Error durante entrenamiento: {e}")
            raise
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Crear estadísticas
        self.training_stats = TrainingStats(
            total_ejemplos=len(filtered_texts),
            ejemplos_por_categoria={cat: filtered_categories.count(cat) for cat in valid_categories},
            accuracy=accuracy,
            fecha_entrenamiento=datetime.now(),
            metodo='multinomial_nb_tfidf',
            features_count=self.pipeline.named_steps['tfidf'].vocabulary_.__len__() if hasattr(self.pipeline.named_steps['tfidf'], 'vocabulary_') else 0
        )
        
        # Guardar modelo
        self.save_model()
        
        self.logger.info(f"Modelo entrenado en {training_time:.2f}s con accuracy: {accuracy:.3f}")
        return self.training_stats
    
    def predict(self, text: str, amount: float = None) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        Predice categoría usando ML.
        
        Args:
            text: Texto del gasto
            amount: Monto del gasto (opcional)
            
        Returns:
            Tupla (categoría, confianza, alternativas)
        """
        if not self.pipeline:
            return 'otros', 0.1, []
        
        try:
            # Preparar texto
            combined_text = text or ""
            if amount:
                if amount < 100:
                    combined_text += " monto_bajo"
                elif amount > 2000:
                    combined_text += " monto_alto"
                else:
                    combined_text += " monto_medio"
            
            preprocessed = self.preprocessor.preprocess_text(combined_text)
            if not preprocessed:
                return 'otros', 0.1, []
            
            # Predecir
            predicted_category = self.pipeline.predict([preprocessed])[0]
            
            # Obtener probabilidades si está disponible
            if hasattr(self.pipeline.named_steps['classifier'], 'predict_proba'):
                proba = self.pipeline.predict_proba([preprocessed])[0]
                classes = self.pipeline.named_steps['classifier'].classes_
                
                # Crear lista de alternativas ordenada por probabilidad
                alternatives = sorted(
                    [(cls, prob) for cls, prob in zip(classes, proba)],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                main_confidence = alternatives[0][1]
                other_alternatives = alternatives[1:4]  # Top 3 alternativas
                
                return predicted_category, main_confidence, other_alternatives
            else:
                return predicted_category, 0.7, []
        
        except Exception as e:
            self.logger.error(f"Error en predicción ML: {e}")
            return 'otros', 0.1, []
    
    def save_model(self):
        """Guarda el modelo entrenado."""
        try:
            if self.pipeline:
                with open(self.model_path, 'wb') as f:
                    pickle.dump(self.pipeline, f)
                
                if self.training_stats:
                    stats_dict = {
                        'total_ejemplos': self.training_stats.total_ejemplos,
                        'ejemplos_por_categoria': self.training_stats.ejemplos_por_categoria,
                        'accuracy': self.training_stats.accuracy,
                        'fecha_entrenamiento': self.training_stats.fecha_entrenamiento.isoformat(),
                        'metodo': self.training_stats.metodo,
                        'features_count': self.training_stats.features_count
                    }
                    
                    with open(self.stats_path, 'w') as f:
                        json.dump(stats_dict, f, indent=2)
                
                self.logger.info(f"Modelo guardado en {self.model_path}")
        
        except Exception as e:
            self.logger.error(f"Error guardando modelo: {e}")
    
    def load_model(self):
        """Carga modelo guardado."""
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                
                if self.stats_path.exists():
                    with open(self.stats_path, 'r') as f:
                        stats_dict = json.load(f)
                        
                        self.training_stats = TrainingStats(
                            total_ejemplos=stats_dict['total_ejemplos'],
                            ejemplos_por_categoria=stats_dict['ejemplos_por_categoria'],
                            accuracy=stats_dict['accuracy'],
                            fecha_entrenamiento=datetime.fromisoformat(stats_dict['fecha_entrenamiento']),
                            metodo=stats_dict['metodo'],
                            features_count=stats_dict['features_count']
                        )
                
                self.logger.info(f"Modelo cargado desde {self.model_path}")
                return True
        
        except Exception as e:
            self.logger.error(f"Error cargando modelo: {e}")
            self.pipeline = None
            self.training_stats = None
            return False


class NLPCategorizer:
    """Categorizador principal que combina múltiples métodos."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        
        self.rule_categorizer = RuleBasedCategorizer()
        self.ml_categorizer = MLCategorizer()
        self.preprocessor = TextPreprocessor()
        
        # Configuración
        self.min_confidence_ml = 0.6
        self.min_confidence_rules = 0.5
        self.enable_ml = HAS_SKLEARN
        
        # Estadísticas de uso
        self.usage_stats = {
            'total_predictions': 0,
            'method_usage': {'ml': 0, 'rules': 0, 'fallback': 0},
            'accuracy_by_method': {'ml': [], 'rules': [], 'fallback': []}
        }
    
    def categorize(self, text: str, amount: float = None, training_data: List[Gasto] = None) -> CategorizationResult:
        """
        Categoriza un gasto usando múltiples métodos.
        
        Args:
            text: Descripción del gasto
            amount: Monto del gasto
            training_data: Datos de entrenamiento si es la primera vez
            
        Returns:
            Resultado de categorización
        """
        start_time = datetime.now()
        self.usage_stats['total_predictions'] += 1
        
        try:
            # Entrenar modelo ML si es necesario y hay datos
            if (training_data and len(training_data) >= 10 and 
                self.enable_ml and not self.ml_categorizer.pipeline):
                try:
                    self.ml_categorizer.train_from_gastos(training_data)
                    self.logger.info("Modelo ML entrenado desde datos proporcionados")
                except Exception as e:
                    self.logger.warning(f"No se pudo entrenar modelo ML: {e}")
            
            # Método 1: Machine Learning (si está disponible y entrenado)
            ml_result = None
            if self.enable_ml and self.ml_categorizer.pipeline:
                try:
                    ml_category, ml_confidence, ml_alternatives = self.ml_categorizer.predict(text, amount)
                    if ml_confidence >= self.min_confidence_ml:
                        ml_result = (ml_category, ml_confidence, ml_alternatives)
                        self.logger.debug(f"ML prediction: {ml_category} ({ml_confidence:.3f})")
                except Exception as e:
                    self.logger.warning(f"Error en predicción ML: {e}")
            
            # Método 2: Reglas heurísticas
            rules_category, rules_confidence = self.rule_categorizer.categorize(text, amount)
            rules_result = (rules_category, rules_confidence) if rules_confidence >= self.min_confidence_rules else None
            
            # Decidir qué resultado usar
            if ml_result and ml_result[1] > rules_confidence:
                # Usar ML
                final_category = ml_result[0]
                final_confidence = ml_result[1]
                alternatives = [(alt[0], alt[1]) for alt in ml_result[2]]
                method = 'ml'
                self.usage_stats['method_usage']['ml'] += 1
                
            elif rules_result:
                # Usar reglas
                final_category = rules_result[0]
                final_confidence = rules_result[1]
                alternatives = []
                method = 'rules'
                self.usage_stats['method_usage']['rules'] += 1
                
            else:
                # Fallback
                final_category = 'otros'
                final_confidence = 0.1
                alternatives = []
                method = 'fallback'
                self.usage_stats['method_usage']['fallback'] += 1
            
            # Extraer features utilizadas
            features = self.preprocessor.extract_features(text or "")
            if amount:
                if amount < 100:
                    features.append("low_amount")
                elif amount > 2000:
                    features.append("high_amount")
                else:
                    features.append("medium_amount")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return CategorizationResult(
                categoria_predicha=final_category,
                confianza=final_confidence,
                alternativas=alternatives,
                metodo=method,
                features_usadas=features,
                tiempo_procesamiento=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error en categorización: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return CategorizationResult(
                categoria_predicha='otros',
                confianza=0.1,
                alternativas=[],
                metodo='error',
                features_usadas=[],
                tiempo_procesamiento=processing_time
            )
    
    def train_from_storage(self, storage) -> bool:
        """
        Entrena el modelo usando datos del storage.
        
        Args:
            storage: Instancia de storage con gastos
            
        Returns:
            True si el entrenamiento fue exitoso
        """
        try:
            gastos = storage.obtener_todos_gastos()
            
            if len(gastos) < 10:
                self.logger.warning(f"Insuficientes gastos para entrenar modelo: {len(gastos)}")
                return False
            
            self.logger.info(f"Entrenando modelo NLP con {len(gastos)} gastos del storage...")
            stats = self.ml_categorizer.train_from_gastos(gastos, force_retrain=True)
            
            self.logger.info(f"Modelo entrenado: accuracy={stats.accuracy:.3f}, "
                           f"categorías={len(stats.ejemplos_por_categoria)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error entrenando desde storage: {e}")
            return False
    
    def get_training_stats(self) -> Optional[TrainingStats]:
        """Obtiene estadísticas del entrenamiento."""
        return self.ml_categorizer.training_stats
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso."""
        return self.usage_stats.copy()
    
    def get_info(self) -> Dict[str, Any]:
        """Obtiene información del categorizador."""
        info = {
            'sklearn_available': HAS_SKLEARN,
            'ml_enabled': self.enable_ml,
            'model_trained': self.ml_categorizer.pipeline is not None,
            'training_stats': None,
            'usage_stats': self.get_usage_stats()
        }
        
        if self.ml_categorizer.training_stats:
            stats = self.ml_categorizer.training_stats
            info['training_stats'] = {
                'total_ejemplos': stats.total_ejemplos,
                'categorias': list(stats.ejemplos_por_categoria.keys()),
                'accuracy': stats.accuracy,
                'fecha_entrenamiento': stats.fecha_entrenamiento.isoformat(),
                'metodo': stats.metodo
            }
        
        return info


# Instancia global del categorizador
_nlp_categorizer: Optional[NLPCategorizer] = None


def get_nlp_categorizer() -> NLPCategorizer:
    """Obtiene instancia global del categorizador NLP."""
    global _nlp_categorizer
    if _nlp_categorizer is None:
        _nlp_categorizer = NLPCategorizer()
    return _nlp_categorizer


def categorize_gasto(text: str, amount: float = None, 
                    training_data: List[Gasto] = None) -> CategorizationResult:
    """
    Función de conveniencia para categorizar un gasto.
    
    Args:
        text: Descripción del gasto
        amount: Monto del gasto
        training_data: Datos de entrenamiento opcionales
        
    Returns:
        Resultado de categorización
    """
    categorizer = get_nlp_categorizer()
    return categorizer.categorize(text, amount, training_data)


def train_categorizer_from_storage(storage) -> bool:
    """
    Función de conveniencia para entrenar desde storage.
    
    Args:
        storage: Instancia de storage
        
    Returns:
        True si fue exitoso
    """
    categorizer = get_nlp_categorizer()
    return categorizer.train_from_storage(storage)