"""
AI clustering module for organizing notes into semantic groups.

Uses K-means clustering on note embeddings to automatically group related notes.
Clusters are labeled using TF-IDF keyword extraction from cluster contents.

Algorithm:
1. Fetch notes with pgvector embeddings
2. Run K-means clustering on embedding vectors
3. Extract keywords from each cluster using TF-IDF
4. Generate human-readable labels and emojis
5. Return cluster assignments with metadata

Dependencies:
- numpy: Vector operations
- sklearn: K-means clustering, TF-IDF vectorizer
- pgvector: Note embeddings storage
"""

import logging
from typing import List, Dict, Optional
from collections import Counter
import re
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session
from sqlalchemy import select

from models import Note

logger = logging.getLogger(__name__)

# Stop words for TF-IDF (expanded list for better keyword extraction)
STOP_WORDS = {
    # Basic English stop words
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
    'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very',
    # Note-taking app specific stop words (generic terms that don't indicate topic)
    'note', 'notes', 'document', 'documents', 'file', 'files', 'page', 'pages',
    'text', 'content', 'item', 'items', 'entry', 'entries', 'record', 'records',
    'sure', 'maybe', 'probably', 'likely', 'think', 'know', 'see', 'get', 'got',
    'want', 'need', 'like', 'just', 'also', 'still', 'even', 'really', 'actually',
    'white', 'black', 'red', 'blue', 'green', 'color', 'image', 'images',
    'today', 'tomorrow', 'yesterday', 'daily', 'morning', 'evening', 'night',
    'person', 'people', 'thing', 'things', 'something', 'anything', 'nothing',
    'time', 'day', 'week', 'month', 'year', 'date', 'new', 'old', 'good', 'bad',
    'first', 'last', 'next', 'well', 'way', 'point', 'part', 'place', 'case',
    'using', 'used', 'use', 'make', 'made', 'take', 'took', 'come', 'came', 'go', 'went'
}


class ClusterResult:
    """Result of clustering operation."""

    def __init__(
        self,
        cluster_id: int,
        label: str,
        keywords: List[str],
        note_ids: List[int],
        size: int,
        emoji: str = "📁"
    ):
        self.cluster_id = cluster_id
        self.label = label
        self.keywords = keywords
        self.note_ids = note_ids
        self.size = size
        self.emoji = emoji

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "keywords": self.keywords,
            "note_ids": self.note_ids,
            "size": self.size,
            "emoji": self.emoji
        }


def extract_keywords_tfidf(texts: List[str], top_n: int = 5) -> List[str]:
    """
    Extract top keywords from a collection of texts using TF-IDF.

    TF-IDF (Term Frequency-Inverse Document Frequency) identifies words
    that are frequent in these documents but rare across all documents,
    making them good cluster identifiers.

    Args:
        texts: List of text documents
        top_n: Number of top keywords to return

    Returns:
        List of top keywords sorted by TF-IDF score
    """
    if not texts:
        return []

    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=list(STOP_WORDS),
            ngram_range=(1, 2),  # Include both unigrams and bigrams
            min_df=1,
            max_df=0.8
        )

        # Fit and transform texts
        tfidf_matrix = vectorizer.fit_transform(texts)

        # Get feature names (words/phrases)
        feature_names = vectorizer.get_feature_names_out()

        # Sum TF-IDF scores across all documents
        scores = np.array(tfidf_matrix.sum(axis=0)).flatten()

        # Get top keywords
        top_indices = scores.argsort()[-top_n:][::-1]
        keywords = [feature_names[i] for i in top_indices]

        return keywords

    except Exception as e:
        logger.error(f"TF-IDF keyword extraction failed: {str(e)}", exc_info=True)
        return []


