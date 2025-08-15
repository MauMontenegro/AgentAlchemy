# Configuración de Reglas de Negocio

Este directorio contiene los archivos de configuración que permiten modificar las reglas de negocio sin tocar el código.

## Archivos de Configuración

### business_rules.json
Contiene las reglas de interpretación de consultas, filtros automáticos y reglas de contexto.

#### Estructura:

```json
{
    "query_interpretation": [
        {
            "pattern": "regex_pattern",
            "transformation": "descripción de la transformación",
            "exclude_companies": ["lista", "de", "empresas"],
            "exclude_categories": ["lista", "de", "categorías"],
            "exclude_types": ["lista", "de", "tipos"],
            "description": "descripción de la regla"
        }
    ],
    "auto_filters": [
        {
            "condition": "palabra_clave",
            "filters": {
                "exclude_companies": ["empresas", "a", "excluir"],
                "exclude_status": ["estados", "a", "excluir"],
                "min_amount": 0
            }
        }
    ],
    "context_rules": [
        {
            "trigger": "regex_pattern",
            "additional_context": "contexto adicional para el LLM",
            "required_fields": ["campos", "requeridos"]
        }
    ]
}
```

## Cómo Agregar Nuevas Reglas

### 1. Reglas de Interpretación de Consultas
Para agregar una nueva regla que transforme cómo se interpreta una consulta:

```json
{
    "pattern": "(?i).*nueva.*consulta.*",
    "transformation": "interpretación específica de la consulta",
    "exclude_companies": ["Empresa X"],
    "description": "Descripción de qué hace esta regla"
}
```

### 2. Filtros Automáticos
Para agregar filtros que se apliquen automáticamente:

```json
{
    "condition": "palabra_clave_en_consulta",
    "filters": {
        "exclude_status": ["INACTIVO"],
        "min_amount": 1000
    }
}
```

### 3. Reglas de Contexto
Para agregar contexto adicional al LLM:

```json
{
    "trigger": "(?i).*análisis.*detallado.*",
    "additional_context": "Proporcionar análisis detallado con métricas adicionales",
    "required_fields": ["campo1", "campo2"]
}
```

## Recarga de Configuración

Las reglas se pueden recargar sin reiniciar la aplicación usando el método `reload_rules()` del servicio.

## Patrones Regex Comunes

- `(?i)` - Insensible a mayúsculas/minúsculas
- `.*` - Cualquier carácter, cualquier cantidad
- `\\b` - Límite de palabra
- `|` - OR lógico

Ejemplos:
- `(?i).*ventas.*total.*` - Coincide con "ventas total", "Total de Ventas", etc.
- `(?i)\\b(cliente|clientes)\\b` - Coincide exactamente con "cliente" o "clientes"