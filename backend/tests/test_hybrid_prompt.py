"""
Unit tests for HybridSmartRouterPrompt

Tests cover:
- Content type detection
- Tag extraction
- Wiki-link extraction
- Metadata extraction
- Prompt generation
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from prompts.hybrid_smart_router_prompt import (
    HybridSmartRouterPrompt,
    ContentType,
    HYBRID_SMART_ROUTER_PROMPT_TEXT,
    LEGACY_PROMPT_TEXT
)


class TestHybridSmartRouterPrompt:
    """Test suite for Hybrid Smart-Router Prompt"""

    # -------------------------------------------------------------------------
    # PROMPT GENERATION TESTS
    # -------------------------------------------------------------------------

    def test_get_prompt_returns_string(self):
        """Test that get_prompt returns a string"""
        prompt = HybridSmartRouterPrompt.get_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # Comprehensive prompt

    def test_prompt_contains_key_sections(self):
        """Test that prompt contains all key sections"""
        prompt = HybridSmartRouterPrompt.get_prompt()

        # Check for content type detection
        assert "CONTENT TYPE DETECTION" in prompt
        assert "DOCUMENT" in prompt
        assert "PHOTO" in prompt
        assert "DIAGRAM" in prompt
        assert "HANDWRITING" in prompt
        assert "MIXED" in prompt

        # Check for strategy sections
        assert "STRATEGY-SPECIFIC EXTRACTION" in prompt

        # Check for universal elements
        assert "UNIVERSAL ELEMENTS" in prompt
        assert "Tags & Categorization" in prompt
        assert "Wiki-Link Connections" in prompt

        # Check for critical instructions
        assert "CRITICAL INSTRUCTIONS" in prompt
        assert "OBSIDIAN COMPATIBILITY" in prompt

    def test_legacy_prompt_exists(self):
        """Test that legacy prompt is available for comparison"""
        assert isinstance(LEGACY_PROMPT_TEXT, str)
        assert len(LEGACY_PROMPT_TEXT) > 100
        assert "note-taking" in LEGACY_PROMPT_TEXT.lower()

    # -------------------------------------------------------------------------
    # CONTENT TYPE DETECTION TESTS
    # -------------------------------------------------------------------------

    def test_extract_detected_type_document_explicit(self):
        """Test explicit document type detection"""
        response = """Detected Type: DOCUMENT
Confidence: HIGH

This is a test document."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.DOCUMENT

    def test_extract_detected_type_photo_explicit(self):
        """Test explicit photo type detection"""
        response = """Detected Type: PHOTO
Confidence: MEDIUM

This is a photograph of a building."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.PHOTO

    def test_extract_detected_type_diagram_explicit(self):
        """Test explicit diagram type detection"""
        response = """Detected Type: DIAGRAM
Confidence: HIGH

This is a flowchart showing process steps."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.DIAGRAM

    def test_extract_detected_type_handwriting_explicit(self):
        """Test explicit handwriting type detection"""
        response = """Detected Type: HANDWRITING
Confidence: LOW

This appears to be handwritten notes."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.HANDWRITING

    def test_extract_detected_type_mixed_explicit(self):
        """Test explicit mixed type detection"""
        response = """Detected Type: MIXED
Confidence: MEDIUM

This contains both a document and a photograph."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.MIXED

    def test_extract_detected_type_document_implicit(self):
        """Test implicit document type detection (fallback)"""
        response = """This is a document containing an invoice from AWS.
The receipt shows payment details."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.DOCUMENT

    def test_extract_detected_type_photo_implicit(self):
        """Test implicit photo type detection (fallback)"""
        response = """This photograph shows a beautiful landscape.
The photo captures mountains in the distance."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.PHOTO

    def test_extract_detected_type_diagram_implicit(self):
        """Test implicit diagram type detection (fallback)"""
        response = """This diagram illustrates the workflow process.
The flowchart shows three main stages."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.DIAGRAM

    def test_extract_detected_type_unknown(self):
        """Test unknown type detection"""
        response = """This is some generic text without clear indicators."""

        content_type = HybridSmartRouterPrompt.extract_detected_type(response)
        assert content_type == ContentType.UNKNOWN

    def test_extract_detected_type_empty(self):
        """Test empty response handling"""
        content_type = HybridSmartRouterPrompt.extract_detected_type("")
        assert content_type == ContentType.UNKNOWN

    # -------------------------------------------------------------------------
    # TAG EXTRACTION TESTS
    # -------------------------------------------------------------------------

    def test_extract_tags_basic(self):
        """Test basic tag extraction"""
        response = """## Tags & Categorization
