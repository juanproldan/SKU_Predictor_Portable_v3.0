#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart Text Processing Module
Enhanced text preprocessing with context-aware abbreviation expansion and automotive spell correction

Author: Augment Agent
Date: 2025-07-25
"""

import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class SmartTextProcessor:
    """
    Enhanced text processor with automotive domain knowledge
    """
    
    def __init__(self):
        # Automotive context patterns for smart abbreviation expansion
        self.automotive_contexts = {
            'parts': ['parachoques', 'paragolpes', 'puerta', 'faro', 'farola', 'espejo', 'capo', 
                     'guardafango', 'vidrio', 'parabrisas', 'motor', 'tapa', 'carcasa'],
            'positions': ['delantero', 'trasero', 'izquierdo', 'derecho', 'superior', 'inferior'],
            'materials': ['plastico', 'metal', 'vidrio', 'goma', 'caucho'],
            'colors': ['negro', 'blanco', 'gris', 'azul', 'rojo', 'verde']
        }
        
        # Context-aware abbreviation mappings
        self.context_abbreviations = {
            'del': {
                'automotive_context': 'delantero',
                'preposition_context': 'del',  # Keep as preposition
                'automotive_indicators': ['parachoques', 'faro', 'puerta', 'vidrio', 'guardafango']
            },
            'tras': {
                'automotive_context': 'trasero',
                'default': 'trasero'
            },
            'der': {
                'automotive_context': 'derecho',
                'default': 'derecho'
            },
            'izq': {
                'automotive_context': 'izquierdo',
                'default': 'izquierdo'
            },
            'sup': {
                'automotive_context': 'superior',
                'default': 'superior'
            },
            'inf': {
                'automotive_context': 'inferior',
                'default': 'inferior'
            }
        }
        
        # Automotive spell corrections
        self.automotive_corrections = {
            # Common misspellings
            'paracoque': 'parachoques',
            'parachoque': 'parachoques',
            'paragolpe': 'paragolpes',
            'parabrisa': 'parabrisas',
            'retrobisores': 'retrovisores',
            'retrobisors': 'retrovisores',
            'guardafangos': 'guardafango',
            'guardafangues': 'guardafango',
            
            # Alternative spellings
            'bomper': 'paragolpes',
            'bumper': 'paragolpes',
            'defensa': 'paragolpes',
            'capot': 'capo',
            'cofre': 'capo',
            
            # Light variations
            'foco': 'faro',
            'luz': 'faro',
            'optica': 'faro',
            'lampara': 'faro',
            
            # Position variations
            'frontal': 'delantero',
            'anterior': 'delantero',
            'posterior': 'trasero',
            'lateral': 'lateral'
        }
        
        # Gender agreement exceptions (building on existing system)
        self.gender_exceptions = {
            'emblema': 'masculine',  # emblema trasero (not trasera)
            'portaplaca': 'masculine',  # portaplaca trasero (not trasera)
            'stop': 'masculine',  # stop derecho (not derecha)
            'bocel': 'masculine',  # bocel derecho
            'guardapolvo': 'masculine',  # guardapolvo delantero
            'remache': 'masculine',  # remache plastico
            'broches': 'masculine',  # broches delantero
        }
    
    def process_text_enhanced(self, text: str, existing_processor=None) -> str:
        """
        Enhanced text processing pipeline
        
        Args:
            text: Input text to process
            existing_processor: Existing text processor instance (if available)
            
        Returns:
            Processed text with enhanced corrections
        """
        if not text:
            return text
        
        # Step 1: Apply existing processing pipeline if available
        if existing_processor and hasattr(existing_processor, 'process_text'):
            processed_text = existing_processor.process_text(text)
        else:
            processed_text = text.lower().strip()
        
        # Step 2: Apply automotive spell corrections
        processed_text = self.apply_automotive_spell_correction(processed_text)
        
        # Step 3: Context-aware abbreviation expansion
        processed_text = self.expand_abbreviations_with_context(processed_text)
        
        # Step 4: Enhanced gender agreement (building on existing)
        processed_text = self.apply_enhanced_gender_agreement(processed_text)
        
        # Step 5: Smart dot handling
        processed_text = self.apply_smart_dot_handling(processed_text)
        
        return processed_text
    
    def apply_automotive_spell_correction(self, text: str) -> str:
        """Apply automotive-specific spell corrections"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if clean_word in self.automotive_corrections:
                # Preserve original punctuation
                corrected = self.automotive_corrections[clean_word]
                if word != clean_word:  # Had punctuation
                    # Try to preserve punctuation pattern
                    corrected = self._preserve_punctuation(word, corrected)
                corrected_words.append(corrected)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def expand_abbreviations_with_context(self, text: str) -> str:
        """
        Expand abbreviations considering automotive context
        
        Example: "parachoques del" → "parachoques delantero"
                 "parte del motor" → "parte del motor" (no change)
        """
        words = text.split()
        expanded_words = []
        
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if clean_word in self.context_abbreviations:
                abbrev_data = self.context_abbreviations[clean_word]
                
                # Check for automotive context
                has_automotive_context = False
                
                # Look at previous words for automotive indicators
                if 'automotive_indicators' in abbrev_data:
                    for j in range(max(0, i-3), i):  # Check 3 words back
                        prev_word = re.sub(r'[^\w]', '', words[j].lower())
                        if prev_word in abbrev_data['automotive_indicators']:
                            has_automotive_context = True
                            break
                
                # Look at next words for automotive indicators
                if not has_automotive_context and 'automotive_indicators' in abbrev_data:
                    for j in range(i+1, min(len(words), i+3)):  # Check 2 words forward
                        next_word = re.sub(r'[^\w]', '', words[j].lower())
                        if next_word in abbrev_data['automotive_indicators']:
                            has_automotive_context = True
                            break
                
                # Choose expansion based on context
                if has_automotive_context and 'automotive_context' in abbrev_data:
                    expansion = abbrev_data['automotive_context']
                elif 'preposition_context' in abbrev_data and not has_automotive_context:
                    expansion = abbrev_data['preposition_context']
                else:
                    expansion = abbrev_data.get('default', word)
                
                # Preserve original punctuation
                if word != clean_word:
                    expansion = self._preserve_punctuation(word, expansion)
                
                expanded_words.append(expansion)
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def apply_enhanced_gender_agreement(self, text: str) -> str:
        """
        Apply enhanced gender agreement rules
        Building on existing gender agreement system
        """
        words = text.split()
        corrected_words = []
        
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Check for position adjectives that need gender agreement
            if clean_word in ['delantero', 'delantera', 'trasero', 'trasera', 'izquierdo', 'izquierda', 'derecho', 'derecha']:
                # Look for nearby nouns to determine gender
                corrected_word = self._apply_gender_agreement_to_word(word, words, i)
                corrected_words.append(corrected_word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _apply_gender_agreement_to_word(self, word: str, words: List[str], position: int) -> str:
        """Apply gender agreement to a specific word based on context"""
        clean_word = re.sub(r'[^\w]', '', word.lower())
        
        # Look for nouns in nearby positions
        for offset in [1, 2, -1, -2]:  # Check adjacent words
            noun_pos = position + offset
            if 0 <= noun_pos < len(words):
                noun = re.sub(r'[^\w]', '', words[noun_pos].lower())
                
                # Check gender exceptions first
                if noun in self.gender_exceptions:
                    gender = self.gender_exceptions[noun]
                    return self._convert_to_gender(word, clean_word, gender)
                
                # Apply existing gender rules (feminine endings)
                if noun.endswith(('a', 'cion', 'sion', 'dad', 'tad')):
                    return self._convert_to_gender(word, clean_word, 'feminine')
                elif noun.endswith(('o', 'or', 'on')):
                    return self._convert_to_gender(word, clean_word, 'masculine')
        
        return word
    
    def _convert_to_gender(self, original_word: str, clean_word: str, gender: str) -> str:
        """Convert adjective to specified gender"""
        if gender == 'feminine':
            if clean_word.endswith('o'):
                new_word = clean_word[:-1] + 'a'
            else:
                new_word = clean_word
        else:  # masculine
            if clean_word.endswith('a'):
                new_word = clean_word[:-1] + 'o'
            else:
                new_word = clean_word
        
        # Preserve original punctuation
        return self._preserve_punctuation(original_word, new_word)
    
    def apply_smart_dot_handling(self, text: str) -> str:
        """
        Apply smart dot handling for automotive part descriptions
        
        Examples:
        - "VIDRIO PUER.DL.D." → "VIDRIO PUERTA DELANTERA DERECHA"
        - "FARO DEL.IZQ." → "FARO DELANTERO IZQUIERDO"
        """
        # Common dot abbreviation patterns in automotive context
        dot_patterns = {
            r'\bPUER\.DL\.D\.': 'PUERTA DELANTERA DERECHA',
            r'\bPUER\.DL\.I\.': 'PUERTA DELANTERA IZQUIERDA',
            r'\bPUER\.TR\.D\.': 'PUERTA TRASERA DERECHA',
            r'\bPUER\.TR\.I\.': 'PUERTA TRASERA IZQUIERDA',
            r'\bDEL\.IZQ\.': 'DELANTERO IZQUIERDO',
            r'\bDEL\.DER\.': 'DELANTERO DERECHO',
            r'\bTR\.IZQ\.': 'TRASERO IZQUIERDO',
            r'\bTR\.DER\.': 'TRASERO DERECHO',
            r'\bIZQ\.': 'IZQUIERDO',
            r'\bDER\.': 'DERECHO',
            r'\bDEL\.': 'DELANTERO',
            r'\bTR\.': 'TRASERO',
            r'\bSUP\.': 'SUPERIOR',
            r'\bINF\.': 'INFERIOR'
        }
        
        processed_text = text.upper()  # Work with uppercase for pattern matching
        
        for pattern, replacement in dot_patterns.items():
            processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
        
        return processed_text.lower()
    
    def _preserve_punctuation(self, original: str, new_word: str) -> str:
        """Preserve punctuation from original word in new word"""
        if original == new_word.lower():
            return original
        
        # Simple punctuation preservation
        if original.endswith('.'):
            return new_word + '.'
        elif original.endswith(','):
            return new_word + ','
        elif original.endswith(';'):
            return new_word + ';'
        else:
            return new_word
    
    def get_processing_stats(self, original_text: str, processed_text: str) -> Dict:
        """Get statistics about text processing changes"""
        original_words = original_text.lower().split()
        processed_words = processed_text.lower().split()
        
        changes = []
        for i, (orig, proc) in enumerate(zip(original_words, processed_words)):
            if orig != proc:
                changes.append({
                    'position': i,
                    'original': orig,
                    'processed': proc,
                    'change_type': self._classify_change(orig, proc)
                })
        
        return {
            'total_words': len(original_words),
            'words_changed': len(changes),
            'change_percentage': len(changes) / len(original_words) * 100 if original_words else 0,
            'changes': changes
        }
    
    def _classify_change(self, original: str, processed: str) -> str:
        """Classify the type of change made"""
        if original in self.automotive_corrections:
            return 'spell_correction'
        elif any(abbrev in original for abbrev in self.context_abbreviations):
            return 'abbreviation_expansion'
        elif original.endswith(('o', 'a')) and processed.endswith(('a', 'o')):
            return 'gender_agreement'
        elif '.' in original:
            return 'dot_handling'
        else:
            return 'other'


# Global instance for the application
smart_processor = None

def initialize_smart_text_processor():
    """Initialize the global smart text processor"""
    global smart_processor
    smart_processor = SmartTextProcessor()
    print("🧠 Smart Text Processor initialized")
    return smart_processor

def get_smart_processor():
    """Get the global smart text processor instance"""
    global smart_processor
    if smart_processor is None:
        smart_processor = initialize_smart_text_processor()
    return smart_processor

def process_text_with_enhancements(text: str, existing_processor=None) -> str:
    """
    Process text with enhanced automotive-specific improvements
    
    Args:
        text: Input text to process
        existing_processor: Existing text processor instance
        
    Returns:
        Enhanced processed text
    """
    processor = get_smart_processor()
    return processor.process_text_enhanced(text, existing_processor)
