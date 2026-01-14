"""
NLP models for sentiment analysis of financial news and social media data.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification, AutoConfig
from transformers import pipeline, AutoModelForCausalLM, BitsAndBytesConfig
import torch

# PEFT for LoRA adapter support (FinGPT)
try:
    from peft import PeftModel, PeftConfig
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
import re
from typing import List, Dict, Union, Tuple, Optional, Any
import logging
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Preprocess text data for sentiment analysis"""
    
    def __init__(self, lowercase: bool = True, remove_urls: bool = True, 
                 remove_stopwords: bool = True, remove_punctuation: bool = True):
        """
        Initialize the text preprocessor
        
        Args:
            lowercase: Whether to convert text to lowercase
            remove_urls: Whether to remove URLs
            remove_stopwords: Whether to remove stopwords
            remove_punctuation: Whether to remove punctuation
        """
        self.lowercase = lowercase
        self.remove_urls = remove_urls
        self.remove_stopwords = remove_stopwords
        self.remove_punctuation = remove_punctuation
        self.stop_words = set(stopwords.words('english'))
        
    def preprocess(self, text: str) -> str:
        """
        Preprocess a single text string
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        if self.lowercase:
            text = text.lower()
        
        # Remove URLs
        if self.remove_urls:
            text = re.sub(r'http\S+', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        if self.remove_stopwords:
            tokens = [token for token in tokens if token not in self.stop_words]
        
        # Remove punctuation
        if self.remove_punctuation:
            tokens = [token for token in tokens if token not in string.punctuation]
        
        # Join tokens back into a single string
        preprocessed_text = ' '.join(tokens)
        
        return preprocessed_text
    
    def preprocess_batch(self, texts: List[str]) -> List[str]:
        """
        Preprocess a batch of text strings
        
        Args:
            texts: List of input texts
            
        Returns:
            List of preprocessed texts
        """
        return [self.preprocess(text) for text in texts]


class TransformerSentimentAnalyzer:
    """
    Sentiment analysis using pre-trained transformer models
    """
    
    def __init__(
        self, 
        model_name: str = 'distilbert-base-uncased-finetuned-sst-2-english',
        max_length: int = 128,
        batch_size: int = 16,
        device: str = None
    ):
        """
        Initialize the transformer sentiment analyzer
        
        Args:
            model_name: Name of the pre-trained model
            max_length: Maximum sequence length
            batch_size: Batch size for inference
            device: Device to use (None for auto-detection)
        """
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        
        # Determine device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        # In TensorFlow environment, we use TF models
        self.use_tensorflow = True
        
        # Load tokenizer and model
        self.tokenizer = None
        self.model = None
        self.sentiment_pipeline = None
        
        # Text preprocessor
        self.preprocessor = TextPreprocessor(
            lowercase=True,
            remove_urls=True,
            remove_stopwords=False,  # Pre-trained models often handle stopwords well
            remove_punctuation=False  # Keep punctuation for better model performance
        )
    
    def load_model(self) -> 'TransformerSentimentAnalyzer':
        """
        Load the pre-trained model and tokenizer
        
        Returns:
            Self
        """
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model
            if self.use_tensorflow:
                config = AutoConfig.from_pretrained(self.model_name)
                self.model = TFAutoModelForSequenceClassification.from_pretrained(
                    self.model_name, 
                    config=config
                )
            
            # Create sentiment pipeline for easier inference
            self.sentiment_pipeline = pipeline(
                task='sentiment-analysis',
                model=self.model_name,
                tokenizer=self.tokenizer,
                device=0 if self.device == 'cuda' else -1
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
        
        return self
    
    def predict(self, texts: Union[str, List[str]], preprocess: bool = True) -> List[Dict[str, Union[str, float]]]:
        """
        Predict sentiment for one or more texts
        
        Args:
            texts: Input text or list of texts
            preprocess: Whether to preprocess the input texts
            
        Returns:
            List of dictionaries containing sentiment prediction results
        """
        if self.sentiment_pipeline is None:
            self.load_model()
        
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
        
        # Preprocess texts if needed
        if preprocess:
            texts = self.preprocessor.preprocess_batch(texts)
        
        # Predict sentiment
        results = self.sentiment_pipeline(texts, batch_size=self.batch_size)
        
        # Format results for consistency
        formatted_results = []
        for i, result in enumerate(results):
            # Standardize result format
            score = result['score']
            label = result['label']
            
            # Map label to consistent format
            sentiment = "positive" if "positive" in label.lower() else "negative"
            
            # For negative sentiment, invert the score to keep -1 to 1 range
            sentiment_score = score if sentiment == "positive" else -score
            
            formatted_results.append({
                'text': texts[i],
                'sentiment': sentiment,
                'score': sentiment_score,
                'confidence': score
            })
        
        return formatted_results
    
    def analyze_batch(self, df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
        """
        Analyze sentiment for a batch of texts in a DataFrame
        
        Args:
            df: DataFrame containing texts
            text_column: Name of the column containing the texts
            
        Returns:
            DataFrame with added sentiment analysis columns
        """
        # Extract texts from the DataFrame
        texts = df[text_column].tolist()
        
        # Predict sentiment
        results = self.predict(texts)
        
        # Add results to a new DataFrame
        result_df = pd.DataFrame(results)
        
        # Combine with original DataFrame
        combined_df = pd.concat([df.reset_index(drop=True), result_df.drop('text', axis=1)], axis=1)
        
        return combined_df


class FinGPTSentimentAnalyzer:
    """
    FinGPT-enhanced sentiment analyzer with financial domain expertise.

    Uses LoRA adapters trained on financial data for superior sentiment
    analysis of financial news, earnings calls, and market commentary.

    Supported FinGPT models:
    - FinGPT/fingpt-sentiment_llama2-13b_lora (Llama-2 based)
    - FinGPT/fingpt-forecaster_dowjones_llama2-7b_lora (Forecasting)

    Usage:
        analyzer = FinGPTSentimentAnalyzer()
        analyzer.load_model()
        results = analyzer.analyze_financial_text("Apple beats Q4 earnings expectations")
    """

    # Financial sentiment labels mapping
    SENTIMENT_LABELS = {
        'positive': 1.0,
        'negative': -1.0,
        'neutral': 0.0,
        'strongly positive': 1.0,
        'strongly negative': -1.0,
        'mildly positive': 0.5,
        'mildly negative': -0.5
    }

    def __init__(
        self,
        base_model: str = "meta-llama/Llama-2-7b-hf",
        lora_weights: str = "FinGPT/fingpt-sentiment_llama2-7b_lora",
        max_length: int = 512,
        load_in_8bit: bool = True,
        load_in_4bit: bool = False,
        device_map: str = "auto"
    ):
        """
        Initialize the FinGPT sentiment analyzer.

        Args:
            base_model: Base LLM model name (Llama-2 recommended)
            lora_weights: FinGPT LoRA adapter weights path
            max_length: Maximum sequence length for tokenization
            load_in_8bit: Use 8-bit quantization (reduces memory)
            load_in_4bit: Use 4-bit quantization (further reduces memory)
            device_map: Device mapping strategy ('auto', 'cpu', 'cuda')
        """
        self.base_model = base_model
        self.lora_weights = lora_weights
        self.max_length = max_length
        self.load_in_8bit = load_in_8bit
        self.load_in_4bit = load_in_4bit
        self.device_map = device_map

        self.model = None
        self.tokenizer = None
        self.available = PEFT_AVAILABLE

        if not self.available:
            logger.warning(
                "PEFT library not available. Install with: pip install peft\n"
                "FinGPT features will be disabled."
            )

    def load_model(self) -> 'FinGPTSentimentAnalyzer':
        """
        Load the base model with FinGPT LoRA adapters.

        Returns:
            Self for method chaining
        """
        if not self.available:
            logger.error("Cannot load FinGPT model - PEFT not available")
            return self

        try:
            logger.info(f"Loading FinGPT model: {self.base_model} with LoRA: {self.lora_weights}")

            # Configure quantization
            quantization_config = None
            if self.load_in_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True
                )
            elif self.load_in_8bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True
                )

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model,
                trust_remote_code=True
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load base model with quantization
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                quantization_config=quantization_config,
                device_map=self.device_map,
                trust_remote_code=True,
                torch_dtype=torch.float16
            )

            # Load LoRA adapter
            self.model = PeftModel.from_pretrained(
                base_model,
                self.lora_weights,
                torch_dtype=torch.float16
            )

            # Set to evaluation mode
            self.model.eval()

            logger.info("FinGPT model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading FinGPT model: {str(e)}")
            self.model = None

        return self

    def _create_prompt(self, text: str, instruction_type: str = "sentiment") -> str:
        """
        Create a FinGPT-style instruction prompt.

        Args:
            text: The financial text to analyze
            instruction_type: Type of analysis ('sentiment', 'summary', 'forecast')

        Returns:
            Formatted prompt string
        """
        if instruction_type == "sentiment":
            prompt = (
                "Instruction: What is the sentiment of this news? "
                "Please choose an answer from {negative/neutral/positive}.\n"
                f"Input: {text}\n"
                "Answer: "
            )
        elif instruction_type == "detailed_sentiment":
            prompt = (
                "Instruction: Analyze the sentiment of this financial news. "
                "Choose from {strongly negative/mildly negative/neutral/mildly positive/strongly positive}.\n"
                f"Input: {text}\n"
                "Answer: "
            )
        elif instruction_type == "summary":
            prompt = (
                "Instruction: Summarize the key financial implications of this news.\n"
                f"Input: {text}\n"
                "Summary: "
            )
        else:
            prompt = f"Input: {text}\nOutput: "

        return prompt

    def analyze_financial_text(
        self,
        texts: Union[str, List[str]],
        detailed: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment of financial text(s).

        Args:
            texts: Single text or list of texts to analyze
            detailed: Use detailed sentiment labels (5-point scale)

        Returns:
            List of analysis results with sentiment and scores
        """
        if self.model is None:
            logger.warning("Model not loaded. Attempting to load...")
            self.load_model()

        if self.model is None:
            # Return fallback results
            return self._fallback_analysis(texts)

        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]

        results = []
        instruction_type = "detailed_sentiment" if detailed else "sentiment"

        for text in texts:
            try:
                # Create prompt
                prompt = self._create_prompt(text, instruction_type)

                # Tokenize
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    max_length=self.max_length,
                    truncation=True,
                    padding=True
                )

                # Move to device
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}

                # Generate response
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=32,
                        do_sample=False,
                        temperature=0.1,
                        pad_token_id=self.tokenizer.pad_token_id
                    )

                # Decode response
                response = self.tokenizer.decode(
                    outputs[0][inputs['input_ids'].shape[1]:],
                    skip_special_tokens=True
                ).strip().lower()

                # Parse sentiment from response
                sentiment, score = self._parse_sentiment(response)

                results.append({
                    'text': text[:200] + '...' if len(text) > 200 else text,
                    'sentiment': sentiment,
                    'score': score,
                    'raw_response': response,
                    'model': 'fingpt'
                })

            except Exception as e:
                logger.error(f"Error analyzing text: {str(e)}")
                results.append({
                    'text': text[:200] + '...' if len(text) > 200 else text,
                    'sentiment': 'neutral',
                    'score': 0.0,
                    'error': str(e),
                    'model': 'fingpt'
                })

        return results

    def _parse_sentiment(self, response: str) -> Tuple[str, float]:
        """
        Parse sentiment from model response.

        Args:
            response: Raw model response text

        Returns:
            Tuple of (sentiment_label, sentiment_score)
        """
        response = response.lower().strip()

        # Check for known sentiment labels
        for label, score in self.SENTIMENT_LABELS.items():
            if label in response:
                return label, score

        # Fallback parsing
        if 'positive' in response:
            return 'positive', 1.0
        elif 'negative' in response:
            return 'negative', -1.0
        else:
            return 'neutral', 0.0

    def _fallback_analysis(self, texts: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Fallback sentiment analysis when FinGPT model is unavailable.
        Uses the standard TransformerSentimentAnalyzer.

        Args:
            texts: Text(s) to analyze

        Returns:
            List of analysis results
        """
        logger.warning("Using fallback sentiment analysis (FinGPT unavailable)")

        # Use standard transformer analyzer as fallback
        fallback_analyzer = TransformerSentimentAnalyzer()
        results = fallback_analyzer.predict(texts)

        # Add model identifier
        for result in results:
            result['model'] = 'fallback_transformer'

        return results

    def analyze_earnings_call(
        self,
        transcript: str,
        chunk_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of an earnings call transcript.

        Breaks transcript into chunks and analyzes each, then aggregates.

        Args:
            transcript: Full earnings call transcript
            chunk_size: Size of text chunks to analyze

        Returns:
            Aggregated sentiment analysis with breakdown
        """
        # Split transcript into manageable chunks
        words = transcript.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)

        # Analyze each chunk
        chunk_results = self.analyze_financial_text(chunks, detailed=True)

        # Aggregate results
        scores = [r['score'] for r in chunk_results]
        avg_score = np.mean(scores) if scores else 0.0

        # Determine overall sentiment
        if avg_score > 0.3:
            overall_sentiment = 'positive'
        elif avg_score < -0.3:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'

        return {
            'overall_sentiment': overall_sentiment,
            'overall_score': float(avg_score),
            'score_std': float(np.std(scores)) if scores else 0.0,
            'num_chunks': len(chunks),
            'chunk_results': chunk_results,
            'sentiment_trend': self._calculate_sentiment_trend(scores)
        }

    def _calculate_sentiment_trend(self, scores: List[float]) -> str:
        """
        Calculate sentiment trend across chunks.

        Args:
            scores: List of sentiment scores in order

        Returns:
            Trend description ('improving', 'declining', 'stable')
        """
        if len(scores) < 2:
            return 'stable'

        # Compare first half to second half
        mid = len(scores) // 2
        first_half_avg = np.mean(scores[:mid])
        second_half_avg = np.mean(scores[mid:])

        diff = second_half_avg - first_half_avg

        if diff > 0.2:
            return 'improving'
        elif diff < -0.2:
            return 'declining'
        else:
            return 'stable'


