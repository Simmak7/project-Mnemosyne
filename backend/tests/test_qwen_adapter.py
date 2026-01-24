"""
Unit tests for QwenVisionAdapter

Tests cover:
- Health checks
- Image analysis
- Error handling
- Response parsing
"""

import pytest
import responses
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from adapters.qwen_vision_adapter import QwenVisionAdapter


class TestQwenVisionAdapter:
    """Test suite for Qwen Vision Adapter"""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance for testing"""
        return QwenVisionAdapter(
            ollama_host="http://localhost:11434",
            model_name="qwen2.5vl:7b-q4_K_M"
        )

    @pytest.fixture
    def test_image_path(self, tmp_path):
        """Create a temporary test image file"""
        test_img = tmp_path / "test.jpg"
        # Create a minimal valid JPEG file (1x1 pixel)
        test_img.write_bytes(
            b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xFF\xDB\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09'
            b'\x08\x0A\x0C\x14\x0D\x0C\x0B\x0B\x0C\x19\x12\x13\x0F\x14\x1D\x1A\x1F'
            b'\x1E\x1D\x1A\x1C\x1C\x20\x24\x2E\x27\x20\x22\x2C\x23\x1C\x1C\x28\x37'
            b'\x29\x2C\x30\x31\x34\x34\x34\x1F\x27\x39\x3D\x38\x32\x3C\x2E\x33\x34'
            b'\x32\xFF\xC0\x00\x0B\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00'
            b'\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\xFF\xDA\x00\x08\x01\x01\x00\x00\x3F\x00\x7F\xFF\xD9'
        )
        return str(test_img)

    # -------------------------------------------------------------------------
    # HEALTH CHECK TESTS
    # -------------------------------------------------------------------------

    @responses.activate
    def test_health_check_success(self, adapter):
        """Test health check when model is available"""
        # Mock /api/tags endpoint
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            json={
                "models": [
                    {"name": "qwen2.5vl:7b-q4_K_M"},
                    {"name": "llama3.2-vision:11b"}
                ]
            },
            status=200
        )

        result = adapter.health_check()
        assert result is True

    @responses.activate
    def test_health_check_model_not_found(self, adapter):
        """Test health check when model is not available"""
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            json={
                "models": [
                    {"name": "llama3.2-vision:11b"}
                ]
            },
            status=200
        )

        result = adapter.health_check()
        assert result is False

    @responses.activate
    def test_health_check_server_error(self, adapter):
        """Test health check when server returns error"""
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            status=500
        )

        result = adapter.health_check()
        assert result is False

    @responses.activate
    def test_health_check_connection_error(self, adapter):
        """Test health check when connection fails"""
        # Don't add any mock response - will raise ConnectionError
        result = adapter.health_check()
        assert result is False

    # -------------------------------------------------------------------------
    # IMAGE ANALYSIS TESTS
    # -------------------------------------------------------------------------

    @responses.activate
    def test_analyze_image_success(self, adapter, test_image_path):
        """Test successful image analysis"""
        # Mock Ollama API response
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": "This is a test image containing a document.",
                "eval_count": 150,
                "total_duration": 8500000000  # 8.5 seconds in nanoseconds
            },
            status=200
        )

        result = adapter.analyze_image(
            image_path=test_image_path,
            prompt="Analyze this image"
        )

        assert result["status"] == "success"
        assert "This is a test image" in result["response"]
        assert result["model"] == "qwen2.5vl:7b-q4_K_M"
        assert result["eval_count"] == 150
        assert result["total_duration_s"] == pytest.approx(8.5, rel=0.1)

    @responses.activate
    def test_analyze_image_with_comprehensive_response(self, adapter, test_image_path):
        """Test analysis with Hybrid Smart-Router prompt response"""
        hybrid_response = """Detected Type: DOCUMENT
Confidence: HIGH

# Invoice Analysis

## Document Metadata
| Metadata | Value |
|----------|-------|
| Document Type | invoice |
| Date | November 2024 |
| Organization | AWS |

## Tags & Categorization
#document #invoice #vendor-aws #2024-november

