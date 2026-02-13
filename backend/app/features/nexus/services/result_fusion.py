"""
Result Fusion - Intent-Aware Weighted Merge

Combines results from vector search and graph navigation with
intent-based weighting and cross-confirmation boosting.

Weight Matrix:
| Intent      | Graph | Vector | Diffusion |
|-------------|:-----:|:------:|:---------:|
| FACTUAL     | 0.30  | 0.50   | 0.20      |
| SYNTHESIS   | 0.40  | 0.30   | 0.30      |
| EXPLORATION | 0.50  | 0.20   | 0.30      |
| TEMPORAL    | 0.20  | 0.60   | 0.20      |
| CREATIVE    | 0.40  | 0.40   | 0.20      |
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

from features.rag_chat.services.retrieval import RetrievalResult
from features.rag_chat.services.ranking import RankedResult

logger = logging.getLogger(__name__)

# Intent -> (graph_weight, vector_weight, diffusion_weight)
INTENT_WEIGHTS = {
    "factual":     (0.30, 0.50, 0.20),
    "synthesis":   (0.40, 0.30, 0.30),
    "exploration": (0.50, 0.20, 0.30),
    "temporal":    (0.20, 0.60, 0.20),
    "creative":    (0.40, 0.40, 0.20),
}

CROSS_CONFIRMATION_BOOST = 1.3


@dataclass
class FusionConfig:
    """Configuration for result fusion."""
    max_results: int = 10
    cross_confirmation_boost: float = CROSS_CONFIRMATION_BOOST
    min_score: float = 0.001  # RRF scores are naturally small (~0.005-0.016)


@dataclass
class FusedResult:
    """A fused result combining multiple strategies."""
    result: RetrievalResult
    final_score: float
    strategies: List[str] = field(default_factory=list)
    cross_confirmed: bool = False


def fuse_results(
    vector_results: List[RankedResult],
    graph_results: Optional[List[RetrievalResult]] = None,
    diffusion_scores: Optional[Dict[int, float]] = None,
    intent: str = "factual",
    config: FusionConfig = None,
) -> List[RankedResult]:
    """
    Fuse results from multiple retrieval strategies.

    Args:
        vector_results: Results from vector search pipeline
        graph_results: Results from graph navigator
        diffusion_scores: Note ID -> importance score from diffusion ranker
        intent: Detected query intent
        config: Fusion configuration

    Returns:
        Merged and re-ranked list of RankedResult
    """
    if config is None:
        config = FusionConfig()

    graph_w, vector_w, diffusion_w = INTENT_WEIGHTS.get(
        intent, INTENT_WEIGHTS["factual"]
    )

    # If no graph results, redistribute weight to vector
    if not graph_results:
        vector_w += graph_w
        graph_w = 0.0

    # If no diffusion scores, redistribute
    if not diffusion_scores:
        vector_w += diffusion_w * 0.5
        graph_w += diffusion_w * 0.5
        diffusion_w = 0.0

    # Normalize weights
    total_w = graph_w + vector_w + diffusion_w
    if total_w > 0:
        graph_w /= total_w
        vector_w /= total_w
        diffusion_w /= total_w

    # Build score map: source_id -> {vector_score, graph_score, diffusion_score, result}
    score_map: Dict[int, Dict] = {}

    for rr in vector_results:
        sid = rr.result.source_id
        score_map[sid] = {
            "result": rr.result,
            "vector_score": rr.final_score,
            "graph_score": 0.0,
            "diffusion_score": 0.0,
            "strategies": ["vector"],
            "rank": rr.rank,
        }

    if graph_results:
        for gr in graph_results:
            sid = gr.source_id
            if sid in score_map:
                score_map[sid]["graph_score"] = gr.similarity
                score_map[sid]["strategies"].append("graph_nav")
            else:
                score_map[sid] = {
                    "result": gr,
                    "vector_score": 0.0,
                    "graph_score": gr.similarity,
                    "diffusion_score": 0.0,
                    "strategies": ["graph_nav"],
                    "rank": len(score_map) + 1,
                }

    if diffusion_scores:
        for sid, d_score in diffusion_scores.items():
            if sid in score_map:
                score_map[sid]["diffusion_score"] = d_score
                if "diffusion" not in score_map[sid]["strategies"]:
                    score_map[sid]["strategies"].append("diffusion")

    # Compute fused scores
    fused: List[RankedResult] = []
    for sid, info in score_map.items():
        weighted_score = (
            info["vector_score"] * vector_w
            + info["graph_score"] * graph_w
            + info["diffusion_score"] * diffusion_w
        )

        # Cross-confirmation boost
        if len(info["strategies"]) > 1:
            weighted_score *= config.cross_confirmation_boost

        if weighted_score < config.min_score:
            continue

        fused.append(RankedResult(
            result=info["result"],
            final_score=round(weighted_score, 4),
            rank=0,
            contributing_methods=info["strategies"],
        ))

    # Sort and assign ranks
    fused.sort(key=lambda x: x.final_score, reverse=True)
    for i, f in enumerate(fused[:config.max_results]):
        f.rank = i + 1

    logger.info(
        f"Fusion: {len(fused[:config.max_results])} results, "
        f"intent={intent}, weights=v{vector_w:.2f}/g{graph_w:.2f}/d{diffusion_w:.2f}"
    )

    return fused[:config.max_results]
