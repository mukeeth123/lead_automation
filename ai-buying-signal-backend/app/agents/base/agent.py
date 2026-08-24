from abc import ABC, abstractmethod
from typing import List
from app.schemas.signal import RawSignalCreate

class BaseSourceAgent(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    async def collect(self) -> List[RawSignalCreate]:
        """Collect and normalize signals."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify the source is accessible and parsing works."""
        pass
