"""
NLP models for sentiment analysis of financial news and social media data.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification, AutoConfig
from transformers import pipeline
import torch
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