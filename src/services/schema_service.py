from abc import ABC, abstractmethod
from typing import List, Dict
import json
import os

class SchemaService(ABC):
    """Abstracción para manejo de esquemas - DIP"""
    
    @abstractmethod
    def get_table_schema(self) -> List[Dict]:
        pass


class JSONSchemaService(SchemaService):
    """Implementación para esquemas en JSON - SRP"""
    
    def __init__(self, schema_path: str):
        self.schema_path = schema_path
    
    def get_table_schema(self) -> List[Dict]:
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)


class SchemaFactory:
    """Factory para crear servicios de esquema - OCP"""
    
    @staticmethod
    def create_schema_service(schema_type: str = "json") -> SchemaService:
        if schema_type == "json":
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(current_dir, 'utils', 'Vis_Ventas..json')
            return JSONSchemaService(json_path)
        # Fácil agregar nuevos tipos: BigQuerySchemaService, etc.
        raise ValueError(f"Schema type {schema_type} not supported")