def generate_cluster_label(
    keywords: List[str],
    note_titles: List[str],
    cluster_index: int = 0
) -> str:
    """
    Generate a human-readable label for a cluster.

    Uses keywords and common title words to create a meaningful label.
    Falls back to descriptive category names if keywords are too generic.

    Args:
        keywords: Top TF-IDF keywords for the cluster
        note_titles: Titles of notes in the cluster
        cluster_index: Index of the cluster (for fallback naming)

    Returns:
        Cluster label (e.g., "Machine Learning", "Project Ideas")
    """
    # Fallback category names for when keywords aren't meaningful
    fallback_categories = [
        "Ideas & Thoughts",
        "Research & Learning",
        "Projects & Tasks",
        "Reference Material",
        "Personal & Journal",
        "Miscellaneous",
    ]

    # Filter out very short or generic keywords
    valid_keywords = [
        kw for kw in keywords
        if len(kw) > 2 and kw.lower() not in STOP_WORDS
    ]

    if not valid_keywords:
        # Try to extract common words from note titles
        if note_titles:
            title_words = []
            for title in note_titles:
                if title:
                    words = title.lower().split()
                    title_words.extend([
                        w for w in words
                        if len(w) > 3 and w not in STOP_WORDS
                    ])
            # Find most common title word
            if title_words:
                word_counts = Counter(title_words)
                most_common = word_counts.most_common(1)
                if most_common and most_common[0][1] > 1:
                    return most_common[0][0].capitalize()

        # Use fallback category
        return fallback_categories[cluster_index % len(fallback_categories)]

    # Use the top keyword as the base
    primary_keyword = valid_keywords[0]

    # Capitalize words properly
    words = primary_keyword.split()
    label = " ".join(word.capitalize() for word in words)

    return label


def select_cluster_emoji(keywords: List[str], label: str) -> str:
    """
    Select an appropriate emoji for a cluster based on keywords and label.

    Args:
        keywords: Top keywords for the cluster
        label: Cluster label

    Returns:
        Emoji character
    """
    # Keyword-to-emoji mapping
    emoji_map = {
        'code': '💻', 'programming': '💻', 'software': '💻', 'development': '💻',
        'data': '📊', 'analysis': '📊', 'statistics': '📊', 'chart': '📊',
        'machine learning': '🤖', 'ai': '🤖', 'artificial intelligence': '🤖',
        'design': '🎨', 'art': '🎨', 'creative': '🎨', 'ui': '🎨', 'ux': '🎨',
        'book': '📚', 'reading': '📚', 'literature': '📚', 'paper': '📚',
        'project': '🚀', 'task': '✅', 'todo': '✅', 'plan': '📝',
        'meeting': '👥', 'discussion': '💬', 'conversation': '💬',
        'idea': '💡', 'brainstorm': '💡', 'concept': '💡',
        'research': '🔬', 'science': '🔬', 'experiment': '🔬',
        'business': '💼', 'work': '💼', 'finance': '💰', 'money': '💰',
        'health': '❤️', 'fitness': '💪', 'exercise': '💪',
        'travel': '✈️', 'trip': '🗺️', 'vacation': '🏖️',
        'food': '🍽️', 'recipe': '👨‍🍳', 'cooking': '👨‍🍳',
        'music': '🎵', 'song': '🎵', 'audio': '🎧',
        'image': '🖼️', 'photo': '📷', 'picture': '🎞️',
        'video': '🎬', 'film': '🎬', 'movie': '🎬',
    }

    # Check keywords for matches
    combined_text = " ".join(keywords + [label]).lower()

    for keyword, emoji in emoji_map.items():
        if keyword in combined_text:
            return emoji

    # Default emoji
    return "📁"


