from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from app.schemas.unified import UnifiedSignal

class BaseConnector(ABC):
    source_name: str

    @abstractmethod
    async def discover(self, campaign: Any, cursor: Optional[str] = None) -> List[Any]:
        """Discover candidate signals based on the campaign intelligence."""
        pass

    @abstractmethod
    async def fetch(self, external_id: str) -> Dict[str, Any]:
        """Fetch complete source data for a specific external ID."""
        pass

    @abstractmethod
    async def normalize(self, raw_data: Dict[str, Any]) -> UnifiedSignal:
        """Convert source-specific data into UnifiedSignal."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check source availability."""
        pass

    @abstractmethod
    async def get_rate_limit(self) -> Dict[str, Any]:
        """Return connector-specific rate limits."""
        pass
