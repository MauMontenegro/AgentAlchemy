from typing import Dict, List, Set
import json
from langchain_aws import ChatBedrockConverse


class IntentAnalysisService:
    """Servicio para análisis de intención y selección de tablas usando LLM"""
    
    def __init__(self, llm_client: ChatBedrockConverse):
        self.llm_client = llm_client
    
    async def analyze_query_intent(self, query: str, available_tables: Dict[str, Dict], table_schemas: Dict[str, List[Dict]] = None) -> Dict:
        """Analiza la intención de la consulta y determina tablas/campos necesarios"""
        
        template = self._get_intent_analysis_template()
        
        response = await self.llm_client.ainvoke(
            template.format(
                query=query,
                tables_info=self._format_tables_info(available_tables),
                schemas_info=self._format_schemas_info(table_schemas or {})
            )
        )
        
        print(f"[INTENT ANALYSIS] Query: {query}")
        print(f"[INTENT ANALYSIS] Raw Response: {response.content}")
        
        try:
            # Limpiar respuesta antes del parsing
            clean_response = self._clean_json_response(response.content.strip())
            print(f"[INTENT ANALYSIS] Clean Response: {clean_response}")
            
            result = json.loads(clean_response)
            print(f"[INTENT ANALYSIS] Parsed Result: {result}")
            return result
        except json.JSONDecodeError as e:
            fallback = {
                "required_tables": ["Vis_Ventas"],
                "primary_intent": "ventas",
                "required_fields": [],
                "confidence": 0.5
            }
            print(f"[INTENT ANALYSIS] JSON Error: {e}")
            print(f"[INTENT ANALYSIS] Using Fallback: {fallback}")
            return fallback
    
    def _get_intent_analysis_template(self) -> str:
        return """
        Analiza la siguiente consulta y determina qué tablas y campos son necesarios para responderla.

        CONSULTA: {query}

        TABLAS DISPONIBLES:
        {tables_info}

        ESQUEMAS DE CAMPOS:
        {schemas_info}

        Responde ÚNICAMENTE con un JSON válido con esta estructura:
        {{
            "required_tables": ["tabla1", "tabla2"],
            "primary_intent": "descripción_breve_intención",
            "required_fields": ["campo1", "campo2"],
            "confidence": 0.9
        }}

        REGLAS:
        - Si la consulta es sobre ventas/facturación/productos: usar Vis_Ventas
        - Si es sobre saldos/cartera/documentos pendientes: usar vis_CarteraClientes  
        - Si es sobre pagos/conciliaciones/movimientos: usar IngresosClientes
        - En required_fields usa SOLO nombres de campos que existen en los esquemas
        - Si necesitas información de múltiples conceptos, incluye múltiples tablas
        - confidence debe ser entre 0.0 y 1.0
        """
    
    def _clean_json_response(self, response: str) -> str:
        """Limpia la respuesta del LLM para extraer solo el JSON"""
        # Remover markdown code blocks
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
        
        # Buscar el primer { y último }
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start != -1 and end > start:
            return response[start:end]
        
        return response.strip()
    
    def _format_tables_info(self, tables: Dict[str, Dict]) -> str:
        """Formatea información de tablas para el prompt"""
        formatted = []
        for table_name, table_info in tables.items():
            description = table_info.get('description', 'Sin descripción')
            formatted.append(f"- {table_name}: {description}")
        return "\n".join(formatted)
    
    def _format_schemas_info(self, schemas: Dict[str, List[Dict]]) -> str:
        """Formatea los esquemas de campos para el prompt"""
        if not schemas:
            return "No hay esquemas disponibles"
        
        formatted = []
        for table_name, fields in schemas.items():
            formatted.append(f"\n{table_name}:")
            for field in fields[:10]:  # Limitar a 10 campos más relevantes
                formatted.append(f"  - {field['name']} ({field['type']}): {field['description']}")
        return "\n".join(formatted)