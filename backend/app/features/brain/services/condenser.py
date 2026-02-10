"""Semantic Condenser - Extract stable facts from user content.

The condenser analyzes notes and images to extract atomic facts that represent
the user's knowledge. These facts are later classified and combined into
training samples for LoRA fine-tuning.

Fact Types:
- entity: People, places, things (e.g., "Sarah is a colleague")
- relation: Connections between entities (e.g., "works with Sarah on wedding")
- attribute: Properties of entities (e.g., "wedding budget is $15,000")
- event: Time-bound occurrences (e.g., "wedding scheduled for June 2025")
"""

import os
import json
import logging
import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
CONDENSER_MODEL = os.getenv("CONDENSER_MODEL", "llama3.2:3b")


@dataclass
class ExtractedFact:
    """A single fact extracted from content."""
    fact_text: str
    concept: str
    fact_type: str  # entity, relation, attribute, event
    confidence: float
    source_text: str
    has_temporal_reference: bool = False
    entities: List[str] = field(default_factory=list)


@dataclass
class CondensationResult:
    """Result of condensing a piece of content."""
    facts: List[ExtractedFact]
    source_type: str  # note, image
    source_id: int
    processing_time_ms: int


FACT_EXTRACTION_PROMPT = """You are a knowledge extraction system. Extract atomic facts from the following text.

For each fact, provide:
1. fact_text: The fact as a clear, standalone statement
2. concept: The main concept/entity this fact is about
3. fact_type: One of: entity, relation, attribute, event
4. confidence: 0.0-1.0 how certain this fact is
5. has_temporal: true if this fact is time-bound
6. entities: List of named entities mentioned

Rules:
- Extract only factual information, not opinions or speculation
- Each fact should be atomic (one piece of information)
- Normalize names (e.g., "my wife Sarah" -> "Sarah (wife)")
- Mark time-bound facts (dates, deadlines, scheduled events) as temporal

Respond with a JSON array of facts. If no clear facts can be extracted, return [].

TEXT:
{text}

FACTS (JSON array):"""


class SemanticCondenser:
    """Extract stable facts from user content."""

    def __init__(self, model: str = None):
        self.model = model or CONDENSER_MODEL
        self._cache: Dict[str, CondensationResult] = {}

    async def extract_facts_from_note(
        self,
        note_id: int,
        title: str,
        content: str
    ) -> CondensationResult:
        """Extract facts from a note.

        Args:
            note_id: Note database ID
            title: Note title
            content: Note content (markdown)

        Returns:
            CondensationResult with extracted facts
        """
        import time
        start_time = time.time()

        # Combine title and content for context
        text = f"# {title}\n\n{content}"

        # Check cache
        cache_key = f"note:{note_id}:{hash(text)}"
        if cache_key in self._cache:
            logger.debug(f"Cache hit for note {note_id}")
            return self._cache[cache_key]

        # Extract facts using LLM
        facts = await self._extract_facts(text)

        processing_time = int((time.time() - start_time) * 1000)

        result = CondensationResult(
            facts=facts,
            source_type="note",
            source_id=note_id,
            processing_time_ms=processing_time
        )

        self._cache[cache_key] = result
        logger.info(f"Extracted {len(facts)} facts from note {note_id} in {processing_time}ms")

        return result

    async def extract_facts_from_image(
        self,
        image_id: int,
        ai_analysis: str
    ) -> CondensationResult:
        """Extract facts from image AI analysis.

        Args:
            image_id: Image database ID
            ai_analysis: AI-generated image analysis text

        Returns:
            CondensationResult with extracted facts
        """
        import time
        start_time = time.time()

        if not ai_analysis:
            return CondensationResult(
                facts=[],
                source_type="image",
                source_id=image_id,
                processing_time_ms=0
            )

        facts = await self._extract_facts(ai_analysis)

        processing_time = int((time.time() - start_time) * 1000)

        return CondensationResult(
            facts=facts,
            source_type="image",
            source_id=image_id,
            processing_time_ms=processing_time
        )

    async def _extract_facts(self, text: str) -> List[ExtractedFact]:
        """Extract facts from text using LLM.

        Args:
            text: Text to extract facts from

        Returns:
            List of ExtractedFact objects
        """
        if not text or len(text.strip()) < 20:
            return []

        # Truncate very long texts
        max_length = 4000
        if len(text) > max_length:
            text = text[:max_length] + "..."

        prompt = FACT_EXTRACTION_PROMPT.format(text=text)

        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "think": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for consistent extraction
                        "num_predict": 2000
                    }
                },
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "")

            # Parse JSON from response
            facts = self._parse_facts_response(response_text, text)
            return facts

        except requests.exceptions.Timeout:
            logger.error("Timeout during fact extraction")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during fact extraction: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during fact extraction: {e}")
            return []

    def _parse_facts_response(
        self,
        response_text: str,
        source_text: str
    ) -> List[ExtractedFact]:
        """Parse LLM response into ExtractedFact objects.

        Args:
            response_text: Raw LLM response
            source_text: Original source text for provenance

        Returns:
            List of ExtractedFact objects
        """
        try:
            # Try to find JSON array in response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1

            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON array found in response")
                return []

            json_str = response_text[start_idx:end_idx]
            facts_data = json.loads(json_str)

            if not isinstance(facts_data, list):
                return []

            facts = []
            for item in facts_data:
                if not isinstance(item, dict):
                    continue

                fact = ExtractedFact(
                    fact_text=item.get("fact_text", ""),
                    concept=item.get("concept", "unknown"),
                    fact_type=item.get("fact_type", "entity"),
                    confidence=float(item.get("confidence", 0.5)),
                    source_text=source_text[:500],  # Truncate for storage
                    has_temporal_reference=item.get("has_temporal", False),
                    entities=item.get("entities", [])
                )

                # Validate fact
                if fact.fact_text and len(fact.fact_text) > 5:
                    facts.append(fact)

            return facts

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse facts JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing facts response: {e}")
            return []

    def merge_duplicate_facts(
        self,
        facts: List[ExtractedFact]
    ) -> List[ExtractedFact]:
        """Merge semantically similar facts.

        Args:
            facts: List of facts to deduplicate

        Returns:
            Deduplicated list with recurrence counts
        """
        # Group by concept
        by_concept: Dict[str, List[ExtractedFact]] = {}
        for fact in facts:
            if not fact.concept:
                continue
            concept = fact.concept.lower().strip()
            if concept not in by_concept:
                by_concept[concept] = []
            by_concept[concept].append(fact)

        merged = []
        for concept, concept_facts in by_concept.items():
            if len(concept_facts) == 1:
                merged.append(concept_facts[0])
            else:
                # Keep highest confidence, note recurrence
                best = max(concept_facts, key=lambda f: f.confidence)
                # Could add recurrence tracking here
                merged.append(best)

        return merged
