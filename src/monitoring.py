import time
import psutil
from typing import Dict, Any
from functools import wraps
from .logger import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "active_connections": len(psutil.net_connections()),
        }
    
    @staticmethod
    def monitor_execution_time(func_name: str = None):
        """Decorator to monitor function execution time"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    logger.info(f"{func_name or func.__name__} executed in {execution_time:.3f}s")
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"{func_name or func.__name__} failed after {execution_time:.3f}s: {str(e)}")
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    logger.info(f"{func_name or func.__name__} executed in {execution_time:.3f}s")
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"{func_name or func.__name__} failed after {execution_time:.3f}s: {str(e)}")
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

import asyncio