class FinancialNewsClassifier:
    """
    Classifies financial news into categories (e.g., earnings, mergers, product releases)
    """
    
    def __init__(
        self, 
        model_name: str = 'distilbert-base-uncased',
        max_length: int = 128,
        batch_size: int = 16,
        num_classes: int = 5
    ):
        """
        Initialize the financial news classifier
        
        Args:
            model_name: Name of the pre-trained model to fine-tune
            max_length: Maximum sequence length
            batch_size: Batch size for training and inference
            num_classes: Number of news categories
        """
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.num_classes = num_classes
        
        self.tokenizer = None
        self.model = None
        self.class_names = [
            'earnings', 
            'merger_acquisition', 
            'product_release', 
            'executive_change', 
            'regulatory'
        ][:num_classes]
        
        # Text preprocessor
        self.preprocessor = TextPreprocessor(
            lowercase=True,
            remove_urls=True,
            remove_stopwords=False,
            remove_punctuation=False
        )
    
    def load_tokenizer(self) -> 'FinancialNewsClassifier':
        """
        Load the tokenizer
        
        Returns:
            Self
        """
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except Exception as e:
            logger.error(f"Error loading tokenizer: {str(e)}")
            raise
        
        return self
    
    def build_model(self) -> tf.keras.Model:
        """
        Build the model for financial news classification
        
        Returns:
            Keras model
        """
        # Input layers
        input_ids = layers.Input(shape=(self.max_length,), dtype=tf.int32, name='input_ids')
        attention_mask = layers.Input(shape=(self.max_length,), dtype=tf.int32, name='attention_mask')
        
        # Load pre-trained model
        config = AutoConfig.from_pretrained(
            self.model_name,
            num_labels=self.num_classes
        )
        transformer = TFAutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            config=config
        )
        
        # Get transformer outputs
        transformer_outputs = transformer([input_ids, attention_mask], training=True).logits
        
        # Add a softmax layer
        outputs = layers.Activation('softmax')(transformer_outputs)
        
        # Create model
        model = tf.keras.Model(
            inputs=[input_ids, attention_mask],
            outputs=outputs
        )
        
        # Compile model
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=2e-5),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def prepare_data(
        self, 
        texts: List[str], 
        labels: List[int]
    ) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """
        Prepare data for training or inference
        
        Args:
            texts: List of texts
            labels: List of labels (class indices)
            
        Returns:
            Tuple of (tokenized_inputs, one_hot_labels)
        """
        if self.tokenizer is None:
            self.load_tokenizer()
        
        # Preprocess texts
        preprocessed_texts = self.preprocessor.preprocess_batch(texts)
        
        # Tokenize texts
        tokenized = self.tokenizer(
            preprocessed_texts,
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors='tf'
        )
        
        # Convert labels to one-hot
        one_hot_labels = tf.keras.utils.to_categorical(labels, num_classes=self.num_classes)
        
        return tokenized, one_hot_labels
    
    def fit(
        self, 
        texts: List[str], 
        labels: List[int],
        validation_texts: List[str] = None,
        validation_labels: List[int] = None,
        epochs: int = 3,
        verbose: int = 1
    ) -> 'FinancialNewsClassifier':
        """
        Fine-tune the model
        
        Args:
            texts: Training texts
            labels: Training labels
            validation_texts: Validation texts
            validation_labels: Validation labels
            epochs: Number of epochs
            verbose: Verbosity level
            
        Returns:
            Self
        """
        # Prepare data
        train_inputs, train_labels = self.prepare_data(texts, labels)
        
        # Prepare validation data if provided
        validation_data = None
        if validation_texts is not None and validation_labels is not None:
            val_inputs, val_labels = self.prepare_data(validation_texts, validation_labels)
            validation_data = (val_inputs, val_labels)
        
        # Build model if not already built
        if self.model is None:
            self.model = self.build_model()
        
        # Train model
        self.model.fit(
            train_inputs,
            train_labels,
            batch_size=self.batch_size,
            epochs=epochs,
            validation_data=validation_data,
            verbose=verbose
        )
        
        return self
    
    def predict(self, texts: List[str]) -> List[Dict[str, Union[str, float]]]:
        """
        Predict news categories for texts
        
        Args:
            texts: List of texts
            
        Returns:
            List of dictionaries containing classification results
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")
        
        # Prepare data
        inputs, _ = self.prepare_data(texts, [0] * len(texts))
        
        # Make predictions
        predictions = self.model.predict(inputs)
        
        # Format results
        results = []
        for i, pred in enumerate(predictions):
            # Get the predicted class
            class_idx = np.argmax(pred)
            class_name = self.class_names[class_idx]
            confidence = float(pred[class_idx])
            
            results.append({
                'text': texts[i],
                'category': class_name,
                'confidence': confidence,
                'probabilities': {self.class_names[j]: float(p) for j, p in enumerate(pred)}
            })
        
        return results


def sentiment_analysis_batch(
    texts: List[str],
    model_name: str = 'distilbert-base-uncased-finetuned-sst-2-english'
) -> pd.DataFrame:
    """
    Perform sentiment analysis on a batch of texts and return results as a DataFrame
    
    Args:
        texts: List of texts
        model_name: Name of the pre-trained model
        
    Returns:
        DataFrame with sentiment analysis results
    """
    # Create analyzer
    analyzer = TransformerSentimentAnalyzer(model_name=model_name)
    
    # Analyze texts
    results = analyzer.predict(texts)
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    return df


def find_market_moving_news(
    news_df: pd.DataFrame,
    sentiment_threshold: float = 0.8,
    min_confidence: float = 0.9,
    text_column: str = 'title',
    return_top_n: int = 10
) -> pd.DataFrame:
    """
    Find potentially market-moving news based on sentiment and other factors
    
    Args:
        news_df: DataFrame with news articles
        sentiment_threshold: Threshold for sentiment score magnitude
        min_confidence: Minimum confidence for sentiment prediction
        text_column: Column containing the news text
        return_top_n: Number of top news to return
        
    Returns:
        DataFrame with top market-moving news
    """
    # Ensure we have the required columns
    if text_column not in news_df.columns:
        raise ValueError(f"DataFrame must contain column: {text_column}")
    
    # Analyze sentiment if not already present
    if 'sentiment' not in news_df.columns or 'score' not in news_df.columns:
        # Extract text
        texts = news_df[text_column].tolist()
        
        # Analyze sentiment
        sentiment_df = sentiment_analysis_batch(texts)
        
        # Combine with original DataFrame
        for col in sentiment_df.columns:
            if col != 'text':
                news_df[col] = sentiment_df[col].values
    
    # Filter high-impact news
    high_impact = news_df[
        (abs(news_df['score']) >= sentiment_threshold) & 
        (news_df['confidence'] >= min_confidence)
    ].copy()
    
    # Sort by absolute sentiment score
    high_impact['impact_score'] = abs(high_impact['score'])
    high_impact = high_impact.sort_values(by='impact_score', ascending=False)
    
    # Return top N
    return high_impact.head(return_top_n)


def fingpt_sentiment_analysis(
    texts: Union[str, List[str]],
    use_quantization: bool = True,
    detailed: bool = False
) -> pd.DataFrame:
    """
    Perform FinGPT-enhanced sentiment analysis on financial texts.

    FinGPT provides superior sentiment analysis for financial domain text
    compared to general-purpose models.

    Args:
        texts: Single text or list of texts to analyze
        use_quantization: Use 8-bit quantization to reduce memory
        detailed: Use 5-point sentiment scale instead of 3-point

    Returns:
        DataFrame with sentiment analysis results

    Example:
        >>> results = fingpt_sentiment_analysis([
        ...     "Apple reports record Q4 revenue beating expectations",
        ...     "Tesla faces regulatory scrutiny over autopilot claims"
        ... ])
        >>> print(results[['text', 'sentiment', 'score']])
    """
    # Create FinGPT analyzer
    analyzer = FinGPTSentimentAnalyzer(
        load_in_8bit=use_quantization,
        load_in_4bit=not use_quantization
    )

    # Analyze texts
    results = analyzer.analyze_financial_text(texts, detailed=detailed)

    # Convert to DataFrame
    df = pd.DataFrame(results)

    return df


def analyze_market_sentiment(
    news_items: List[Dict[str, str]],
    use_fingpt: bool = True
) -> Dict[str, Any]:
    """
    Analyze overall market sentiment from a collection of news items.

    Args:
        news_items: List of dicts with 'title' and optionally 'description' keys
        use_fingpt: Use FinGPT for analysis (falls back to transformer if unavailable)

    Returns:
        Dictionary with aggregated sentiment metrics:
        - overall_sentiment: 'bullish', 'bearish', or 'neutral'
        - sentiment_score: -1.0 to 1.0
        - positive_ratio: Percentage of positive news
        - negative_ratio: Percentage of negative news
        - top_bullish: Most positive news items
        - top_bearish: Most negative news items
    """
    # Extract texts
    texts = []
    for item in news_items:
        text = item.get('title', '')
        if 'description' in item and item['description']:
            text += ' ' + item['description']
        texts.append(text)

    # Analyze sentiment
    if use_fingpt and PEFT_AVAILABLE:
        analyzer = FinGPTSentimentAnalyzer()
        results = analyzer.analyze_financial_text(texts)
    else:
        analyzer = TransformerSentimentAnalyzer()
        results = analyzer.predict(texts)

    # Calculate metrics
    scores = [r['score'] for r in results]
    avg_score = np.mean(scores) if scores else 0.0

    positive_count = sum(1 for s in scores if s > 0.2)
    negative_count = sum(1 for s in scores if s < -0.2)
    total = len(scores)

    # Determine overall sentiment
    if avg_score > 0.2:
        overall = 'bullish'
    elif avg_score < -0.2:
        overall = 'bearish'
    else:
        overall = 'neutral'

    # Sort results by score
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)

    return {
        'overall_sentiment': overall,
        'sentiment_score': float(avg_score),
        'sentiment_std': float(np.std(scores)) if scores else 0.0,
        'positive_ratio': positive_count / total if total > 0 else 0.0,
        'negative_ratio': negative_count / total if total > 0 else 0.0,
        'neutral_ratio': (total - positive_count - negative_count) / total if total > 0 else 0.0,
        'total_analyzed': total,
        'top_bullish': sorted_results[:3],
        'top_bearish': sorted_results[-3:] if len(sorted_results) >= 3 else sorted_results,
        'model_used': 'fingpt' if (use_fingpt and PEFT_AVAILABLE) else 'transformer'
    }