def cluster_notes_by_embeddings(
    db: Session,
    owner_id: int,
    k: int = 5,
    min_notes: int = 10
) -> List[ClusterResult]:
    """
    Cluster notes using K-means on their embeddings.

    K-means algorithm:
    1. Initialize k centroids randomly
    2. Assign each note to nearest centroid
    3. Update centroids to mean of assigned notes
    4. Repeat until convergence

    Args:
        db: Database session
        owner_id: User ID to cluster notes for
        k: Number of clusters (default: 5)
        min_notes: Minimum number of notes required for clustering

    Returns:
        List of ClusterResult objects

    Raises:
        ValueError: If not enough notes with embeddings
    """
    logger.info(f"Clustering notes for user {owner_id} with k={k}")

    # Fetch notes with embeddings
    stmt = select(Note).where(
        Note.owner_id == owner_id,
        Note.embedding.isnot(None)
    )
    result = db.execute(stmt)
    notes = result.scalars().all()

    if len(notes) < min_notes:
        logger.warning(
            f"Not enough notes for clustering: {len(notes)} < {min_notes}"
        )
        raise ValueError(
            f"Need at least {min_notes} notes with embeddings for clustering. "
            f"Currently have {len(notes)}."
        )

    # Adjust k if we have fewer notes than clusters
    actual_k = min(k, len(notes))
    if actual_k < k:
        logger.warning(f"Adjusting k from {k} to {actual_k} (not enough notes)")

    # Extract embeddings and metadata
    embeddings = []
    note_data = []

    for note in notes:
        if note.embedding is not None and len(note.embedding) == 768:
            embeddings.append(note.embedding)
            note_data.append({
                'id': note.id,
                'title': note.title or '',
                'content': note.content or ''
            })

    if len(embeddings) < min_notes:
        raise ValueError(
            f"Need at least {min_notes} valid embeddings for clustering. "
            f"Currently have {len(embeddings)}."
        )

    # Convert to numpy array
    X = np.array(embeddings)

    logger.info(f"Clustering {len(X)} notes into {actual_k} clusters")

    # Perform K-means clustering
    try:
        kmeans = KMeans(
            n_clusters=actual_k,
            random_state=42,
            n_init=10,
            max_iter=300
        )
        cluster_labels = kmeans.fit_predict(X)

    except Exception as e:
        logger.error(f"K-means clustering failed: {str(e)}", exc_info=True)
        raise ValueError(f"Clustering failed: {str(e)}")

    # Group notes by cluster
    clusters: Dict[int, List[dict]] = {i: [] for i in range(actual_k)}

    for idx, cluster_id in enumerate(cluster_labels):
        clusters[cluster_id].append(note_data[idx])

    # Generate labels and keywords for each cluster
    results = []

    for cluster_id in range(actual_k):
        cluster_notes = clusters[cluster_id]

        if not cluster_notes:
            continue

        # Extract keywords using TF-IDF
        cluster_texts = [
            f"{note['title']} {note['content']}" for note in cluster_notes
        ]
        keywords = extract_keywords_tfidf(cluster_texts, top_n=5)

        # Generate label
        titles = [note['title'] for note in cluster_notes]
        label = generate_cluster_label(keywords, titles, cluster_id)

        # Select emoji
        emoji = select_cluster_emoji(keywords, label)

        # Create result
        note_ids = [note['id'] for note in cluster_notes]
        result = ClusterResult(
            cluster_id=cluster_id,
            label=label,
            keywords=keywords,
            note_ids=note_ids,
            size=len(note_ids),
            emoji=emoji
        )

        results.append(result)

    logger.info(f"Created {len(results)} clusters")

    # Sort by size (largest first)
    results.sort(key=lambda x: x.size, reverse=True)

    return results


def get_cluster_statistics(clusters: List[ClusterResult]) -> dict:
    """
    Generate statistics about clustering results.

    Args:
        clusters: List of ClusterResult objects

    Returns:
        Dictionary with statistics
    """
    total_notes = sum(c.size for c in clusters)
    avg_size = total_notes / len(clusters) if clusters else 0

    sizes = [c.size for c in clusters]

    return {
        "total_clusters": len(clusters),
        "total_notes": total_notes,
        "average_cluster_size": round(avg_size, 2),
        "min_cluster_size": min(sizes) if sizes else 0,
        "max_cluster_size": max(sizes) if sizes else 0,
        "clusters": [c.to_dict() for c in clusters]
    }
