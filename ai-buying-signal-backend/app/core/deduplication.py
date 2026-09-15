import re
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.unified_signal import UnifiedSignalModel

class DeduplicationResult:
    def __init__(self, is_duplicate: bool, duplicate_type: Optional[str] = None, original_id: Optional[str] = None, similarity: float = 0.0):
        self.is_duplicate = is_duplicate
        self.duplicate_type = duplicate_type
        self.original_id = original_id
        self.similarity = similarity

class Deduplicator:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _tokenize(self, text: str) -> set:
        """Simple tokenizer for Jaccard similarity."""
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return set(words)

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    async def check_duplicate(self, source: str, external_id: str, content_hash: str, text_body: str) -> DeduplicationResult:
        """
        Run the 3-Tier Deduplication Process:
        1. Source ID Match (Same exact post ID from the same source)
        2. Exact Hash Match (Same exact content seen before, possibly crossposted)
        3. Semantic / Near-Duplicate Match (Jaccard similarity > 0.8)
        """
        
        # Level 1: Source + External ID Match
        stmt1 = select(UnifiedSignalModel.signal_id).where(
            UnifiedSignalModel.source == source,
            UnifiedSignalModel.external_id == external_id
        )
        result1 = await self.db.execute(stmt1)
        existing_id = result1.scalars().first()
        if existing_id:
            return DeduplicationResult(is_duplicate=True, duplicate_type="SOURCE_ID", original_id=existing_id, similarity=1.0)
            
        # Level 2: Exact Content Hash Match
        stmt2 = select(UnifiedSignalModel.signal_id).where(
            UnifiedSignalModel.content_hash == content_hash
        )
        result2 = await self.db.execute(stmt2)
        existing_hash_id = result2.scalars().first()
        if existing_hash_id:
            return DeduplicationResult(is_duplicate=True, duplicate_type="EXACT_HASH", original_id=existing_hash_id, similarity=1.0)
            
        # Level 3: Near-Duplicate Detection (Jaccard Similarity)
        # In a production DB with millions of rows, we wouldn't fetch all text bodies.
        # We would use pgvector or minhash index. For the MVP, we assume we fetch recent signals.
        
        # We will skip fetching thousands of rows for Jaccard here to prevent DB death.
        # Instead, we just stub the semantic check which would ideally be done via pgvector or a specialized DB index in Phase 4.
        
        # Placeholder for Semantic match
        # To truly implement this safely, we would need the vector DB (Phase 4).
        # We will return not duplicate for now unless we do a limited time-window fetch.
        
        return DeduplicationResult(is_duplicate=False)
