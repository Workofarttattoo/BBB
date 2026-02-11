import pytest
import sys
import os

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from blank_business_builder.all_features_implementation import SentimentAnalyzer

@pytest.mark.asyncio
class TestSentimentAnalyzer:
    """Tests for the SentimentAnalyzer class."""

    async def test_analyze_feedback_positive(self):
        """Test that positive feedback is correctly identified."""
        analyzer = SentimentAnalyzer()
        text = "This product is great and amazing."
        result = await analyzer.analyze_feedback(text)

        assert result["sentiment"] == "positive"
        assert result["score"] > 0.5
        assert result["text"] == text
        # positive count = 2 ('great', 'amazing'), negative = 0
        # score = 0.5 + (2 * 0.15) = 0.8
        assert result["score"] == 0.8

    async def test_analyze_feedback_negative(self):
        """Test that negative feedback is correctly identified."""
        analyzer = SentimentAnalyzer()
        text = "This service is terrible."
        result = await analyzer.analyze_feedback(text)

        assert result["sentiment"] == "negative"
        assert result["score"] < 0.5
        assert result["text"] == text
        # positive count = 0, negative = 1 ('terrible')
        # score = 0.5 - (1 * 0.15) = 0.35
        assert result["score"] == 0.35

    async def test_analyze_feedback_neutral_mixed(self):
        """Test that mixed feedback with equal counts is neutral."""
        analyzer = SentimentAnalyzer()
        text = "I love the product but hate the price."
        result = await analyzer.analyze_feedback(text)

        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.5
        # positive ('love') == negative ('hate')

    async def test_analyze_feedback_neutral_no_keywords(self):
        """Test that feedback with no keywords is neutral."""
        analyzer = SentimentAnalyzer()
        text = "It is a product."
        result = await analyzer.analyze_feedback(text)

        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.5

    async def test_analyze_feedback_score_cap_positive(self):
        """Test that the score is capped at 1.0 for very positive feedback."""
        analyzer = SentimentAnalyzer()
        # 5 positive words: great, excellent, amazing, love, fantastic
        text = "great excellent amazing love fantastic"
        result = await analyzer.analyze_feedback(text)

        assert result["sentiment"] == "positive"
        assert result["score"] == 1.0

    async def test_analyze_feedback_score_cap_negative(self):
        """Test that the score is capped at 0.0 for very negative feedback."""
        analyzer = SentimentAnalyzer()
        # 5 negative words: bad, terrible, awful, hate, poor
        text = "bad terrible awful hate poor"
        result = await analyzer.analyze_feedback(text)

        assert result["sentiment"] == "negative"
        assert result["score"] == 0.0

    async def test_analyze_feedback_structure(self):
        """Test the structure of the returned dictionary."""
        analyzer = SentimentAnalyzer()
        text = "Test"
        result = await analyzer.analyze_feedback(text)

        required_keys = ["text", "sentiment", "score", "confidence", "key_phrases"]
        for key in required_keys:
            assert key in result

        assert isinstance(result["key_phrases"], list)
