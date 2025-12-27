"""
Sentiment Analysis Module

Provides NLP-based sentiment analysis for financial news and social media.
Supports transformer models (HuggingFace) with fallback to simpler methods.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# Check for available NLP libraries
TRANSFORMERS_AVAILABLE = False
TORCH_AVAILABLE = False
NLTK_AVAILABLE = False
VADER_AVAILABLE = False
TEXTBLOB_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
    logger.info(f"PyTorch {torch.__version__} available for NLP")
except ImportError:
    pass

try:
    import transformers
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
    logger.info(f"Transformers {transformers.__version__} available")
except ImportError:
    logger.info("Transformers not available")

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    pass

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    pass

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    pass


class SentimentLabel(Enum):
    """Sentiment classification labels"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    text: str
    label: SentimentLabel
    score: float  # -1 to 1 scale
    confidence: float  # 0 to 1
    details: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "label": self.label.value,
            "score": self.score,
            "confidence": self.confidence,
            "details": self.details
        }


class TextPreprocessor:
    """Preprocess text for sentiment analysis"""

    def __init__(
        self,
        lowercase: bool = True,
        remove_urls: bool = True,
        remove_mentions: bool = True,
        remove_hashtags: bool = False,
        remove_numbers: bool = False
    ):
        self.lowercase = lowercase
        self.remove_urls = remove_urls
        self.remove_mentions = remove_mentions
        self.remove_hashtags = remove_hashtags
        self.remove_numbers = remove_numbers

        # Financial-specific patterns
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.number_pattern = re.compile(r'\d+\.?\d*%?')
        self.ticker_pattern = re.compile(r'\$[A-Z]{1,5}')

    def preprocess(self, text: str) -> str:
        """Preprocess a single text"""
        if not isinstance(text, str):
            return ""

        # Remove URLs
        if self.remove_urls:
            text = self.url_pattern.sub('', text)

        # Remove mentions
        if self.remove_mentions:
            text = self.mention_pattern.sub('', text)

        # Keep or remove hashtags (but remove the # symbol)
        if self.remove_hashtags:
            text = self.hashtag_pattern.sub('', text)
        else:
            text = re.sub(r'#(\w+)', r'\1', text)

        # Remove numbers
        if self.remove_numbers:
            text = self.number_pattern.sub('', text)

        # Convert to lowercase
        if self.lowercase:
            text = text.lower()

        # Clean up whitespace
        text = ' '.join(text.split())

        return text

    def preprocess_batch(self, texts: List[str]) -> List[str]:
        """Preprocess a batch of texts"""
        return [self.preprocess(t) for t in texts]


