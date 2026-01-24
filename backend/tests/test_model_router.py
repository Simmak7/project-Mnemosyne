"""
Integration tests for ModelRouter

Tests cover:
- Model selection logic (feature flags)
- Routing percentages (gradual rollout)
- Prompt selection logic
- Fallback behavior
- Health checks
- Error handling
"""

import pytest
import responses
from pathlib import Path
from unittest.mock import Mock, patch
import random
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from model_router import ModelRouter, ModelSelection, PromptSelection
from adapters.qwen_vision_adapter import QwenVisionAdapter
from adapters.llama_vision_adapter import LlamaVisionAdapter


class TestModelRouter:
    """Test suite for Model Router"""

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
    # INITIALIZATION TESTS
    # -------------------------------------------------------------------------

    def test_router_initialization_defaults(self):
        """Test router initialization with default values"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=False,
            new_model_rollout_percent=0,
            prompt_rollout_percent=0
        )

        assert router.ollama_host == "http://localhost:11434"
        assert router.use_new_model is False
        assert router.new_model_rollout_percent == 0
        assert router.prompt_rollout_percent == 0
        assert isinstance(router.llama_adapter, LlamaVisionAdapter)
        assert isinstance(router.qwen_adapter, QwenVisionAdapter)

    def test_router_initialization_new_model_enabled(self):
        """Test router initialization with new model enabled"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=100
        )

        assert router.use_new_model is True
        assert router.new_model_rollout_percent == 100

    def test_router_repr(self):
        """Test router string representation"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=25,
            prompt_rollout_percent=50
        )

        repr_str = repr(router)
        assert "ModelRouter" in repr_str
        assert "25" in repr_str  # rollout percent
        assert "50" in repr_str  # prompt rollout

    # -------------------------------------------------------------------------
    # MODEL SELECTION LOGIC TESTS
    # -------------------------------------------------------------------------

    def test_should_use_new_model_disabled(self):
        """Test that new model is not used when feature flag is disabled"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=False,
            new_model_rollout_percent=100  # Even at 100%, should not use
        )

        # Test multiple times to ensure consistency
        for _ in range(10):
            assert router._should_use_new_model() is False

    def test_should_use_new_model_zero_percent(self):
        """Test that new model is not used at 0% rollout"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=0
        )

        for _ in range(10):
            assert router._should_use_new_model() is False

    def test_should_use_new_model_hundred_percent(self):
        """Test that new model is always used at 100% rollout"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=100
        )

        for _ in range(10):
            assert router._should_use_new_model() is True

    @patch('model_router.random.randint')
    def test_should_use_new_model_25_percent(self, mock_randint):
        """Test 25% rollout probability"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=25
        )

        # Test cases: randint returns value, expected result
        test_cases = [
            (1, True),    # 1 <= 25, use new
            (25, True),   # 25 <= 25, use new
            (26, False),  # 26 > 25, use old
            (50, False),  # 50 > 25, use old
            (100, False)  # 100 > 25, use old
        ]

        for randint_value, expected in test_cases:
            mock_randint.return_value = randint_value
            result = router._should_use_new_model()
            assert result == expected, f"At rollout=25%, randint={randint_value} should return {expected}"

    @patch('model_router.random.randint')
    def test_should_use_new_model_75_percent(self, mock_randint):
        """Test 75% rollout probability"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=75
        )

        test_cases = [
            (1, True),    # Use new
            (50, True),   # Use new
            (75, True),   # Boundary - use new
            (76, False),  # Use old
            (100, False)  # Use old
        ]

        for randint_value, expected in test_cases:
            mock_randint.return_value = randint_value
            assert router._should_use_new_model() == expected

    # -------------------------------------------------------------------------
    # PROMPT SELECTION LOGIC TESTS
    # -------------------------------------------------------------------------

    def test_should_use_hybrid_prompt_old_model(self):
        """Test that hybrid prompt is never used with old model"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=False,
            prompt_rollout_percent=100
        )

        # Hybrid prompt should not be used with old model
        assert router._should_use_hybrid_prompt(using_new_model=False) is False

    def test_should_use_hybrid_prompt_zero_percent(self):
        """Test that hybrid prompt is not used at 0% rollout"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            prompt_rollout_percent=0
        )

        assert router._should_use_hybrid_prompt(using_new_model=True) is False

    def test_should_use_hybrid_prompt_hundred_percent(self):
        """Test that hybrid prompt is always used at 100% rollout"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            prompt_rollout_percent=100
        )

        assert router._should_use_hybrid_prompt(using_new_model=True) is True

    @patch('model_router.random.randint')
    def test_should_use_hybrid_prompt_50_percent(self, mock_randint):
        """Test 50% prompt rollout"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            prompt_rollout_percent=50
        )

        # Test boundary cases
        mock_randint.return_value = 25
        assert router._should_use_hybrid_prompt(using_new_model=True) is True

        mock_randint.return_value = 50
        assert router._should_use_hybrid_prompt(using_new_model=True) is True

        mock_randint.return_value = 51
        assert router._should_use_hybrid_prompt(using_new_model=True) is False

    def test_get_prompt_old_model(self):
        """Test prompt selection for old model"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=False,
            prompt_rollout_percent=100
        )

        prompt, selection = router._get_prompt(using_new_model=False)

        assert selection == PromptSelection.LEGACY
        assert "note-taking" in prompt.lower()

    def test_get_prompt_new_model_legacy(self):
        """Test legacy prompt selection for new model"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            prompt_rollout_percent=0
        )

        prompt, selection = router._get_prompt(using_new_model=True)

        assert selection == PromptSelection.LEGACY

    def test_get_prompt_new_model_hybrid(self):
        """Test hybrid prompt selection for new model"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            prompt_rollout_percent=100
        )

        prompt, selection = router._get_prompt(using_new_model=True)

        assert selection == PromptSelection.HYBRID
        assert "CONTENT TYPE DETECTION" in prompt
        assert "OBSIDIAN COMPATIBILITY" in prompt

    # -------------------------------------------------------------------------
    # IMAGE ANALYSIS INTEGRATION TESTS
    # -------------------------------------------------------------------------

    @responses.activate
    def test_analyze_image_old_model(self, test_image_path):
        """Test image analysis routing to old model"""
        # Mock Ollama API for old model
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": "Test analysis from old model",
                "eval_count": 100,
                "total_duration": 5000000000
            },
            status=200
        )

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=False,
            new_model_rollout_percent=0
        )

        result = router.analyze_image(
            image_path=test_image_path,
            timeout=300
        )

        assert result["status"] == "success"
        assert result["model_selection"] == "old"
        assert result["prompt_selection"] == "legacy"
        assert "old model" in result["response"]

    @responses.activate
    def test_analyze_image_new_model(self, test_image_path):
        """Test image analysis routing to new model"""
        # Mock Ollama API for new model
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": "Detected Type: DOCUMENT\nTest analysis from new model",
                "eval_count": 200,
                "total_duration": 7000000000
            },
            status=200
        )

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=100,
            prompt_rollout_percent=100
        )

        result = router.analyze_image(
            image_path=test_image_path,
            timeout=300
        )

        assert result["status"] == "success"
        assert result["model_selection"] == "new"
        assert result["prompt_selection"] == "hybrid"
        assert "content_metadata" in result

    @responses.activate
    def test_analyze_image_with_custom_prompt(self, test_image_path):
        """Test image analysis with custom prompt"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": "Custom prompt response",
                "eval_count": 150,
                "total_duration": 6000000000
            },
            status=200
        )

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=100
        )

        result = router.analyze_image(
            image_path=test_image_path,
            custom_prompt="This is a custom prompt",
            timeout=300
        )

        assert result["status"] == "success"
        assert result["prompt_selection"] == "custom"

    @responses.activate
    def test_analyze_image_metadata_extraction(self, test_image_path):
        """Test metadata extraction from hybrid prompt response"""
        hybrid_response = """Detected Type: DOCUMENT
Confidence: HIGH

# Test Document

## Tags & Categorization
#document #invoice #test

## Suggested Wiki-Link Connections
1. **[[Test Topic]]** - Testing"""

        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": hybrid_response,
                "eval_count": 300,
                "total_duration": 8000000000
            },
            status=200
        )

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=100,
            prompt_rollout_percent=100
        )

        result = router.analyze_image(
            image_path=test_image_path,
            timeout=300
        )

        assert result["status"] == "success"
        assert "content_metadata" in result
        assert result["content_metadata"]["content_type"] == "document"
        assert "document" in result["content_metadata"]["tags"]
        assert "Test Topic" in result["content_metadata"]["wikilinks"]

    # -------------------------------------------------------------------------
    # ERROR HANDLING TESTS
    # -------------------------------------------------------------------------

    def test_analyze_image_file_not_found(self):
        """Test error handling for missing file"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=False
        )

        result = router.analyze_image(
            image_path="/nonexistent/file.jpg",
            timeout=300
        )

        assert result["status"] == "error"
        assert "error" in result

    @responses.activate
    def test_analyze_image_api_error(self, test_image_path):
        """Test error handling for API errors"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            status=500,
            body="Internal server error"
        )

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=False
        )

        result = router.analyze_image(
            image_path=test_image_path,
            timeout=300
        )

        assert result["status"] == "error"
        assert "model_selection" in result

    # -------------------------------------------------------------------------
    # HEALTH CHECK TESTS
    # -------------------------------------------------------------------------

    @responses.activate
    def test_health_check_both_healthy(self):
        """Test health check when both models are available"""
        # Mock both model health checks
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            json={
                "models": [
                    {"name": "llama3.2-vision:11b"},
                    {"name": "qwen2.5vl:7b-q4_K_M"}
                ]
            },
            status=200
        )

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True
        )

        health = router.health_check()

        assert health["old_model"] is True
        assert health["new_model"] is True
        assert health["router"] is True

    @responses.activate
    def test_health_check_only_old_healthy(self):
        """Test health check when only old model is available"""
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

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True
        )

        health = router.health_check()

        assert health["old_model"] is True
        assert health["new_model"] is False
        assert health["router"] is True  # Router is healthy if old model works

    @responses.activate
    def test_health_check_config_included(self):
        """Test that health check includes configuration"""
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            json={"models": [{"name": "llama3.2-vision:11b"}]},
            status=200
        )

        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=25,
            prompt_rollout_percent=50
        )

        health = router.health_check()

        assert "config" in health
        assert health["config"]["use_new_model"] is True
        assert health["config"]["new_model_rollout_percent"] == 25
        assert health["config"]["prompt_rollout_percent"] == 50

    # -------------------------------------------------------------------------
    # GRADUAL ROLLOUT SIMULATION TESTS
    # -------------------------------------------------------------------------

    def test_rollout_distribution_25_percent(self):
        """Test that 25% rollout approximates 25% distribution over many calls"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=25
        )

        # Run 1000 selections
        selections = [router._should_use_new_model() for _ in range(1000)]
        new_model_count = sum(selections)
        new_model_percent = (new_model_count / 1000) * 100

        # Should be approximately 25% (allow ±10% margin due to randomness)
        assert 15 <= new_model_percent <= 35

    def test_rollout_distribution_75_percent(self):
        """Test that 75% rollout approximates 75% distribution"""
        router = ModelRouter(
            ollama_host="http://localhost:11434",
            use_new_model=True,
            new_model_rollout_percent=75
        )

        selections = [router._should_use_new_model() for _ in range(1000)]
        new_model_count = sum(selections)
        new_model_percent = (new_model_count / 1000) * 100

        # Should be approximately 75% (allow ±10% margin)
        assert 65 <= new_model_percent <= 85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
