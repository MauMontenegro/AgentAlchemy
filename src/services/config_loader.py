import json
import os
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Servicio para cargar configuraciones desde archivos JSON"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # Usar directorio config relativo al archivo actual
            current_dir = Path(__file__).parent.parent
            self.config_dir = current_dir / "config"
        else:
            self.config_dir = Path(config_dir)
    
    def load_business_rules(self) -> Dict[str, Any]:
        """Carga las reglas de negocio desde el archivo JSON"""
        rules_file = self.config_dir / "business_rules.json"
        return self._load_json_file(rules_file)
    
    def load_table_relationships(self) -> Dict[str, Any]:
        """Carga las relaciones de tablas desde el archivo JSON"""
        relationships_file = self.config_dir.parent / "utils" / "table_relationships.json"
        return self._load_json_file(relationships_file)
    
    def load_sql_templates(self) -> Dict[str, Any]:
        """Carga los templates SQL desde el archivo JSON"""
        templates_file = self.config_dir / "sql_templates.json"
        return self._load_json_file(templates_file)
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Carga un archivo JSON y retorna su contenido"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Archivo de configuración no encontrado: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error al parsear JSON en {file_path}: {e}")
            return {}
    
    def reload_config(self) -> bool:
        """Recarga todas las configuraciones"""
        try:
            # Verificar que los archivos existan y sean válidos
            self.load_business_rules()
            self.load_table_relationships()
            self.load_sql_templates()
            return True
        except Exception as e:
            print(f"Error al recargar configuración: {e}")
            return False