class TransformerSentimentAnalyzer:
    """
    Sentiment analyzer using HuggingFace transformers.

    Uses FinBERT or other financial sentiment models when available.
    """

    # Financial sentiment models (in order of preference)
    FINANCIAL_MODELS = [
        "ProsusAI/finbert",
        "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
        "yiyanghkust/finbert-tone",
    ]

    # General sentiment models (fallback)
    GENERAL_MODELS = [
        "distilbert-base-uncased-finetuned-sst-2-english",
        "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "nlptown/bert-base-multilingual-uncased-sentiment",
    ]

    def __init__(
        self,
        model_name: Optional[str] = None,
        use_financial_model: bool = True,
        max_length: int = 512,
        batch_size: int = 16,
        device: str = "cpu"
    ):
        self.model_name = model_name
        self.use_financial_model = use_financial_model
        self.max_length = max_length
        self.batch_size = batch_size
        self.device = device

        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self.preprocessor = TextPreprocessor()

        self._initialized = False

    def _initialize(self):
        """Initialize the model (lazy loading)"""
        if self._initialized:
            return

        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library not available")

        # Try to load a model
        models_to_try = []

        if self.model_name:
            models_to_try.append(self.model_name)

        if self.use_financial_model:
            models_to_try.extend(self.FINANCIAL_MODELS)

        models_to_try.extend(self.GENERAL_MODELS)

        for model_name in models_to_try:
            try:
                logger.info(f"Trying to load model: {model_name}")
                self.pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    device=0 if self.device == "cuda" and TORCH_AVAILABLE else -1,
                    truncation=True,
                    max_length=self.max_length
                )
                self.model_name = model_name
                logger.info(f"Successfully loaded: {model_name}")
                self._initialized = True
                return
            except Exception as e:
                logger.warning(f"Could not load {model_name}: {e}")
                continue

        raise RuntimeError("Could not load any sentiment model")

    def analyze(
        self,
        texts: Union[str, List[str]],
        preprocess: bool = True
    ) -> List[SentimentResult]:
        """
        Analyze sentiment of text(s).

        Args:
            texts: Single text or list of texts
            preprocess: Whether to preprocess texts

        Returns:
            List of SentimentResult objects
        """
        self._initialize()

        if isinstance(texts, str):
            texts = [texts]

        # Preprocess
        if preprocess:
            texts = self.preprocessor.preprocess_batch(texts)

        # Analyze in batches
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_results = self.pipeline(batch)

            for text, result in zip(batch, batch_results):
                # Normalize the result
                label_str = result['label'].lower()
                score_raw = result['score']

                # Convert to our standard format
                if 'positive' in label_str or label_str in ['pos', '5', '4']:
                    score = score_raw
                    if score > 0.8:
                        label = SentimentLabel.VERY_POSITIVE
                    else:
                        label = SentimentLabel.POSITIVE
                elif 'negative' in label_str or label_str in ['neg', '1', '2']:
                    score = -score_raw
                    if score < -0.8:
                        label = SentimentLabel.VERY_NEGATIVE
                    else:
                        label = SentimentLabel.NEGATIVE
                else:
                    score = 0.0
                    label = SentimentLabel.NEUTRAL

                results.append(SentimentResult(
                    text=text,
                    label=label,
                    score=score,
                    confidence=abs(score_raw),
                    details={"raw_label": result['label'], "raw_score": result['score']}
                ))

        return results

    def analyze_financial_news(
        self,
        headlines: List[str],
        return_aggregate: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze financial news headlines and aggregate results.

        Args:
            headlines: List of news headlines
            return_aggregate: Whether to return aggregated metrics

        Returns:
            Analysis results with optional aggregation
        """
        results = self.analyze(headlines)

        response = {
            "results": [r.to_dict() for r in results],
            "count": len(results)
        }

        if return_aggregate:
            scores = [r.score for r in results]
            confidences = [r.confidence for r in results]

            # Count labels
            label_counts = {}
            for r in results:
                label_counts[r.label.value] = label_counts.get(r.label.value, 0) + 1

            response["aggregate"] = {
                "mean_score": float(np.mean(scores)),
                "std_score": float(np.std(scores)),
                "mean_confidence": float(np.mean(confidences)),
                "bullish_ratio": sum(1 for s in scores if s > 0.3) / len(scores),
                "bearish_ratio": sum(1 for s in scores if s < -0.3) / len(scores),
                "label_distribution": label_counts
            }

        return response


class VaderSentimentAnalyzer:
    """
    VADER-based sentiment analyzer.

    Fast and effective for social media and short texts.
    """

    def __init__(self):
        if not VADER_AVAILABLE:
            raise ImportError("vaderSentiment not available")

        self.analyzer = SentimentIntensityAnalyzer()
        self.preprocessor = TextPreprocessor(lowercase=False)

    def analyze(
        self,
        texts: Union[str, List[str]],
        preprocess: bool = True
    ) -> List[SentimentResult]:
        """Analyze sentiment using VADER"""
        if isinstance(texts, str):
            texts = [texts]

        if preprocess:
            texts = self.preprocessor.preprocess_batch(texts)

        results = []
        for text in texts:
            scores = self.analyzer.polarity_scores(text)
            compound = scores['compound']

            # Determine label
            if compound >= 0.5:
                label = SentimentLabel.VERY_POSITIVE
            elif compound >= 0.05:
                label = SentimentLabel.POSITIVE
            elif compound <= -0.5:
                label = SentimentLabel.VERY_NEGATIVE
            elif compound <= -0.05:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL

            results.append(SentimentResult(
                text=text,
                label=label,
                score=compound,
                confidence=abs(compound),
                details={
                    "positive": scores['pos'],
                    "negative": scores['neg'],
                    "neutral": scores['neu']
                }
            ))

        return results


class TextBlobSentimentAnalyzer:
    """TextBlob-based sentiment analyzer"""

    def __init__(self):
        if not TEXTBLOB_AVAILABLE:
            raise ImportError("TextBlob not available")

        self.preprocessor = TextPreprocessor()

    def analyze(
        self,
        texts: Union[str, List[str]],
        preprocess: bool = True
    ) -> List[SentimentResult]:
        """Analyze sentiment using TextBlob"""
        if isinstance(texts, str):
            texts = [texts]

        if preprocess:
            texts = self.preprocessor.preprocess_batch(texts)

        results = []
        for text in texts:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Determine label
            if polarity >= 0.5:
                label = SentimentLabel.VERY_POSITIVE
            elif polarity >= 0.1:
                label = SentimentLabel.POSITIVE
            elif polarity <= -0.5:
                label = SentimentLabel.VERY_NEGATIVE
            elif polarity <= -0.1:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL

            results.append(SentimentResult(
                text=text,
                label=label,
                score=polarity,
                confidence=abs(polarity) * (1 - subjectivity * 0.3),
                details={
                    "polarity": polarity,
                    "subjectivity": subjectivity
                }
            ))

        return results


class FinancialKeywordSentimentAnalyzer:
    """
    Simple keyword-based sentiment analyzer for financial text.

    Works without any external NLP libraries.
    """

    # Financial sentiment keywords
    POSITIVE_KEYWORDS = {
        'strong': 2, 'bullish': 3, 'surge': 2, 'rally': 2, 'gain': 1,
        'profit': 2, 'growth': 2, 'upgrade': 2, 'beat': 2, 'exceed': 2,
        'outperform': 2, 'buy': 1, 'long': 1, 'opportunity': 1,
        'positive': 1, 'optimistic': 2, 'momentum': 1, 'breakout': 2,
        'record': 2, 'high': 1, 'up': 1, 'increase': 1, 'rise': 1
    }

    NEGATIVE_KEYWORDS = {
        'weak': -2, 'bearish': -3, 'crash': -3, 'plunge': -2, 'drop': -1,
        'loss': -2, 'decline': -2, 'downgrade': -2, 'miss': -2, 'below': -1,
        'underperform': -2, 'sell': -1, 'short': -1, 'risk': -1,
        'negative': -1, 'pessimistic': -2, 'resistance': -1, 'breakdown': -2,
        'low': -1, 'down': -1, 'decrease': -1, 'fall': -1, 'fear': -2,
        'concern': -1, 'warning': -2, 'bankruptcy': -3, 'fraud': -3
    }

    def __init__(self):
        self.preprocessor = TextPreprocessor()

    def analyze(
        self,
        texts: Union[str, List[str]],
        preprocess: bool = True
    ) -> List[SentimentResult]:
        """Analyze sentiment using keyword matching"""
        if isinstance(texts, str):
            texts = [texts]

        if preprocess:
            texts = self.preprocessor.preprocess_batch(texts)

        results = []
        for text in texts:
            words = text.lower().split()
            total_score = 0
            matched_keywords = []

            for word in words:
                if word in self.POSITIVE_KEYWORDS:
                    total_score += self.POSITIVE_KEYWORDS[word]
                    matched_keywords.append((word, self.POSITIVE_KEYWORDS[word]))
                elif word in self.NEGATIVE_KEYWORDS:
                    total_score += self.NEGATIVE_KEYWORDS[word]
                    matched_keywords.append((word, self.NEGATIVE_KEYWORDS[word]))

            # Normalize score to -1 to 1
            max_possible = len(words) * 3  # Max weight is 3
            if max_possible > 0:
                normalized_score = total_score / max_possible
                normalized_score = max(-1, min(1, normalized_score * 5))  # Scale up
            else:
                normalized_score = 0

            # Determine label
            if normalized_score >= 0.5:
                label = SentimentLabel.VERY_POSITIVE
            elif normalized_score >= 0.1:
                label = SentimentLabel.POSITIVE
            elif normalized_score <= -0.5:
                label = SentimentLabel.VERY_NEGATIVE
            elif normalized_score <= -0.1:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL

            results.append(SentimentResult(
                text=text,
                label=label,
                score=normalized_score,
                confidence=min(1.0, len(matched_keywords) / 5),
                details={"matched_keywords": matched_keywords}
            ))

        return results


class SentimentAnalyzerFactory:
    """Factory for creating sentiment analyzers based on availability"""

    @staticmethod
    def get_best_analyzer(
        prefer_transformer: bool = True,
        financial_domain: bool = True
    ):
        """
        Get the best available sentiment analyzer.

        Args:
            prefer_transformer: Prefer transformer models if available
            financial_domain: Use financial-specific models/keywords

        Returns:
            A sentiment analyzer instance
        """
        if prefer_transformer and TRANSFORMERS_AVAILABLE and TORCH_AVAILABLE:
            try:
                analyzer = TransformerSentimentAnalyzer(
                    use_financial_model=financial_domain
                )
                # Test initialization
                analyzer._initialize()
                logger.info("Using TransformerSentimentAnalyzer")
                return analyzer
            except Exception as e:
                logger.warning(f"Transformer analyzer failed: {e}")

        if VADER_AVAILABLE:
            logger.info("Using VaderSentimentAnalyzer")
            return VaderSentimentAnalyzer()

        if TEXTBLOB_AVAILABLE:
            logger.info("Using TextBlobSentimentAnalyzer")
            return TextBlobSentimentAnalyzer()

        # Fallback to keyword-based
        logger.info("Using FinancialKeywordSentimentAnalyzer")
        return FinancialKeywordSentimentAnalyzer()


def get_sentiment_analyzer(financial: bool = True):
    """Convenience function to get a sentiment analyzer"""
    return SentimentAnalyzerFactory.get_best_analyzer(
        prefer_transformer=True,
        financial_domain=financial
    )
