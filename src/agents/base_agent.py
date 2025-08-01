from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph
from ..logger import get_logger

logger = get_logger(__name__)

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.graph = self._build_graph()
    
    @abstractmethod
    def _build_graph(self) -> StateGraph:
        """Build the agent's state graph"""
        pass
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the agent request"""
        pass
    
    def validate_state(self, state: Dict[str, Any], required_keys: list[str]) -> None:
        """Validate required keys in state"""
        missing_keys = [key for key in required_keys if key not in state]
        if missing_keys:
            raise ValueError(f"Missing required state keys: {missing_keys}")

class AgentFactory:
    """Factory for creating agents"""
    
    _agents = {}
    
    @classmethod
    def register_agent(cls, name: str, agent_class: type[BaseAgent]):
        """Register an agent class"""
        cls._agents[name] = agent_class
    
    @classmethod
    def create_agent(cls, name: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """Create an agent instance"""
        if name not in cls._agents:
            raise ValueError(f"Unknown agent type: {name}")
        
        agent_class = cls._agents[name]
        return agent_class(config)
    
    @classmethod
    def list_agents(cls) -> list[str]:
        """List available agent types"""
        return list(cls._agents.keys())