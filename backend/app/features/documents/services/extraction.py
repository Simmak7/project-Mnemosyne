"""
PDF Extraction Service

Extracts text from PDFs using pdfplumber.
Generates thumbnails using pdf2image.
Detects scanned (image-only) PDFs.
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Minimum chars per page to consider it "text-rich" vs scanned
SPARSE_TEXT_THRESHOLD = 50


class PDFExtractor:
    """Extracts text and metadata from PDF files."""

    def extract_text(self, filepath: str) -> Dict:
        """
        Extract text from a PDF using pdfplumber.

        Returns:
            {
                "text": str,          # Full extracted text
                "page_count": int,
                "pages": [{"page": int, "text": str, "chars": int}],
                "is_scanned": bool,   # True if most pages have sparse text
            }
        """
        import pdfplumber

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PDF not found: {filepath}")

        pages_data = []
        all_text_parts = []

        with pdfplumber.open(filepath) as pdf:
            page_count = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text() or ""
                    pages_data.append({
                        "page": i + 1,
                        "text": page_text,
                        "chars": len(page_text),
                    })
                    all_text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {i + 1}: {e}")
                    pages_data.append({"page": i + 1, "text": "", "chars": 0})

        full_text = "\n\n".join(all_text_parts)
        is_scanned = self._detect_sparse_text(pages_data)

        logger.info(
            f"Extracted {len(full_text)} chars from {page_count} pages "
            f"(scanned={is_scanned})"
        )

        return {
            "text": full_text,
            "page_count": page_count,
            "pages": pages_data,
            "is_scanned": is_scanned,
        }

    def generate_thumbnail(
        self, filepath: str, output_dir: str, doc_id: int
    ) -> Dict:
        """
        Generate a thumbnail from the first page of a PDF.

        Returns:
            {"thumbnail_path": str, "blur_hash": str|None, "width": int, "height": int}
        """
        os.makedirs(output_dir, exist_ok=True)

        try:
            from pdf2image import convert_from_path

            # Convert first page only, at 150 DPI for thumbnails
            images = convert_from_path(
                filepath, first_page=1, last_page=1, dpi=150
            )

            if not images:
                return {"thumbnail_path": None, "blur_hash": None}

            thumb_image = images[0]
            # Resize to max 400px wide
            max_width = 400
            if thumb_image.width > max_width:
                ratio = max_width / thumb_image.width
                new_height = int(thumb_image.height * ratio)
                thumb_image = thumb_image.resize((max_width, new_height))

            thumb_filename = f"doc_{doc_id}_thumb.jpg"
            thumb_path = os.path.join(output_dir, thumb_filename)
            thumb_image.save(thumb_path, "JPEG", quality=85)

            # Generate blur hash
            blur_hash_str = self._generate_blur_hash(thumb_image)

            return {
                "thumbnail_path": thumb_path,
                "blur_hash": blur_hash_str,
                "width": thumb_image.width,
                "height": thumb_image.height,
            }

        except Exception as e:
            logger.error(f"Thumbnail generation failed for doc {doc_id}: {e}")
            return {"thumbnail_path": None, "blur_hash": None}

    def _generate_blur_hash(self, image) -> Optional[str]:
        """Generate blur hash from a PIL image."""
        try:
            import blurhash
            # Resize to small for blur hash computation
            small = image.resize((32, 32))
            return blurhash.encode(small, x_components=4, y_components=3)
        except Exception:
            return None

    def _detect_sparse_text(self, pages: list, threshold: int = SPARSE_TEXT_THRESHOLD) -> bool:
        """
        Detect if a PDF is mostly scanned (image-only).

        Returns True if more than half the pages have fewer than
        `threshold` characters of extracted text.
        """
        if not pages:
            return True

        sparse_count = sum(1 for p in pages if p["chars"] < threshold)
        return sparse_count > len(pages) / 2