## Suggested Wiki-Link Connections
1. **[[Vendor Management]]** - Because: This is an invoice from AWS
2. **[[Q4 Budget]]** - Because: Tagged with Q4 expenses"""

        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": hybrid_response,
                "eval_count": 450,
                "total_duration": 9200000000
            },
            status=200
        )

        result = adapter.analyze_image(
            image_path=test_image_path,
            prompt="Analyze this image"
        )

        assert result["status"] == "success"
        assert "DOCUMENT" in result["response"]
        assert "#document" in result["response"]
        assert "[[Vendor Management]]" in result["response"]

    def test_analyze_image_file_not_found(self, adapter):
        """Test analysis with non-existent image file"""
        with pytest.raises(FileNotFoundError):
            adapter.analyze_image(
                image_path="/nonexistent/image.jpg",
                prompt="Analyze this"
            )

    @responses.activate
    def test_analyze_image_model_not_found(self, adapter, test_image_path):
        """Test analysis when model is not available"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            status=404,
            body="model 'qwen2.5vl:7b-q4_K_M' not found"
        )

        result = adapter.analyze_image(
            image_path=test_image_path,
            prompt="Analyze this"
        )

        assert result["status"] == "error"
        assert "not found" in result["error"]
        assert result["http_status"] == 404
        assert "docker-compose exec ollama ollama pull" in result["error"]

    @responses.activate
    def test_analyze_image_timeout(self, adapter, test_image_path):
        """Test analysis with timeout"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            body=requests.Timeout()
        )

        result = adapter.analyze_image(
            image_path=test_image_path,
            prompt="Analyze this",
            timeout=10
        )

        assert result["status"] == "error"
        assert "timeout" in result["error"].lower()

    @responses.activate
    def test_analyze_image_server_error(self, adapter, test_image_path):
        """Test analysis with server error"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            status=500,
            body="Internal server error"
        )

        result = adapter.analyze_image(
            image_path=test_image_path,
            prompt="Analyze this"
        )

        assert result["status"] == "error"
        assert result["http_status"] == 500
        assert "500" in result["error"]

    # -------------------------------------------------------------------------
    # CONFIGURATION TESTS
    # -------------------------------------------------------------------------

    def test_adapter_initialization(self):
        """Test adapter initialization with custom config"""
        adapter = QwenVisionAdapter(
            ollama_host="http://custom-host:9999",
            model_name="qwen2.5vl:custom"
        )

        assert adapter.ollama_host == "http://custom-host:9999"
        assert adapter.model_name == "qwen2.5vl:custom"
        assert adapter.api_url == "http://custom-host:9999/api/generate"

    def test_adapter_repr(self, adapter):
        """Test adapter string representation"""
        repr_str = repr(adapter)
        assert "QwenVisionAdapter" in repr_str
        assert "qwen2.5vl:7b-q4_K_M" in repr_str
        assert "localhost:11434" in repr_str

    # -------------------------------------------------------------------------
    # PAYLOAD VALIDATION TESTS
    # -------------------------------------------------------------------------

    @responses.activate
    def test_analyze_image_payload_structure(self, adapter, test_image_path):
        """Test that request payload has correct structure"""
        def request_callback(request):
            payload = json.loads(request.body)

            # Validate payload structure
            assert "model" in payload
            assert payload["model"] == "qwen2.5vl:7b-q4_K_M"
            assert "prompt" in payload
            assert "images" in payload
            assert isinstance(payload["images"], list)
            assert len(payload["images"]) > 0
            assert "stream" in payload
            assert payload["stream"] is False
            assert "options" in payload

            # Validate options
            options = payload["options"]
            assert "num_predict" in options
            assert options["num_predict"] == 2048
            assert "temperature" in options
            assert "top_p" in options
            assert "top_k" in options

            return (200, {}, json.dumps({
                "response": "Test response",
                "eval_count": 100,
                "total_duration": 5000000000
            }))

        responses.add_callback(
            responses.POST,
            "http://localhost:11434/api/generate",
            callback=request_callback,
            content_type="application/json"
        )

        result = adapter.analyze_image(
            image_path=test_image_path,
            prompt="Test prompt"
        )

        assert result["status"] == "success"


# Import requests for the test
import requests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
