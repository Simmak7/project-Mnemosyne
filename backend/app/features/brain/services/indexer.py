"""Brain Indexer - Main orchestration for semantic condensation pipeline.

Pipeline:
1. Detect changed content since last indexing
2. Extract facts using SemanticCondenser
3. Analyze graph signals (centrality, connections)
4. Classify facts using MemoryClassifier
5. Generate training samples
6. Store results in database

The indexer runs incrementally - only processing content that has
changed since the last indexing run.
"""

import logging
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models import Note, Image
from .condenser import SemanticCondenser, ExtractedFact, CondensationResult
from .classifier import MemoryClassifier, ClassifiedMemory, GraphSignals, ClassifiedFact
from ..models import TrainingSample, CondensedFact, IndexingRun, MemoryType

logger = logging.getLogger(__name__)


@dataclass
class IndexingStats:
    """Statistics from an indexing run."""
    notes_processed: int = 0
    images_processed: int = 0
    facts_extracted: int = 0
    facts_new: int = 0
    facts_updated: int = 0
    samples_generated: int = 0
    processing_time_ms: int = 0


@dataclass
class IndexingResult:
    """Result of a brain indexing run."""
    run_id: int
    stats: IndexingStats
    classified: ClassifiedMemory
    errors: List[str] = field(default_factory=list)


# Training sample templates by type
SAMPLE_TEMPLATES = {
    "identity": [
        ("Who am I?", "You are {content}"),
        ("Tell me about myself.", "{content}"),
    ],
    "interests": [
        ("What topics am I interested in?", "You frequently explore: {content}"),
        ("What are my main interests?", "{content}"),
    ],
    "cognitive_style": [
        ("How do I organize my thoughts?", "{content}"),
        ("What's my thinking style?", "{content}"),
    ],
    "preferences": [
        ("What are my preferences?", "{content}"),
        ("How do I like things done?", "{content}"),
    ],
    "projects": [
        ("What am I working on?", "{content}"),
        ("What are my current projects?", "{content}"),
    ],
    "behaviors": [
        ("What are my habits?", "{content}"),
        ("What do I typically do?", "{content}"),
    ],
}


