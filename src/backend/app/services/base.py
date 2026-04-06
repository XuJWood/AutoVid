"""
Base AI Service Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class GenerationResult(BaseModel):
    """Result of AI generation"""
    success: bool
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class BaseAIService(ABC):
    """Base class for AI services"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate content from prompt"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the service is accessible"""
        pass
