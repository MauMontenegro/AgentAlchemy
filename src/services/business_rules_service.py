from typing import Dict, List, Optional
import re
from .config_loader import ConfigLoader


class BusinessRulesService:
    """Servicio para aplicar reglas específicas del negocio a las consultas"""
    
    def __init__(self, config_loader: ConfigLoader = None):
        self.config_loader = config_loader or ConfigLoader()
        self.rules = self._load_business_rules()
    
    def _load_business_rules(self) -> Dict:
        """Carga las reglas de negocio desde archivo de configuración"""
        return self.config_loader.load_business_rules()
    
    def apply_business_rules(self, user_query: str) -> Dict:
        """Aplica las reglas de negocio a una consulta del usuario"""
        result = {
            "original_query": user_query,
            "transformed_query": user_query,
            "filters_to_apply": [],
            "additional_context": [],
            "excluded_entities": []
        }
        
        # Aplicar reglas de interpretación
        for rule in self.rules["query_interpretation"]:
            if re.search(rule["pattern"], user_query):
                result["transformed_query"] = rule["transformation"]
                
                # Agregar exclusiones específicas
                if "exclude_companies" in rule:
                    result["excluded_entities"].extend(rule["exclude_companies"])
                if "exclude_categories" in rule:
                    result["excluded_entities"].extend(rule["exclude_categories"])
                if "exclude_types" in rule:
                    result["excluded_entities"].extend(rule["exclude_types"])
                
                result["additional_context"].append(rule["description"])
                break
        
        # Aplicar filtros automáticos
        for rule in self.rules["auto_filters"]:
            if rule["condition"].lower() in user_query.lower():
                result["filters_to_apply"].append(rule["filters"])
        
        # Aplicar reglas de contexto
        for rule in self.rules["context_rules"]:
            if re.search(rule["trigger"], user_query):
                result["additional_context"].append(rule["additional_context"])
                if "required_fields" in rule:
                    result["required_fields"] = rule.get("required_fields", [])
        
        return result
    
    def get_sql_filters(self, business_rules_result: Dict) -> str:
        """Genera filtros SQL basados en las reglas de negocio aplicadas"""
        filters = []
        
        # Procesar exclusiones de entidades
        if business_rules_result["excluded_entities"]:
            excluded = "', '".join(business_rules_result["excluded_entities"])
            filters.append(f"AND nombre_empresa NOT IN ('{excluded}')")
        
        # Procesar filtros automáticos
        for filter_rule in business_rules_result["filters_to_apply"]:
            if "exclude_companies" in filter_rule:
                excluded = "', '".join(filter_rule["exclude_companies"])
                filters.append(f"AND nombre_empresa NOT IN ('{excluded}')")
            
            if "exclude_status" in filter_rule:
                excluded = "', '".join(filter_rule["exclude_status"])
                filters.append(f"AND estado NOT IN ('{excluded}')")
            
            if "min_amount" in filter_rule:
                filters.append(f"AND valor > {filter_rule['min_amount']}")
        
        return " ".join(filters)
    
    def add_custom_rule(self, rule_type: str, rule_data: Dict):
        """Permite agregar reglas personalizadas dinámicamente"""
        if rule_type not in self.rules:
            self.rules[rule_type] = []
        
        self.rules[rule_type].append(rule_data)
    
    def reload_rules(self):
        """Recarga las reglas desde el archivo de configuración"""
        self.rules = self._load_business_rules()
    
    def get_business_context(self, business_rules_result: Dict) -> str:
        """Genera contexto adicional para el LLM basado en las reglas aplicadas"""
        context_parts = []
        
        if business_rules_result["additional_context"]:
            context_parts.append("REGLAS DE NEGOCIO APLICADAS:")
            for context in business_rules_result["additional_context"]:
                context_parts.append(f"- {context}")
        
        if business_rules_result["excluded_entities"]:
            context_parts.append(f"ENTIDADES EXCLUIDAS: {', '.join(business_rules_result['excluded_entities'])}")
        
        if business_rules_result["transformed_query"] != business_rules_result["original_query"]:
            context_parts.append(f"CONSULTA INTERPRETADA COMO: {business_rules_result['transformed_query']}")
        
        return "\n".join(context_parts)