class BrainIndexer:
    """Orchestrates the brain indexing pipeline."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.condenser = SemanticCondenser()
        self.classifier = MemoryClassifier()

    async def index_changes(
        self,
        full_reindex: bool = False
    ) -> IndexingResult:
        """Run the indexing pipeline.

        Args:
            full_reindex: If True, reprocess all content

        Returns:
            IndexingResult with statistics and classified facts
        """
        import time
        start_time = time.time()

        # Create indexing run record
        run = IndexingRun(owner_id=self.user_id, status="running")
        self.db.add(run)
        self.db.commit()

        stats = IndexingStats()
        errors = []
        all_facts: List[ExtractedFact] = []

        try:
            # 1. Detect changed content
            notes, images = self._detect_changes(full_reindex)
            stats.notes_processed = len(notes)
            stats.images_processed = len(images)

            logger.info(f"Processing {len(notes)} notes and {len(images)} images")

            # 2. Extract facts from notes
            for note in notes:
                try:
                    result = await self.condenser.extract_facts_from_note(
                        note_id=note.id,
                        title=note.title,
                        content=note.content or ""
                    )
                    all_facts.extend(result.facts)
                except Exception as e:
                    errors.append(f"Note {note.id}: {str(e)}")
                    logger.error(f"Error processing note {note.id}: {e}")

            # 3. Extract facts from images
            for image in images:
                try:
                    result = await self.condenser.extract_facts_from_image(
                        image_id=image.id,
                        ai_analysis=image.ai_analysis_result or ""
                    )
                    all_facts.extend(result.facts)
                except Exception as e:
                    errors.append(f"Image {image.id}: {str(e)}")
                    logger.error(f"Error processing image {image.id}: {e}")

            stats.facts_extracted = len(all_facts)

            # 4. Analyze graph signals
            graph_signals = self._analyze_graph_signals()

            # 5. Classify facts
            classified = self.classifier.classify(all_facts, graph_signals)

            # 6. Update with historical recurrence
            fact_history = self._get_fact_recurrence()
            classified = self.classifier.update_with_recurrence(classified, fact_history)

            # 7. Store facts in database
            new_count, updated_count = await self._store_facts(classified)
            stats.facts_new = new_count
            stats.facts_updated = updated_count

            # 8. Generate training samples
            samples = await self._generate_samples(classified)
            stats.samples_generated = len(samples)

            # Calculate processing time
            stats.processing_time_ms = int((time.time() - start_time) * 1000)

            # Update run record
            run.status = "completed"
            run.notes_processed = stats.notes_processed
            run.images_processed = stats.images_processed
            run.facts_extracted = stats.facts_extracted
            run.samples_generated = stats.samples_generated
            run.completed_at = datetime.utcnow()
            run.duration_seconds = stats.processing_time_ms // 1000
            self.db.commit()

            logger.info(
                f"Indexing complete: {stats.facts_extracted} facts, "
                f"{stats.samples_generated} samples in {stats.processing_time_ms}ms"
            )

            return IndexingResult(
                run_id=run.id,
                stats=stats,
                classified=classified,
                errors=errors
            )

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            self.db.commit()
            logger.error(f"Indexing failed: {e}")
            raise

    def _detect_changes(
        self,
        full_reindex: bool
    ) -> Tuple[List[Note], List[Image]]:
        """Detect content changed since last indexing."""
        # Get last successful run
        last_run = (
            self.db.query(IndexingRun)
            .filter(
                IndexingRun.owner_id == self.user_id,
                IndexingRun.status == "completed"
            )
            .order_by(IndexingRun.completed_at.desc())
            .first()
        )

        if full_reindex or last_run is None:
            # Process all content
            notes = (
                self.db.query(Note)
                .filter(Note.owner_id == self.user_id, Note.is_trashed == False)
                .all()
            )
            images = (
                self.db.query(Image)
                .filter(
                    Image.owner_id == self.user_id,
                    Image.is_trashed == False,
                    Image.ai_analysis_result.isnot(None)
                )
                .all()
            )
        else:
            # Only changed since last run
            since = last_run.completed_at
            notes = (
                self.db.query(Note)
                .filter(
                    Note.owner_id == self.user_id,
                    Note.is_trashed == False,
                    Note.updated_at > since
                )
                .all()
            )
            images = (
                self.db.query(Image)
                .filter(
                    Image.owner_id == self.user_id,
                    Image.is_trashed == False,
                    Image.ai_analysis_result.isnot(None),
                    Image.uploaded_at > since
                )
                .all()
            )

        return notes, images

    def _analyze_graph_signals(self) -> GraphSignals:
        """Analyze knowledge graph for concept centrality."""
        signals = GraphSignals()

        # Get all notes for graph analysis
        notes = (
            self.db.query(Note)
            .filter(Note.owner_id == self.user_id, Note.is_trashed == False)
            .all()
        )

        # Extract wikilinks and build concept graph
        from features.graph.wikilink_parser import extract_wikilinks

        concept_links: Dict[str, Set[str]] = {}
        concept_counts: Dict[str, int] = {}

        for note in notes:
            # Count title as concept
            title_lower = note.title.lower()
            concept_counts[title_lower] = concept_counts.get(title_lower, 0) + 1

            # Extract wikilinks
            content = note.content or ""
            links = extract_wikilinks(content)

            for link in links:
                target = link.lower()
                concept_counts[target] = concept_counts.get(target, 0) + 1

                if title_lower not in concept_links:
                    concept_links[title_lower] = set()
                concept_links[title_lower].add(target)

        # Calculate centrality (simplified degree centrality)
        total_concepts = len(concept_counts) or 1
        for concept, count in concept_counts.items():
            # Normalize by total concepts
            connections = len(concept_links.get(concept, set()))
            centrality = (count + connections) / (total_concepts * 2)
            signals.centrality[concept] = min(1.0, centrality)
            signals.recurrence[concept] = count

        signals.connections = concept_links

        return signals

    def _get_fact_recurrence(self) -> Dict[str, int]:
        """Get historical recurrence counts for concepts."""
        facts = (
            self.db.query(CondensedFact.concept, func.sum(CondensedFact.recurrence))
            .filter(CondensedFact.owner_id == self.user_id)
            .group_by(CondensedFact.concept)
            .all()
        )

        return {concept.lower(): count for concept, count in facts}

    async def _store_facts(
        self,
        classified: ClassifiedMemory
    ) -> Tuple[int, int]:
        """Store classified facts in database."""
        new_count = 0
        updated_count = 0

        all_classified = (
            classified.preferences +
            classified.semantic +
            classified.episodic
        )

        for cf in all_classified:
            fact = cf.fact
            # Skip facts with missing concept
            if not fact.concept:
                logger.warning(f"Skipping fact with missing concept: {fact.fact_text[:50]}")
                continue
            concept = fact.concept.lower()

            # Check if fact exists
            existing = (
                self.db.query(CondensedFact)
                .filter(
                    CondensedFact.owner_id == self.user_id,
                    CondensedFact.concept == concept,
                    CondensedFact.fact_text == fact.fact_text
                )
                .first()
            )

            if existing:
                # Update existing fact
                existing.recurrence += 1
                existing.last_seen = datetime.utcnow()
                existing.memory_type = MemoryType(cf.memory_type)
                existing.confidence = max(existing.confidence, fact.confidence)
                updated_count += 1
            else:
                # Create new fact
                new_fact = CondensedFact(
                    owner_id=self.user_id,
                    fact_text=fact.fact_text,
                    concept=concept,
                    fact_type=fact.fact_type,
                    memory_type=MemoryType(cf.memory_type),
                    confidence=fact.confidence,
                    recurrence=1
                )
                self.db.add(new_fact)
                new_count += 1

        self.db.commit()
        return new_count, updated_count

    async def _generate_samples(
        self,
        classified: ClassifiedMemory
    ) -> List[TrainingSample]:
        """Generate training samples from classified facts."""
        samples = []

        # Only generate from semantic and preference facts
        trainable = classified.preferences + classified.semantic

        # Group facts by concept for aggregation
        by_concept: Dict[str, List[ClassifiedFact]] = {}
        for cf in trainable:
            # Skip facts with missing concept
            if not cf.fact.concept:
                continue
            concept = cf.fact.concept.lower()
            if concept not in by_concept:
                by_concept[concept] = []
            by_concept[concept].append(cf)

        # Generate samples for each concept
        for concept, facts in by_concept.items():
            # Determine sample type based on facts
            sample_type = self._determine_sample_type(facts)

            # Combine facts into coherent output
            combined_output = self._combine_facts_for_sample(facts)

            if not combined_output:
                continue

            # Get template for this type
            templates = SAMPLE_TEMPLATES.get(sample_type, SAMPLE_TEMPLATES["preferences"])
            instruction, output_template = templates[0]

            # Create sample
            sample = TrainingSample(
                owner_id=self.user_id,
                instruction=instruction,
                input_text="",
                output=output_template.format(content=combined_output),
                sample_type=sample_type,
                memory_type=MemoryType.PREFERENCE if facts[0].memory_type == "preference" else MemoryType.SEMANTIC,
                source_note_ids=[],  # Could track source notes
                confidence=sum(f.fact.confidence for f in facts) / len(facts),
                recurrence=sum(1 for f in facts),
                is_trained="pending"
            )
            self.db.add(sample)
            samples.append(sample)

        self.db.commit()
        return samples

    def _determine_sample_type(self, facts: List[ClassifiedFact]) -> str:
        """Determine the sample type based on facts."""
        # Check classification reasons and fact types
        reasons = [f.classification_reason for f in facts]
        fact_types = [f.fact.fact_type for f in facts]

        if any("identity" in r for r in reasons):
            return "identity"
        if any("preference" in r for r in reasons):
            return "preferences"
        if "relation" in fact_types:
            return "projects"
        if "entity" in fact_types:
            return "interests"

        return "behaviors"

    def _combine_facts_for_sample(self, facts: List[ClassifiedFact]) -> str:
        """Combine multiple facts into a coherent training output."""
        if not facts:
            return ""

        # Simple combination - join fact texts
        fact_texts = [f.fact.fact_text for f in facts if f.fact.fact_text]

        if len(fact_texts) == 1:
            return fact_texts[0]

        # Combine with semicolons for multiple facts
        return "; ".join(fact_texts[:5])  # Limit to 5 facts per sample

    def get_status(self) -> Dict:
        """Get current brain indexing status."""
        # Get latest run
        latest_run = (
            self.db.query(IndexingRun)
            .filter(IndexingRun.owner_id == self.user_id)
            .order_by(IndexingRun.started_at.desc())
            .first()
        )

        # Count facts and samples
        facts_count = (
            self.db.query(CondensedFact)
            .filter(CondensedFact.owner_id == self.user_id)
            .count()
        )

        samples_count = (
            self.db.query(TrainingSample)
            .filter(TrainingSample.owner_id == self.user_id)
            .count()
        )

        # Count notes indexed
        notes_count = (
            self.db.query(Note)
            .filter(Note.owner_id == self.user_id, Note.is_trashed == False)
            .count()
        )

        return {
            "last_run": {
                "id": latest_run.id if latest_run else None,
                "status": latest_run.status if latest_run else None,
                "completed_at": latest_run.completed_at if latest_run else None,
                "facts_extracted": latest_run.facts_extracted if latest_run else 0,
                "samples_generated": latest_run.samples_generated if latest_run else 0,
            } if latest_run else None,
            "totals": {
                "facts": facts_count,
                "samples": samples_count,
                "notes": notes_count,
            }
        }
