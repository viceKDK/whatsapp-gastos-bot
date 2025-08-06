"""
Implementación Storage para SQLite

Guarda gastos en base de datos SQLite con funcionalidades avanzadas.
"""

import sqlite3
import os
from typing import List, Optional
from datetime import date, datetime
from pathlib import Path
from decimal import Decimal

from domain.models.gasto import Gasto
from shared.logger import get_logger


logger = get_logger(__name__)


class SQLiteStorage:
    """Implementación de storage usando SQLite."""
    
    def __init__(self, db_path: str):
        """
        Inicializa el storage de SQLite.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.logger = logger
        
        # Asegurar que el directorio existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear base de datos y tablas si no existen
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Inicializa la base de datos con las tablas necesarias."""
        try:
            self.logger.info(f"Inicializando base de datos SQLite: {self.db_path}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Crear tabla de gastos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gastos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monto DECIMAL(10, 2) NOT NULL,
                        categoria VARCHAR(50) NOT NULL,
                        descripcion TEXT,
                        fecha DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Crear índices para mejorar performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos(categoria)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_created_at ON gastos(created_at)')
                
                # Crear tabla de metadatos para versioning
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata (
                        key VARCHAR(50) PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insertar versión de esquema si no existe
                cursor.execute('''
                    INSERT OR IGNORE INTO metadata (key, value) 
                    VALUES ('schema_version', '1.0')
                ''')
                
                conn.commit()
                self.logger.info("Base de datos SQLite inicializada correctamente")
                
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos: {str(e)}")
            raise
    
    def guardar_gasto(self, gasto: Gasto) -> bool:
        """
        Guarda un gasto en la base de datos.
        
        Args:
            gasto: Gasto a guardar
            
        Returns:
            True si se guardó exitosamente, False si no
        """
        try:
            self.logger.debug(f"Guardando gasto en SQLite: {gasto}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO gastos (monto, categoria, descripcion, fecha)
                    VALUES (?, ?, ?, ?)
                ''', (
                    float(gasto.monto),
                    gasto.categoria,
                    gasto.descripcion,
                    gasto.fecha.isoformat()
                ))
                
                # Asignar el ID generado al gasto
                gasto.id = cursor.lastrowid
                
                conn.commit()
                
                self.logger.info(f"Gasto guardado en SQLite con ID {gasto.id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error guardando gasto en SQLite: {str(e)}")
            return False
    
    def obtener_gastos(self, fecha_desde: date, fecha_hasta: date) -> List[Gasto]:
        """
        Obtiene gastos en un rango de fechas.
        
        Args:
            fecha_desde: Fecha inicio
            fecha_hasta: Fecha fin
            
        Returns:
            Lista de gastos en el rango
        """
        try:
            self.logger.debug(f"Obteniendo gastos desde {fecha_desde} hasta {fecha_hasta}")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, monto, categoria, descripcion, fecha
                    FROM gastos
                    WHERE date(fecha) BETWEEN ? AND ?
                    ORDER BY fecha DESC
                ''', (fecha_desde.isoformat(), fecha_hasta.isoformat()))
                
                gastos = []
                for row in cursor.fetchall():
                    try:
                        gasto = Gasto(
                            monto=Decimal(str(row['monto'])),
                            categoria=row['categoria'],
                            fecha=datetime.fromisoformat(row['fecha']),
                            descripcion=row['descripcion']
                        )
                        gasto.id = row['id']
                        gastos.append(gasto)
                        
                    except Exception as e:
                        self.logger.warning(f"Error procesando gasto ID {row['id']}: {str(e)}")
                        continue
                
                self.logger.info(f"Obtenidos {len(gastos)} gastos de SQLite")
                return gastos
                
        except Exception as e:
            self.logger.error(f"Error obteniendo gastos de SQLite: {str(e)}")
            return []
    
    def obtener_gastos_por_categoria(self, categoria: str) -> List[Gasto]:
        """
        Obtiene todos los gastos de una categoría.
        
        Args:
            categoria: Nombre de la categoría
            
        Returns:
            Lista de gastos de la categoría
        """
        try:
            self.logger.debug(f"Obteniendo gastos de categoría: {categoria}")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, monto, categoria, descripcion, fecha
                    FROM gastos
                    WHERE LOWER(categoria) = LOWER(?)
                    ORDER BY fecha DESC
                ''', (categoria,))
                
                gastos = []
                for row in cursor.fetchall():
                    try:
                        gasto = Gasto(
                            monto=Decimal(str(row['monto'])),
                            categoria=row['categoria'],
                            fecha=datetime.fromisoformat(row['fecha']),
                            descripcion=row['descripcion']
                        )
                        gasto.id = row['id']
                        gastos.append(gasto)
                        
                    except Exception as e:
                        self.logger.warning(f"Error procesando gasto ID {row['id']}: {str(e)}")
                        continue
                
                self.logger.info(f"Encontrados {len(gastos)} gastos en categoría '{categoria}'")
                return gastos
                
        except Exception as e:
            self.logger.error(f"Error obteniendo gastos por categoría: {str(e)}")
            return []
    
    def obtener_gasto_por_id(self, gasto_id: int) -> Optional[Gasto]:
        """
        Obtiene un gasto específico por ID.
        
        Args:
            gasto_id: ID del gasto
            
        Returns:
            Gasto encontrado o None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, monto, categoria, descripcion, fecha
                    FROM gastos
                    WHERE id = ?
                ''', (gasto_id,))
                
                row = cursor.fetchone()
                if row:
                    gasto = Gasto(
                        monto=Decimal(str(row['monto'])),
                        categoria=row['categoria'],
                        fecha=datetime.fromisoformat(row['fecha']),
                        descripcion=row['descripcion']
                    )
                    gasto.id = row['id']
                    return gasto
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo gasto por ID {gasto_id}: {str(e)}")
            return None
    
    def actualizar_gasto(self, gasto: Gasto) -> bool:
        """
        Actualiza un gasto existente.
        
        Args:
            gasto: Gasto con datos actualizados
            
        Returns:
            True si se actualizó exitosamente, False si no
        """
        try:
            if not gasto.id:
                self.logger.error("No se puede actualizar gasto sin ID")
                return False
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE gastos 
                    SET monto = ?, categoria = ?, descripcion = ?, fecha = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    float(gasto.monto),
                    gasto.categoria,
                    gasto.descripcion,
                    gasto.fecha.isoformat(),
                    gasto.id
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Gasto ID {gasto.id} actualizado exitosamente")
                    return True
                else:
                    self.logger.warning(f"No se encontró gasto con ID {gasto.id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error actualizando gasto: {str(e)}")
            return False
    
    def eliminar_gasto(self, gasto_id: int) -> bool:
        """
        Elimina un gasto por ID.
        
        Args:
            gasto_id: ID del gasto a eliminar
            
        Returns:
            True si se eliminó exitosamente, False si no
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM gastos WHERE id = ?', (gasto_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Gasto ID {gasto_id} eliminado exitosamente")
                    return True
                else:
                    self.logger.warning(f"No se encontró gasto con ID {gasto_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error eliminando gasto: {str(e)}")
            return False
    
    def obtener_estadisticas(self) -> dict:
        """
        Obtiene estadísticas de gastos.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas generales
                cursor.execute('SELECT COUNT(*) as total, SUM(monto) as suma FROM gastos')
                general = cursor.fetchone()
                
                # Estadísticas por categoría
                cursor.execute('''
                    SELECT categoria, COUNT(*) as cantidad, SUM(monto) as total
                    FROM gastos
                    GROUP BY categoria
                    ORDER BY total DESC
                ''')
                categorias = {row[0]: {'cantidad': row[1], 'total': float(row[2])} for row in cursor.fetchall()}
                
                # Fechas de primer y último gasto
                cursor.execute('SELECT MIN(fecha) as primera, MAX(fecha) as ultima FROM gastos')
                fechas = cursor.fetchone()
                
                return {
                    'total_gastos': general[0] or 0,
                    'monto_total': float(general[1]) if general[1] else 0.0,
                    'categorias': categorias,
                    'fecha_primer_gasto': fechas[0],
                    'fecha_ultimo_gasto': fechas[1]
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'total_gastos': 0,
                'monto_total': 0.0,
                'categorias': {},
                'fecha_primer_gasto': None,
                'fecha_ultimo_gasto': None
            }
    
    def backup_database(self) -> str:
        """
        Crea un backup de la base de datos.
        
        Returns:
            Ruta del archivo backup creado
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.with_name(f"{self.db_path.stem}_backup_{timestamp}.db")
            
            if self.db_path.exists():
                import shutil
                shutil.copy2(self.db_path, backup_path)
                self.logger.info(f"Backup creado: {backup_path}")
                return str(backup_path)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error creando backup: {str(e)}")
            return ""
    
    def ejecutar_migrations(self) -> bool:
        """
        Ejecuta migraciones de base de datos si es necesario.
        
        Returns:
            True si las migraciones fueron exitosas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener versión actual del esquema
                cursor.execute('SELECT value FROM metadata WHERE key = "schema_version"')
                result = cursor.fetchone()
                current_version = result[0] if result else "0.0"
                
                self.logger.info(f"Versión actual del esquema: {current_version}")
                
                # Aquí se agregarían las migraciones según la versión
                if current_version == "1.0":
                    # Ya está actualizado
                    return True
                
                # Ejemplo de migración futura:
                # if current_version < "1.1":
                #     cursor.execute('ALTER TABLE gastos ADD COLUMN nueva_columna TEXT')
                #     cursor.execute('UPDATE metadata SET value = "1.1" WHERE key = "schema_version"')
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error ejecutando migraciones: {str(e)}")
            return False
    
    def vacuum_database(self) -> bool:
        """
        Optimiza la base de datos ejecutando VACUUM.
        
        Returns:
            True si la optimización fue exitosa
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('VACUUM')
                self.logger.info("Base de datos optimizada con VACUUM")
                return True
                
        except Exception as e:
            self.logger.error(f"Error ejecutando VACUUM: {str(e)}")
            return False
    
    def obtener_info_database(self) -> dict:
        """
        Obtiene información técnica de la base de datos.
        
        Returns:
            Diccionario con información de la BD
        """
        try:
            info = {
                'ruta': str(self.db_path),
                'exists': self.db_path.exists(),
                'size_bytes': 0,
                'tablas': []
            }
            
            if self.db_path.exists():
                info['size_bytes'] = self.db_path.stat().st_size
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Obtener lista de tablas
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    info['tablas'] = [row[0] for row in cursor.fetchall()]
                    
                    # Obtener versión del esquema
                    cursor.execute('SELECT value FROM metadata WHERE key = "schema_version"')
                    result = cursor.fetchone()
                    info['schema_version'] = result[0] if result else "desconocida"
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de base de datos: {str(e)}")
            return {'error': str(e)}