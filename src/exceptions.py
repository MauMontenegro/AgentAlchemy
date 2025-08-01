from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class AgentAlchemyException(Exception):
    """Base exception for AgentAlchemy"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(AgentAlchemyException):
    """Authentication related errors"""
    pass

class AuthorizationError(AgentAlchemyException):
    """Authorization related errors"""
    pass

class AgentProcessingError(AgentAlchemyException):
    """Agent processing errors"""
    pass

class DatabaseError(AgentAlchemyException):
    """Database related errors"""
    pass

class ConfigurationError(AgentAlchemyException):
    """Configuration related errors"""
    pass

def create_http_exception(exc: AgentAlchemyException) -> HTTPException:
    """Convert custom exceptions to HTTP exceptions"""
    status_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        AgentProcessingError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(status_code=status_code, detail=exc.message)