#document #invoice #vendor-aws #q4-expenses #2024-november"""

        tags = HybridSmartRouterPrompt.extract_tags(response)

        assert "document" in tags
        assert "invoice" in tags
        assert "vendor-aws" in tags
        assert "q4-expenses" in tags
        assert "2024-november" in tags

    def test_extract_tags_scattered(self):
        """Test tag extraction from scattered locations"""
        response = """This is a #document about #cloud-infrastructure.
Some text here.
Related to #vendor-management and #expense-tracking."""

        tags = HybridSmartRouterPrompt.extract_tags(response)

        assert "document" in tags
        assert "cloud-infrastructure" in tags
        assert "vendor-management" in tags
        assert "expense-tracking" in tags

    def test_extract_tags_with_numbers(self):
        """Test tag extraction with numbers"""
        response = """#2024-q4 #phase-1 #version-2 #test-123"""

        tags = HybridSmartRouterPrompt.extract_tags(response)

        assert "2024-q4" in tags
        assert "phase-1" in tags
        assert "version-2" in tags
        assert "test-123" in tags

    def test_extract_tags_deduplication(self):
        """Test that tags are deduplicated"""
        response = """#document #invoice #document #invoice #document"""

        tags = HybridSmartRouterPrompt.extract_tags(response)

        # Should have only 2 unique tags
        assert len(tags) == 2
        assert "document" in tags
        assert "invoice" in tags

    def test_extract_tags_case_normalization(self):
        """Test that tags are lowercased"""
        response = """#Document #INVOICE #Vendor-AWS"""

        tags = HybridSmartRouterPrompt.extract_tags(response)

        # All should be lowercase
        assert "document" in tags
        assert "invoice" in tags
        assert "vendor-aws" in tags

    def test_extract_tags_empty(self):
        """Test empty response handling"""
        tags = HybridSmartRouterPrompt.extract_tags("")
        assert tags == []

    def test_extract_tags_no_tags(self):
        """Test response with no tags"""
        response = """This is a response without any tags."""
        tags = HybridSmartRouterPrompt.extract_tags(response)
        assert tags == []

    # -------------------------------------------------------------------------
    # WIKILINK EXTRACTION TESTS
    # -------------------------------------------------------------------------

    def test_extract_wikilinks_basic(self):
        """Test basic wikilink extraction"""
        response = """## Suggested Connections
1. **[[Vendor Management]]** - Related topic
2. **[[Q4 Budget]]** - Budget planning
3. **[[Cloud Infrastructure Costs]]** - Infrastructure"""

        wikilinks = HybridSmartRouterPrompt.extract_wikilinks(response)

        assert "Vendor Management" in wikilinks
        assert "Q4 Budget" in wikilinks
        assert "Cloud Infrastructure Costs" in wikilinks

    def test_extract_wikilinks_inline(self):
        """Test wikilink extraction from inline text"""
        response = """This relates to [[Project Alpha]] and [[Team Meeting Notes]].
Also see [[November 2024]] for more context."""

        wikilinks = HybridSmartRouterPrompt.extract_wikilinks(response)

        assert "Project Alpha" in wikilinks
        assert "Team Meeting Notes" in wikilinks
        assert "November 2024" in wikilinks

    def test_extract_wikilinks_with_special_chars(self):
        """Test wikilink extraction with special characters"""
        response = """[[Q4 2024: Budget Planning]] and [[Meeting Notes (Nov 27)]]"""

        wikilinks = HybridSmartRouterPrompt.extract_wikilinks(response)

        assert "Q4 2024: Budget Planning" in wikilinks
        assert "Meeting Notes (Nov 27)" in wikilinks

    def test_extract_wikilinks_empty(self):
        """Test empty response handling"""
        wikilinks = HybridSmartRouterPrompt.extract_wikilinks("")
        assert wikilinks == []

    def test_extract_wikilinks_no_links(self):
        """Test response with no wikilinks"""
        response = """This is a response without any wikilinks."""
        wikilinks = HybridSmartRouterPrompt.extract_wikilinks(response)
        assert wikilinks == []

    # -------------------------------------------------------------------------
    # METADATA EXTRACTION TESTS
    # -------------------------------------------------------------------------

    def test_extract_metadata_complete(self):
        """Test complete metadata extraction"""
        response = """Detected Type: DOCUMENT
Confidence: HIGH

This is an invoice from AWS.

## Tags & Categorization
#document #invoice #vendor-aws #2024-november

## Suggested Connections
1. **[[Vendor Management]]** - Managing vendors
2. **[[Q4 Budget]]** - Budget tracking

## Content Quality Assessment
- **Needs Review**: yes"""

        metadata = HybridSmartRouterPrompt.extract_metadata(response)

        assert metadata["content_type"] == "document"
        assert metadata["confidence"] == "high"
        assert "document" in metadata["tags"]
        assert "invoice" in metadata["tags"]
        assert "Vendor Management" in metadata["wikilinks"]
        assert "Q4 Budget" in metadata["wikilinks"]
        assert metadata["needs_review"] is True

    def test_extract_metadata_minimal(self):
        """Test metadata extraction with minimal info"""
        response = """This is a basic response."""

        metadata = HybridSmartRouterPrompt.extract_metadata(response)

        assert "content_type" in metadata
        assert metadata["content_type"] == "unknown"
        assert "tags" in metadata
        assert "wikilinks" in metadata
        assert "confidence" in metadata
        assert metadata["needs_review"] is False

    def test_extract_metadata_confidence_levels(self):
        """Test confidence level extraction"""
        for confidence_level in ["HIGH", "MEDIUM", "LOW"]:
            response = f"""Detected Type: DOCUMENT
Confidence: {confidence_level}"""

            metadata = HybridSmartRouterPrompt.extract_metadata(response)
            assert metadata["confidence"] == confidence_level.lower()

    def test_extract_metadata_needs_review_no(self):
        """Test needs_review when explicitly set to no"""
        response = """## Content Quality Assessment
- **Needs Review**: no"""

        metadata = HybridSmartRouterPrompt.extract_metadata(response)
        assert metadata["needs_review"] is False

    def test_extract_metadata_needs_review_yes(self):
        """Test needs_review when explicitly set to yes"""
        response = """## Content Quality Assessment
- **Needs Review**: Yes"""

        metadata = HybridSmartRouterPrompt.extract_metadata(response)
        assert metadata["needs_review"] is True

    # -------------------------------------------------------------------------
    # INTEGRATION TESTS
    # -------------------------------------------------------------------------

    def test_full_document_response_parsing(self):
        """Test parsing a complete document response"""
        response = """Detected Type: DOCUMENT
Confidence: HIGH

# AWS Invoice - November 2024

## Document Metadata
| Metadata | Value |
|----------|-------|
| Document Type | invoice |
| Date | November 15, 2024 |
| Organization | Amazon Web Services |

## Structured Content
Service: EC2 Computing
Amount: $245.00
Period: November 1-30, 2024

## Tags & Categorization
#document #invoice #vendor-aws #cloud-services #2024-november #q4-expenses

## Suggested Wiki-Link Connections
1. **[[Vendor Management]]** - Because: This is an invoice from AWS
2. **[[Q4 Budget]]** - Because: Tagged with Q4 expenses
3. **[[Cloud Infrastructure Costs]]** - Because: Invoice details cloud services

## Content Quality Assessment
- **Clarity Score**: ★★★★★
- **Completeness**: complete
- **Confidence Level**: high
- **Needs Review**: no"""

        metadata = HybridSmartRouterPrompt.extract_metadata(response)

        # Validate all extracted metadata
        assert metadata["content_type"] == "document"
        assert metadata["confidence"] == "high"
        assert len(metadata["tags"]) >= 5
        assert "document" in metadata["tags"]
        assert "invoice" in metadata["tags"]
        assert "vendor-aws" in metadata["tags"]
        assert len(metadata["wikilinks"]) == 3
        assert "Vendor Management" in metadata["wikilinks"]
        assert metadata["needs_review"] is False

    def test_full_photo_response_parsing(self):
        """Test parsing a complete photo response"""
        response = """Detected Type: PHOTO
Confidence: MEDIUM

# Downtown Building: Modern Architecture

## Visual Summary
This photograph captures a modern glass building in the downtown area.

## Tags & Categorization
#photo #architecture #downtown #building #urban

## Suggested Connections
1. **[[Architecture Gallery]]** - Photo collection
2. **[[Downtown Area]]** - Location reference"""

        metadata = HybridSmartRouterPrompt.extract_metadata(response)

        assert metadata["content_type"] == "photo"
        assert metadata["confidence"] == "medium"
        assert "photo" in metadata["tags"]
        assert "architecture" in metadata["tags"]
        assert len(metadata["wikilinks"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
