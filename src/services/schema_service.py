from abc import ABC, abstractmethod
from typing import List, Dict, Set
import json
import os
import re

class SchemaService(ABC):
    """Abstracción para manejo de esquemas - DIP"""
    
    @abstractmethod
    async def get_relevant_schemas(self, query: str, intent_service=None) -> Dict[str, List[Dict]]:
        pass
    
    @abstractmethod
    def get_table_relationships(self) -> Dict:
        pass


class MultiTableSchemaService(SchemaService):
    """Servicio para manejar múltiples tablas y sus relaciones"""
    
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.table_schemas = self._load_all_schemas()
        self.relationships = self._load_relationships()
    
    def _load_all_schemas(self) -> Dict[str, List[Dict]]:
        """Carga todos los esquemas disponibles"""
        schemas = {}
        schema_files = {
            'Vis_Ventas': 'Vis_Ventas..json',
            'vis_CarteraClientes': 'vis_CarteraClientes.json', 
            'IngresosClientes': 'IngresosClientes.json'
        }
        
        for table_name, filename in schema_files.items():
            file_path = os.path.join(self.utils_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    schemas[table_name] = json.load(f)
        
        return schemas
    
    def _load_relationships(self) -> Dict:
        """Carga las relaciones entre tablas"""
        rel_path = os.path.join(self.utils_dir, 'table_relationships.json')
        if os.path.exists(rel_path):
            with open(rel_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    async def get_relevant_schemas(self, query: str, intent_service=None) -> Dict[str, List[Dict]]:
        """Determina qué tablas son relevantes usando análisis de intención"""
        if intent_service:
            # Usar análisis de intención con LLM
            intent_analysis = await intent_service.analyze_query_intent(
                query, 
                self.relationships.get('tables', {}),
                self.table_schemas
            )
            required_tables = set(intent_analysis.get('required_tables', ['Vis_Ventas']))
        else:
            # Fallback a detección por palabras clave
            required_tables = self._keyword_based_detection(query)
        
        # Expandir tablas relacionadas si es necesario
        if len(required_tables) > 1:
            required_tables = self._expand_related_tables(required_tables)
        
        return {table: self.table_schemas[table] for table in required_tables if table in self.table_schemas}
    
    def _keyword_based_detection(self, query: str) -> Set[str]:
        """Método fallback de detección por palabras clave"""
        query_lower = query.lower()
        relevant_tables = set()
        
        table_keywords = {
            'Vis_Ventas': ['venta', 'ventas', 'factura', 'producto', 'cliente', 'vendedor', 'estacion', 'remision'],
            'vis_CarteraClientes': ['cartera', 'credito', 'saldo', 'vencimiento', 'limite', 'documento', 'vencido'],
            'IngresosClientes': ['pago', 'pagos', 'contado', 'conciliacion', 'movimiento', 'aplicado', 'identificada']
        }
        
        for table, keywords in table_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                relevant_tables.add(table)
        
        return relevant_tables if relevant_tables else {'Vis_Ventas'}
    
    def _expand_related_tables(self, tables: Set[str]) -> Set[str]:
        """Expande el conjunto de tablas para incluir las relacionadas"""
        expanded = set(tables)
        
        # Agregar tablas relacionadas basado en las relaciones definidas
        for rel in self.relationships.get('relationships', []):
            from_table = rel['from_table']
            to_table = rel['to_table']
            
            if from_table in tables and to_table in self.table_schemas:
                expanded.add(to_table)
            if to_table in tables and from_table in self.table_schemas:
                expanded.add(from_table)
        
        return expanded
    
    def get_table_relationships(self) -> Dict:
        """Retorna las relaciones entre tablas"""
        return self.relationships


class JSONSchemaService(SchemaService):
    """Implementación legacy para compatibilidad"""
    
    def __init__(self, schema_path: str):
        self.schema_path = schema_path
    
    async def get_relevant_schemas(self, query: str, intent_service=None) -> Dict[str, List[Dict]]:
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            return {'Vis_Ventas': json.load(f)}
    
    def get_table_relationships(self) -> Dict:
        return {}


class SchemaFactory:
    """Factory para crear servicios de esquema - OCP"""
    
    @staticmethod
    def create_schema_service(schema_type: str = "multi_table") -> SchemaService:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        utils_dir = os.path.join(current_dir, 'utils')
        
        if schema_type == "multi_table":
            return MultiTableSchemaService(utils_dir)
        elif schema_type == "json":
            json_path = os.path.join(utils_dir, 'Vis_Ventas..json')
            return JSONSchemaService(json_path)
        
        raise ValueError(f"Schema type {schema_type} not supported")