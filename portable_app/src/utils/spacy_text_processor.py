#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
spaCy-based Spanish Text Processor

This module replaces the manual gender agreement and linguistic processing
with spaCy's advanced Spanish NLP capabilities for better accuracy and performance.

Key Features:
- Automatic gender agreement using spaCy's morphological analysis
- POS tagging for proper noun-adjective relationships
- Lemmatization for plural/singular normalization
- Dependency parsing for context-aware processing
- Automotive-specific term handling
- Integration with existing equivalencias system

Author: Augment Agent
Date: 2025-07-29
"""

import spacy
import re
import logging
from typing import Dict, List, Tuple, Optional
import unicodedata

# Configure logging
logger = logging.getLogger(__name__)

class SpacyTextProcessor:
    """
    Advanced Spanish text processor using spaCy for automotive part descriptions.
    
    Replaces manual gender agreement rules with spaCy's linguistic intelligence
    while preserving automotive-specific processing.
    """
    
    def __init__(self):
        """Initialize the spaCy processor with Spanish model."""
        self.nlp = None
        self.automotive_exceptions = {}
        self.automotive_abbreviations = {}
        self._load_spacy_model()
        self._setup_automotive_rules()
    
    def _load_spacy_model(self):
        """Load the Spanish spaCy model with error handling."""
        try:
            self.nlp = spacy.load("es_core_news_sm")
            logger.info("✅ spaCy Spanish model loaded successfully")
        except OSError as e:
            logger.error(f"❌ Failed to load spaCy Spanish model: {e}")
            logger.error("Please install with: python -m spacy download es_core_news_sm")
            raise
    
    def _setup_automotive_rules(self):
        """Setup automotive-specific rules and exceptions."""
        
        # Gender exceptions for automotive parts (overrides spaCy's default gender detection)
        self.automotive_exceptions = {
            # Masculine exceptions
            'emblema': 'MASC',      # el emblema (not la emblema)
            'portaplaca': 'MASC',   # el portaplaca (not la portaplaca)
            'stop': 'MASC',         # el stop (not la stop)
            'bocel': 'MASC',        # el bocel
            'guardapolvo': 'MASC',  # el guardapolvo
            'remache': 'MASC',      # el remache
            'broches': 'MASC',      # los broches
            'vidrio': 'MASC',       # el vidrio
            'cristal': 'MASC',      # el cristal
            'parabrisas': 'MASC',   # el parabrisas
            'espejo': 'MASC',       # el espejo
            'retrovisor': 'MASC',   # el retrovisor
            'paragolpes': 'MASC',   # el paragolpes
            'absorbedor': 'MASC',   # el absorbedor
            'electroventilador': 'MASC',  # el electroventilador
            'radiador': 'MASC',     # el radiador

            # Feminine exceptions
            'puerta': 'FEM',        # la puerta
            'luz': 'FEM',           # la luz
            'antiniebla': 'FEM',    # la antiniebla
        }
        
        # Automotive abbreviations with context
        self.automotive_abbreviations = {
            'del': 'delantero',
            'tras': 'trasero',
            'der': 'derecho',
            'izq': 'izquierdo',
            'i': 'izquierda',  # Single letter abbreviation for izquierda
            'sup': 'superior',
            'inf': 'inferior',
            'ant': 'anterior',
            'post': 'posterior',
            'ext': 'exterior',
            'int': 'interior',
            'plast': 'plastico',
            'met': 'metalico',
            'tra': 'trasero',
        }
    
    def process_text(self, text: str, preserve_automotive_terms: bool = True) -> str:
        """
        Main text processing function using spaCy.
        
        Args:
            text: Input text to process
            preserve_automotive_terms: Whether to preserve automotive-specific terms
            
        Returns:
            Processed text with correct gender agreement and normalization
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Basic normalization (preserve dots for smart handling)
        normalized_text = self._basic_normalization(text)
        
        # Step 2: Smart dot handling (before spaCy processing)
        dot_processed = self._smart_dot_handling(normalized_text)
        
        # Step 3: Expand automotive abbreviations
        abbrev_expanded = self._expand_automotive_abbreviations(dot_processed)
        
        # Step 4: spaCy linguistic processing
        spacy_processed = self._spacy_linguistic_processing(abbrev_expanded)
        
        # Step 5: Final cleanup
        final_text = self._final_cleanup(spacy_processed)
        
        return final_text
    
    def _basic_normalization(self, text: str) -> str:
        """Basic text normalization (case, accents, whitespace)."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents/diacritics
        nfkd_form = unicodedata.normalize('NFKD', text)
        text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _smart_dot_handling(self, text: str) -> str:
        """
        Smart dot handling for automotive descriptions.
        Converts dots between letters to spaces (e.g., 'FARO.DELANTERO' -> 'FARO DELANTERO')
        """
        # Replace dots between letters with spaces
        text = re.sub(r'([a-zA-Z])\.([a-zA-Z])', r'\1 \2', text)
        
        # Remove remaining dots at word boundaries
        text = re.sub(r'\b\.\b', ' ', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _expand_automotive_abbreviations(self, text: str) -> str:
        """Expand automotive abbreviations before spaCy processing."""
        words = text.split()
        expanded_words = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word)
            
            if clean_word in self.automotive_abbreviations:
                expanded_words.append(self.automotive_abbreviations[clean_word])
                logger.debug(f"Expanded abbreviation: '{clean_word}' -> '{self.automotive_abbreviations[clean_word]}'")
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def _spacy_linguistic_processing(self, text: str) -> str:
        """
        Main spaCy processing for gender agreement and linguistic corrections.
        Optimized for performance.
        """
        if not self.nlp:
            logger.warning("spaCy model not loaded, skipping linguistic processing")
            return text

        # Process with spaCy (disable unnecessary components for speed)
        doc = self.nlp(text, disable=['ner', 'parser'])  # Keep only POS and morphology

        # Apply gender agreement corrections
        corrected_tokens = []

        for token in doc:
            corrected_token = self._apply_gender_agreement(token, doc)
            corrected_tokens.append(corrected_token)

        return ' '.join(corrected_tokens)
    
    def _apply_gender_agreement(self, token, doc) -> str:
        """
        Apply gender agreement using spaCy's linguistic analysis.
        """
        # If it's not an adjective, return as-is
        if token.pos_ != "ADJ":
            return token.text
        
        # Find the noun this adjective modifies
        head_noun = self._find_governing_noun(token, doc)
        
        if not head_noun:
            return token.text
        
        # Determine the correct gender
        target_gender = self._get_noun_gender(head_noun)
        
        # Apply gender agreement
        corrected_form = self._convert_adjective_gender(token.text, target_gender)
        
        if corrected_form != token.text:
            logger.debug(f"Gender correction: '{token.text}' -> '{corrected_form}' (noun: '{head_noun.text}', gender: {target_gender})")
        
        return corrected_form
    
    def _find_governing_noun(self, adjective_token, doc):
        """
        Find the noun that this adjective modifies using automotive-specific logic.

        For automotive parts, the main part (usually the second noun) determines gender:
        - "VIDRIO PUERTA" → "puerta" determines gender (feminine)
        - "FARO DELANTERO" → "faro" determines gender (masculine)
        """
        # Check if the adjective directly modifies a noun or proper noun
        if adjective_token.head.pos_ in ["NOUN", "PROPN"]:
            return adjective_token.head

        # Look for nearby nouns (within 3 positions)
        adj_index = adjective_token.i

        # Collect all nearby nouns
        nearby_nouns = []

        # Check preceding nouns (Spanish: noun + adjective)
        for i in range(max(0, adj_index - 3), adj_index):
            if doc[i].pos_ in ["NOUN", "PROPN"]:
                nearby_nouns.append(doc[i])

        # Check following nouns (less common but possible)
        for i in range(adj_index + 1, min(len(doc), adj_index + 4)):
            if doc[i].pos_ in ["NOUN", "PROPN"]:
                nearby_nouns.append(doc[i])

        if not nearby_nouns:
            return None

        # Automotive-specific logic: prefer the main part noun
        # For compound parts like "VIDRIO PUERTA", "PUERTA" is the main part
        main_part_nouns = []
        material_nouns = []

        for noun in nearby_nouns:
            noun_text = noun.text.lower()
            # Material/component nouns (usually modifiers)
            if noun_text in ['vidrio', 'cristal', 'plastico', 'metal', 'goma', 'caucho']:
                material_nouns.append(noun)
            else:
                # Main part nouns (determine gender)
                main_part_nouns.append(noun)

        # Prefer main part nouns over material nouns
        if main_part_nouns:
            # Return the closest main part noun
            return min(main_part_nouns, key=lambda n: abs(n.i - adj_index))
        elif material_nouns:
            # Fallback to material nouns if no main part found
            return min(material_nouns, key=lambda n: abs(n.i - adj_index))
        else:
            # Fallback to closest noun
            return min(nearby_nouns, key=lambda n: abs(n.i - adj_index))
    
    def _get_noun_gender(self, noun_token) -> str:
        """
        Determine noun gender using automotive exceptions and spaCy morphology.
        """
        noun_text = noun_token.text.lower()

        # Check automotive exceptions first (highest priority)
        if noun_text in self.automotive_exceptions:
            gender = self.automotive_exceptions[noun_text]
            logger.debug(f"Automotive exception: '{noun_text}' → {gender}")
            return gender

        # Use spaCy's morphological analysis
        if noun_token.morph.get("Gender"):
            spacy_gender = noun_token.morph.get("Gender")[0]  # Get first gender value
            gender = spacy_gender.upper()  # Convert to MASC/FEM format
            logger.debug(f"spaCy morphology: '{noun_text}' → {gender}")
            return gender

        # Fallback to Spanish grammar rules
        if noun_text.endswith(('a', 'cion', 'sion', 'dad', 'tad', 'tud')):
            logger.debug(f"Grammar rule (feminine): '{noun_text}' → FEM")
            return 'FEM'
        elif noun_text.endswith(('o', 'or', 'on', 'an', 'en')):
            logger.debug(f"Grammar rule (masculine): '{noun_text}' → MASC")
            return 'MASC'

        # Default to masculine for unknown cases
        logger.debug(f"Default rule: '{noun_text}' → MASC")
        return 'MASC'
    
    def _convert_adjective_gender(self, adjective: str, target_gender: str) -> str:
        """
        Convert adjective to the target gender.
        """
        adj_lower = adjective.lower()

        # Common Spanish adjective gender patterns
        if target_gender == 'MASC':
            # Convert to masculine
            if adj_lower in ['derecha', 'izquierda', 'delantera', 'trasera']:
                return adjective[:-1] + 'o'  # Remove 'a' and add 'o'
            elif adj_lower.endswith('a') and adj_lower in ['derecha', 'izquierda', 'delantera', 'trasera']:
                return adjective[:-1] + 'o'
        elif target_gender == 'FEM':
            # Convert to feminine
            if adj_lower in ['derecho', 'izquierdo', 'delantero', 'trasero']:
                return adjective[:-1] + 'a'  # Remove 'o' and add 'a'
            elif adj_lower.endswith('o'):
                return adjective[:-1] + 'a'

        # Return unchanged if no conversion needed
        return adjective
    
    def _final_cleanup(self, text: str) -> str:
        """Final text cleanup and normalization."""
        # Remove extra punctuation
        text = re.sub(r'[^\w\s]', '', text)

        # Remove common Spanish prepositions that don't add meaning in automotive contexts
        # Split into words, filter out prepositions, rejoin
        words = text.split()
        filtered_words = []

        spanish_prepositions = {'de', 'del', 'la', 'el', 'los', 'las', 'y', 'con', 'sin', 'para', 'por'}

        for word in words:
            word_lower = word.lower()
            # Keep the word if it's not a preposition or if it's the only word
            if word_lower not in spanish_prepositions or len(words) == 1:
                filtered_words.append(word)

        text = ' '.join(filtered_words)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get statistics about the processing."""
        return {
            'model_loaded': 1 if self.nlp else 0,
            'automotive_exceptions': len(self.automotive_exceptions),
            'automotive_abbreviations': len(self.automotive_abbreviations)
        }


# Global instance for the application
spacy_processor = None

def initialize_spacy_processor():
    """Initialize the global spaCy text processor."""
    global spacy_processor
    try:
        spacy_processor = SpacyTextProcessor()
        logger.info("🧠 spaCy Text Processor initialized successfully")
        return spacy_processor
    except Exception as e:
        logger.error(f"❌ Failed to initialize spaCy processor: {e}")
        return None

def process_text_with_spacy(text: str) -> str:
    """
    Convenience function to process text with the global spaCy processor.
    
    Args:
        text: Input text to process
        
    Returns:
        Processed text with spaCy-based corrections
    """
    global spacy_processor
    
    if not spacy_processor:
        spacy_processor = initialize_spacy_processor()
    
    if spacy_processor:
        return spacy_processor.process_text(text)
    else:
        # Fallback to basic normalization if spaCy fails
        logger.warning("spaCy processor not available, using basic normalization")
        return text.lower().strip()
