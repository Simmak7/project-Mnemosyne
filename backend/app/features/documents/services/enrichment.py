"""
Document Enrichment Service

Uses Ollama Qwen3:8b for AI analysis: summary, document type, tags, wikilinks.
Falls back to Llama Vision for OCR on scanned PDFs.
"""

import os
import re
import json
import logging
import requests
import base64
from typing import Dict, Optional

from core import config

logger = logging.getLogger(__name__)

# Enrichment prompt template
ENRICHMENT_PROMPT = """You are analyzing extracted text from a PDF document.
The text below was extracted directly from the document.

Provide:
1. A detailed summary (4-6 paragraphs) covering the key points, purpose, and main arguments. Include specific details, key arguments, notable data points, and important conclusions. Do not be overly brief.
2. The document type (contract, report, letter, invoice, academic, manual, presentation, notes, unknown)
3. Up to 10 relevant tags (lowercase, single words or hyphenated phrases, e.g. "machine-learning")
4. Up to 5 important entities, people, concepts, or topics mentioned that could be wikilinks to related notes

Respond ONLY with this exact JSON format (no other text, no markdown, no explanation):
{
  "summary": "...",
  "document_type": "...",
  "tags": ["tag1", "tag2"],
  "wikilinks": ["Entity Name", "Topic"]
}

/no_think

Extracted document text:
"""

# Max text to send to AI (avoid token overflow)
MAX_TEXT_FOR_AI = 16000


class DocumentEnricher:
    """AI enrichment for extracted document text."""

    def __init__(self):
        self.ollama_host = config.OLLAMA_HOST
        self.model = config.RAG_MODEL  # qwen3:8b
        self.timeout = config.RAG_TIMEOUT

    def enrich_document(
        self,
        text: str,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        user_instructions: Optional[str] = None,
    ) -> Dict:
        """
        Enrich document text with AI analysis.

        Returns:
            {
                "summary": str,
                "document_type": str,
                "tags": list[str],
                "wikilinks": list[str],
                "raw_response": str,
            }
        """
        model = model or self.model
        timeout = timeout or self.timeout

        # Truncate text for AI context
        truncated = text[:MAX_TEXT_FOR_AI]
        if len(text) > MAX_TEXT_FOR_AI:
            truncated += f"\n\n[... truncated, {len(text) - MAX_TEXT_FOR_AI} chars omitted]"

        prompt = ENRICHMENT_PROMPT
        if user_instructions:
            prompt += f"\n\nAdditional user instructions: {user_instructions}\n\n"
        prompt += truncated

        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 4000},
                },
                timeout=timeout,
            )

            if response.status_code != 200:
                logger.error(f"Ollama returned {response.status_code}")
                return self._empty_result(f"Ollama error: {response.status_code}")

            raw_text = response.json().get("response", "")
            parsed = self._parse_ai_response(raw_text)
            parsed["raw_response"] = raw_text
            return parsed

        except requests.exceptions.Timeout:
            logger.error("Ollama timeout during enrichment")
            return self._empty_result("AI enrichment timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama for enrichment")
            return self._empty_result("Cannot connect to AI service")
        except Exception as e:
            logger.error(f"Enrichment error: {e}", exc_info=True)
            return self._empty_result(str(e))

    def ocr_with_vision(self, filepath: str) -> Optional[str]:
        """
        OCR fallback for scanned PDFs using Llama Vision.

        Converts first few pages to images and sends to vision model.
        """
        try:
            from pdf2image import convert_from_path

            # Convert first 3 pages
            images = convert_from_path(filepath, first_page=1, last_page=3, dpi=200)
            if not images:
                return None

            all_text = []
            vision_model = os.getenv("OLLAMA_MODEL_OLD", "llama3.2-vision:11b")

            for i, image in enumerate(images):
                # Convert PIL to base64
                import io
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode()

                response = requests.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": vision_model,
                        "prompt": "Extract all text from this document page. Return only the text content.",
                        "images": [img_b64],
                        "stream": False,
                    },
                    timeout=120,
                )

                if response.status_code == 200:
                    page_text = response.json().get("response", "")
                    all_text.append(f"--- Page {i + 1} ---\n{page_text}")

            return "\n\n".join(all_text) if all_text else None

        except Exception as e:
            logger.error(f"Vision OCR failed: {e}", exc_info=True)
            return None

    def _parse_ai_response(self, text: str) -> Dict:
        """Parse AI JSON response, handling partial/malformed output."""
        # Strip Qwen3 <think>...</think> blocks
        cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text).strip()

        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "summary": data.get("summary", ""),
                    "document_type": data.get("document_type", "unknown"),
                    "tags": self._clean_tags(data.get("tags", [])),
                    "wikilinks": data.get("wikilinks", []),
                }
            except json.JSONDecodeError:
                logger.warning("JSON decode failed, trying markdown fallback")

        # Fallback: extract from markdown/text response
        logger.warning("No JSON found in AI response, using markdown fallback parser")
        return self._parse_markdown_fallback(cleaned or text)

    def _parse_markdown_fallback(self, text: str) -> Dict:
        """Extract summary, tags, wikilinks from non-JSON AI response."""
        summary = text[:2000]
        doc_type = "unknown"
        tags = []
        wikilinks = []

        # Try to detect document type from text
        type_match = re.search(
            r'(?:document[_ ]?type|type)\s*[:=]\s*["\']?(\w+)',
            text, re.IGNORECASE
        )
        if type_match:
            doc_type = type_match.group(1).lower()

        # Extract tags from markdown lists or inline mentions
        tag_section = re.search(
            r'(?:tags?|keywords?)\s*[:]\s*(.*?)(?:\n\n|\n(?=[A-Z#*])|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        if tag_section:
            raw = tag_section.group(1)
            # Match list items: - tag, * tag, or "tag", or `tag`
            found = re.findall(r'[-*]\s*["`]?([^",`\n]+)["`]?', raw)
            if not found:
                found = re.findall(r'["`]([^"`]+)["`]', raw)
            tags = [t.strip().lower().replace(" ", "-") for t in found if t.strip()]

        # Extract wikilinks from markdown lists
        wiki_section = re.search(
            r'(?:wikilinks?|entities|concepts|topics)\s*[:]\s*(.*?)(?:\n\n|\n(?=[A-Z#*])|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        if wiki_section:
            raw = wiki_section.group(1)
            found = re.findall(r'[-*]\s*["`]?([^",`\n]+)["`]?', raw)
            if not found:
                found = re.findall(r'["`]([^"`]+)["`]', raw)
            wikilinks = [w.strip() for w in found if w.strip()]

        return {
            "summary": summary,
            "document_type": doc_type,
            "tags": self._clean_tags(tags[:10]),
            "wikilinks": wikilinks[:5],
        }

    def _clean_tags(self, tags: list) -> list:
        """Normalize tags: lowercase, strip, limit length."""
        cleaned = []
        for tag in tags[:10]:
            if isinstance(tag, str):
                t = tag.strip().lower().replace(" ", "-")
                if t and len(t) <= 50:
                    cleaned.append(t)
        return cleaned

    def _empty_result(self, error: str) -> Dict:
        """Return empty enrichment result with error."""
        return {
            "summary": "",
            "document_type": "unknown",
            "tags": [],
            "wikilinks": [],
            "raw_response": error,
        }
