import unicodedata
import re
from typing import Optional, List, Tuple

# Import our fuzzy matching utilities
try:
    from utils.fuzzy_matcher import fuzzy_normalize_text, get_fuzzy_matches, find_best_match, AUTOMOTIVE_ABBR
except ImportError:
    # Fallback for direct execution if src is not in path
    try:
        from .fuzzy_matcher import fuzzy_normalize_text, get_fuzzy_matches, find_best_match, AUTOMOTIVE_ABBR
    except ImportError:
        # If fuzzy_matcher is not available, define placeholder functions
        def fuzzy_normalize_text(text: str) -> str:
            """Placeholder for fuzzy_normalize_text if module not available"""
            return normalize_text(text)

        def get_fuzzy_matches(query: str, candidates: List[str], threshold: float = 0.7) -> List[Tuple[str, float]]:
            """Placeholder for get_fuzzy_matches if module not available"""
            return [(c, 1.0) for c in candidates if c == query]

        def find_best_match(query: str, candidates: List[str], threshold: float = 0.7) -> Optional[Tuple[str, float]]:
            """Placeholder for find_best_match if module not available"""
            if query in candidates:
                return (query, 1.0)
            return None

        # Placeholder for AUTOMOTIVE_ABBR if module not available
        AUTOMOTIVE_ABBR = {}


# Gender dictionary for Spanish automotive parts nouns
# Used for context-aware word corrections (gender agreement)
NOUN_GENDERS = {
    # Feminine nouns
    'puerta': 'feminine',
    'farola': 'feminine',
    'luz': 'feminine',
    'llanta': 'feminine',
    'rueda': 'feminine',
    'ventana': 'feminine',
    'ventanilla': 'feminine',
    'guia': 'feminine',
    'correa': 'feminine',
    'bomba': 'feminine',
    'bateria': 'feminine',
    'antena': 'feminine',
    'manija': 'feminine',
    'cerradura': 'feminine',
    'chapa': 'feminine',
    'tapa': 'feminine',
    'cubierta': 'feminine',
    'manguera': 'feminine',
    'bujia': 'feminine',
    'valvula': 'feminine',
    'palanca': 'feminine',
    'bisagra': 'feminine',
    'junta': 'feminine',
    'goma': 'feminine',
    'banda': 'feminine',
    'cadena': 'feminine',
    'placa': 'feminine',
    'rejilla': 'feminine',
    'parrilla': 'feminine',
    'moldura': 'feminine',
    'varilla': 'feminine',
    'barra': 'feminine',
    'tuerca': 'feminine',
    'arandela': 'feminine',
    'empaquetadura': 'feminine',
    'puntera': 'feminine',  # Bumper corner piece (la puntera)

    # Masculine nouns
    'faro': 'masculine',
    'espejo': 'masculine',
    'capo': 'masculine',
    'baul': 'masculine',
    'maletero': 'masculine',
    'parabrisas': 'masculine',
    'vidrio': 'masculine',
    'cristal': 'masculine',
    'motor': 'masculine',
    'filtro': 'masculine',
    'radiador': 'masculine',
    'alternador': 'masculine',
    'arranque': 'masculine',
    'compresor': 'masculine',
    'condensador': 'masculine',
    'evaporador': 'masculine',
    'termostato': 'masculine',
    'sensor': 'masculine',
    'interruptor': 'masculine',
    'rele': 'masculine',
    'fusible': 'masculine',
    'cable': 'masculine',
    'conector': 'masculine',
    'soporte': 'masculine',
    'bracket': 'masculine',
    'tornillo': 'masculine',
    'perno': 'masculine',
    'retenedor': 'masculine',
    'sello': 'masculine',
    'anillo': 'masculine',
    'rodamiento': 'masculine',
    'cojinete': 'masculine',
    'amortiguador': 'masculine',
    'resorte': 'masculine',
    'brazo': 'masculine',
    'eje': 'masculine',
    'disco': 'masculine',
    'tambor': 'masculine',
    'cilindro': 'masculine',
    'piston': 'masculine',
    'embolo': 'masculine',
    'vastago': 'masculine',
    'tubo': 'masculine',
    'ducto': 'masculine',
    'multiple': 'masculine',
    'colector': 'masculine',
    'escape': 'masculine',
    'silenciador': 'masculine',
    'catalizador': 'masculine',
    'tanque': 'masculine',
    'deposito': 'masculine',
    'reservorio': 'masculine',
    'carter': 'masculine',
    'diferencial': 'masculine',
    'embrague': 'masculine',
    'volante': 'masculine',
    'pedal': 'masculine',
    'freno': 'masculine',
    'acelerador': 'masculine',
    'clutch': 'masculine',
    'cambio': 'masculine',
    'engranaje': 'masculine',
    'pino': 'masculine',
    'bulon': 'masculine',
    'pasador': 'masculine',
    'retenedor': 'masculine',
    'guardapolvo': 'masculine',
    'fuelle': 'masculine',
    'tensor': 'masculine',
    'regulador': 'masculine',
    'limitador': 'masculine',
    'estabilizador': 'masculine',
    'compensador': 'masculine',
    'distribuidor': 'masculine',
    'carburador': 'masculine',
    'inyector': 'masculine',
    'medidor': 'masculine',
    'indicador': 'masculine',
    'tablero': 'masculine',
    'panel': 'masculine',
    'boton': 'masculine',
    'control': 'masculine',
    'mando': 'masculine',
    'volumen': 'masculine',
    'nivel': 'masculine',
    'aceite': 'masculine',
    'liquido': 'masculine',
    'refrigerante': 'masculine',
    'combustible': 'masculine',
    'gas': 'masculine',
    'aire': 'masculine',
    'viento': 'masculine',
    'humo': 'masculine',
    'vapor': 'masculine',
    'calor': 'masculine',
    'frio': 'masculine',
    'hielo': 'masculine',
    'agua': 'feminine',  # Exception: agua is feminine but uses masculine articles
    'asiento': 'masculine',
    'respaldo': 'masculine',
    'apoyacabeza': 'masculine',
    'cinturon': 'masculine',
    'arnes': 'masculine',
    'airbag': 'masculine',
    'volante': 'masculine',
    'timón': 'masculine',
    'manubrio': 'masculine',
    'neumatico': 'masculine',
    'caucho': 'masculine',
    'rin': 'masculine',
    'aro': 'masculine',
    'tapacubo': 'masculine',
    'centro': 'masculine',
    'nucleo': 'masculine',
    'corazon': 'masculine',
    'alma': 'feminine',
    'cuerpo': 'masculine',
    'chasis': 'masculine',
    'bastidor': 'masculine',
    'marco': 'masculine',
    'estructura': 'feminine',
    'carroceria': 'feminine',
    # Gender exceptions (words ending in 'a' but masculine)
    'emblema': 'masculine',  # Exception: el emblema (not la emblema)
    'portaplaca': 'masculine',  # Exception: el portaplaca (not la portaplaca)
    'pintura': 'feminine',
    'barniz': 'masculine',
    'esmalte': 'masculine',
    'primer': 'masculine',
    'masilla': 'feminine',
    'soldadura': 'feminine',
    'remache': 'masculine',
    'pegamento': 'masculine',
    'adhesivo': 'masculine',
    'sellador': 'masculine',
    'limpiador': 'masculine',
    'desengrasante': 'masculine',
    'lubricante': 'masculine',
    'grasa': 'feminine',
    'aceite': 'masculine',
    'fluido': 'masculine'
}


def smart_dot_handling(text: str) -> str:
    """
    Smart dot handling for automotive part descriptions.

    Converts dots to spaces ONLY when they're between letters/numbers,
    making abbreviated descriptions more readable.

    Examples:
    - "GUARDAP.PLAST.TRA.D." → "GUARDAP PLAST TRA D"
    - "PART.123.XYZ" → "PART 123 XYZ"
    - "A.B.C" → "A B C"
    - "SOP.I.PARAGOLPES DL." → "SOP I PARAGOLPES DL"

    Args:
        text: Input text with potential dot separators

    Returns:
        Text with dots converted to spaces where appropriate
    """
    if not isinstance(text, str):
        return ""

    # Replace dots between alphanumeric characters with spaces
    # Use a loop to handle multiple consecutive dots like A.B.C → A B C
    # The regex only replaces one at a time, so we need to repeat until no more matches
    while True:
        new_text = re.sub(r'([a-zA-Z0-9])\.([a-zA-Z0-9])', r'\1 \2', text)
        if new_text == text:  # No more replacements made
            break
        text = new_text

    # Remove trailing dots
    text = re.sub(r'\.+$', '', text)

    return text


def normalize_text(text: str, use_fuzzy: bool = False, expand_linguistic_variations: bool = True, use_spacy: bool = True) -> str:
    """
    Normalizes a text string according to the project's requirements:
    - NEW: Uses spaCy for advanced Spanish linguistic processing (gender agreement, POS tagging)
    - Smart dot handling (converts dots between letters to spaces)
    - Converts to lowercase.
    - Removes leading/trailing whitespace.
    - Standardizes internal whitespace (multiple spaces to one).
    - Removes common punctuation (keeps alphanumeric and spaces).
    - Handles accented characters/diacritics (e.g., converts 'á' to 'a').
    - Optionally expands abbreviations, gender, and plural variations.

    Args:
        text: The input text to normalize
        use_fuzzy: Whether to use enhanced fuzzy normalization (default: False)
        expand_linguistic_variations: Whether to expand abbreviations, gender, plurals (default: True)
        use_spacy: Whether to use spaCy for advanced linguistic processing (default: True)

    Returns:
        Normalized text string
    """
    if not isinstance(text, str):
        return ""  # Or raise an error, depending on desired handling for non-strings

    if use_fuzzy:
        # Use the enhanced fuzzy normalization
        return fuzzy_normalize_text(text)

    # NEW: Try spaCy processing first (if available and requested)
    if use_spacy and expand_linguistic_variations:
        try:
            from .spacy_text_processor import process_text_with_spacy
            return process_text_with_spacy(text)
        except ImportError:
            print("⚠️ spaCy processor not available, falling back to manual processing")
        except Exception as e:
            print(f"⚠️ spaCy processing failed: {e}, falling back to manual processing")

    # FALLBACK: Standard normalization (original implementation)
    # 1. Smart dot handling (BEFORE other processing)
    text = smart_dot_handling(text)

    # 2. Convert to lowercase
    text = text.lower()

    # 3. Remove leading/trailing whitespace
    text = text.strip()

    # 4. Normalize accented characters
    # Decompose into base character and combining diacritical marks, then remove marks
    nfkd_form = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    # 5. Remove common punctuation (keeps alphanumeric characters and spaces)
    # This regex will remove anything that's not a letter, number, or whitespace.
    # If specific punctuation needs to be kept or replaced differently, adjust the regex.
    text = re.sub(r'[^\w\s]', '', text)  # \w is alphanumeric + underscore

    # 6. Standardize internal whitespace (multiple spaces/tabs/newlines to a single space)
    # strip again in case regex leaves leading/trailing space
    text = re.sub(r'\s+', ' ', text).strip()

    # 7. Expand linguistic variations (abbreviations, gender, plurals) if requested
    if expand_linguistic_variations:
        text = expand_linguistic_variations_text(text)

    return text


def normalize_text_with_spacy(text: str) -> str:
    """
    Convenience function for spaCy-based text normalization.

    This function specifically uses spaCy for advanced Spanish linguistic processing
    and is the recommended approach for new implementations.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text using spaCy processing
    """
    return normalize_text(text, use_fuzzy=False, expand_linguistic_variations=True, use_spacy=True)


def normalize_text_legacy(text: str) -> str:
    """
    Legacy text normalization using manual rules (for comparison/fallback).

    Args:
        text: Input text to normalize

    Returns:
        Normalized text using legacy manual processing
    """
    return normalize_text(text, use_fuzzy=False, expand_linguistic_variations=True, use_spacy=False)


def expand_comprehensive_abbreviations(text: str) -> str:
    """
    Expands automotive abbreviations using the comprehensive AUTOMOTIVE_ABBR dictionary.
    This integrates the full abbreviation dictionary into the main text processing pipeline.

    Args:
        text: Input text with potential abbreviations

    Returns:
        Text with abbreviations expanded to their full forms
    """
    if not isinstance(text, str) or not text.strip():
        return text

    words = text.lower().split()  # Convert to lowercase for case-insensitive matching
    expanded_words = []

    for word in words:
        # Check if the word is in our comprehensive abbreviation dictionary
        if word in AUTOMOTIVE_ABBR:
            expanded_words.append(AUTOMOTIVE_ABBR[word])
            # print(f"    Comprehensive abbrev: '{word}' -> '{AUTOMOTIVE_ABBR[word]}'")  # Disabled for performance
        else:
            expanded_words.append(word)

    return " ".join(expanded_words)


def get_noun_gender(word: str) -> str:
    """
    Determines the gender of Spanish automotive nouns.

    Args:
        word: The noun to analyze

    Returns:
        'masculine' or 'feminine'
    """
    word = word.lower()

    # Explicit masculine automotive parts
    masculine_parts = {
        'guardafango', 'guardabarros', 'paragolpes', 'parachoques', 'espejo',
        'retrovisor', 'faro', 'piloto', 'intermitente', 'absorbedor',
        'amortiguador', 'radiador', 'electroventilador', 'ventilador',
        'filtro', 'motor', 'alternador', 'compresor', 'condensador',
        'evaporador', 'intercooler', 'turbo', 'catalizador', 'silenciador',
        'tubo', 'colector', 'multiple', 'deposito', 'tanque', 'carter',
        'diferencial', 'eje', 'semieje', 'cardan', 'tensor', 'rodamiento',
        'cojinete', 'reten', 'soporte', 'brazo', 'triangulo', 'rotula',
        'estabilizador', 'bieleta', 'tirante', 'travesano', 'larguero',
        'refuerzo', 'marco', 'chasis', 'bastidor', 'capo', 'maletero',
        'techo', 'techo', 'cristal', 'vidrio', 'elevalunas', 'regulador',
        'guardapolvo', 'broche', 'remache', 'tornillo', 'perno',  # Added missing parts
        'emblema', 'portaplaca'  # Gender exceptions: words ending in 'a' but masculine
    }

    # Explicit feminine automotive parts
    feminine_parts = {
        'farola', 'luz', 'lampara', 'bombilla', 'optica', 'tulipa',
        'puerta', 'ventana', 'ventanilla', 'luna', 'aleta', 'chapa',
        'carroceria', 'pintura', 'moldura', 'maneta', 'manilla', 'cerradura',
        'bisagra', 'goma', 'junta', 'correa', 'cadena', 'polea', 'rueda',
        'llanta', 'cubierta', 'neumatico', 'camara', 'valvula', 'bujia',
        'bobina', 'bateria', 'dinamo', 'bomba', 'manguera', 'tuberia',
        'conexion', 'union', 'abrazadera', 'brida', 'tapa', 'cubierta',
        'carcasa', 'caja', 'palanca', 'varilla', 'barra', 'biela',
        'cruceta', 'horquilla', 'zapata', 'pastilla', 'lona', 'banda',
        'placa', 'chapa', 'plancha', 'rejilla', 'parrilla', 'mascara',
        'guia', 'tuerca', 'arandela', 'puntera'  # Added: GUIA is feminine (la guía), PUNTERA is feminine (la puntera)
    }

    if word in masculine_parts:
        return 'masculine'
    elif word in feminine_parts:
        return 'feminine'
    else:
        # Default rules based on Spanish grammar
        if word.endswith(('o', 'or', 'aje', 'an', 'en', 'in', 'on', 'un')):
            return 'masculine'
        elif word.endswith(('a', 'ion', 'dad', 'tad', 'tud', 'ez', 'eza', 'sis', 'itis')):
            return 'feminine'
        else:
            # Default to masculine for unknown cases
            return 'masculine'


def expand_linguistic_variations_text(text: str) -> str:
    """
    Expands linguistic variations in Spanish automotive text:
    - Comprehensive automotive abbreviations (from AUTOMOTIVE_ABBR dictionary)
    - Context-aware abbreviations: handles 'd' and 't' based on part type
    - Gender-aware abbreviations: izq -> izquierdo/izquierda based on noun gender
    - Standard abbreviations with proper gender agreement
    - Plural variations: farolas -> farola (normalize to singular, except specific cases)

    This is independent of industry synonyms and handles basic Spanish linguistic patterns.
    """
    if not text:
        return text

    # Step 1: Apply comprehensive automotive abbreviation expansion first
    text = expand_comprehensive_abbreviations(text)

    words = text.split()
    expanded_words = []

    # Step 2: Handle special abbreviation patterns (like "D I" = "DELANTERO IZQUIERDO")
    words = handle_abbreviation_patterns(words)

    for i, word in enumerate(words):
        # Handle context-dependent single-letter abbreviations
        if word in ['d', 't'] and i > 0:
            # Find the main noun for context, not just the previous word
            context_word = find_main_noun_for_context(words, i)
            expanded_word = expand_context_dependent_abbreviation(word, context_word)
        # Handle gender-dependent abbreviations AND full words that need gender agreement
        elif word in ['i', 'iz', 'izq', 'der', 'dere', 'derec', 'derech', 'del', 'dl', 'delan', 'delant', 'delante', 'tra', 'tras', 'trase', 'traser',
                     'izquierdo', 'izquierda', 'derecho', 'derecha', 'delantero', 'delantera', 'trasero', 'trasera']:
            # Pass complete context for better gender agreement analysis
            expanded_word = expand_gender_dependent_abbreviation(
                word, words[i-1] if i > 0 else "", all_words=words, word_index=i)
        else:
            expanded_word = expand_single_word_linguistic(word)
        expanded_words.append(expanded_word)

    return ' '.join(expanded_words)


def find_main_noun_for_context(words: list, current_index: int) -> str:
    """
    Finds the main noun that should provide context for abbreviation expansion.

    For phrases like "GUIA LATERAL D", we want "GUIA" (the main noun), not "LATERAL" (adjective).

    Args:
        words: List of words in the phrase
        current_index: Index of the current abbreviation being processed

    Returns:
        The main noun that should provide context
    """
    if current_index <= 0:
        return ""

    # Define common automotive adjectives that are not main nouns
    adjectives = {
        'lateral', 'superior', 'inferior', 'central', 'medio', 'exterior', 'interior',
        'plastico', 'metalico', 'cromado', 'negro', 'blanco', 'transparente',
        'grande', 'pequeno', 'largo', 'corto', 'ancho', 'estrecho'
    }

    # Look backwards from current position to find the main noun
    for i in range(current_index - 1, -1, -1):
        word = words[i].lower()

        # Skip adjectives and look for the main noun
        if word not in adjectives:
            return word

    # Fallback to previous word if no main noun found
    return words[current_index - 1] if current_index > 0 else ""


def handle_abbreviation_patterns(words: list) -> list:
    """
    Handles special abbreviation patterns that require contextual analysis.

    LOGICAL RULE: A part cannot be both LEFT and RIGHT simultaneously!

    Recognizes ALL abbreviation combinations:
    - Position abbreviations: D, DE, DEL, DELAN, DELANT, T, TR, TRA, TRAS, TRASE
    - Side abbreviations: I, IZ, IZQ, IZQU, DER, DERE, DEREC, DERECH

    Examples:
    - "D I" -> "DELANTERO IZQUIERDO" (front left)
    - "D IZQU" -> "DELANTERO IZQUIERDO" (front left)
    - "DEL IZ" -> "DELANTERO IZQUIERDO" (front left)
    - "T DER" -> "TRASERO DERECHO" (rear right)
    - "TRA I" -> "TRASERO IZQUIERDO" (rear left)

    The system applies logical spatial reasoning to avoid impossible combinations.

    Args:
        words: List of words to process

    Returns:
        List of words with patterns expanded using logical spatial rules
    """
    if len(words) < 2:
        return words

    # Define abbreviation groups
    position_front_abbrevs = {'d', 'de', 'del', 'delan', 'delant', 'delante'}
    position_rear_abbrevs = {'t', 'tr', 'tra', 'tras', 'trase', 'traser'}
    side_left_abbrevs = {'i', 'iz', 'izq', 'izqu', 'izqui', 'izquie', 'izquier'}
    side_right_abbrevs = {'der', 'dere', 'derec', 'derech', 'derecho', 'derecha'}

    result = []
    i = 0

    while i < len(words):
        current_word = words[i].lower()
        next_word = words[i + 1].lower() if i + 1 < len(words) else ""

        # Find immediate noun for gender agreement (FIXED)
        # For pattern matching, we need to find the noun that the directional adjectives should agree with
        immediate_noun = ""

        # Look backwards from the current position to find the nearest noun
        for j in range(i - 1, -1, -1):
            word = words[j].lower()
            if word in {'guia', 'farola', 'luz', 'puerta', 'aleta', 'chapa', 'rejilla', 'parrilla', 'mascara',
                       'guardafango', 'paragolpes', 'espejo', 'faro', 'absorbedor', 'radiador', 'soporte',
                       'guardapolvo', 'bomper', 'bumper', 'capo', 'tapa', 'cubierta', 'moldura',
                       'broches', 'broche', 'remache', 'remaches', 'emblema', 'portaplaca', 'puntera'}:
                immediate_noun = word
                break

        gender = get_noun_gender(immediate_noun) if immediate_noun else 'masculine'
        # print(f"    Pattern gender agreement: position {i}, immediate noun: '{immediate_noun}' ({gender})")  # Disabled for performance

        # Check if current word is a position abbreviation
        is_front = current_word in position_front_abbrevs
        is_rear = current_word in position_rear_abbrevs

        # Check if next word is a side abbreviation
        is_left = next_word in side_left_abbrevs
        is_right = next_word in side_right_abbrevs

        # Handle FRONT + LEFT patterns (D I, DEL IZQU, etc.)
        if is_front and is_left:
            if gender == 'feminine':
                result.append('delantera')
                result.append('izquierda')
            else:
                result.append('delantero')
                result.append('izquierdo')
            i += 2  # Skip both words
        # Handle FRONT + RIGHT patterns (D DER, DEL DERECH, etc.)
        elif is_front and is_right:
            if gender == 'feminine':
                result.append('delantera')
                result.append('derecha')
            else:
                result.append('delantero')
                result.append('derecho')
            i += 2
        # Handle REAR + LEFT patterns (T I, TRA IZQU, etc.)
        elif is_rear and is_left:
            if gender == 'feminine':
                result.append('trasera')
                result.append('izquierda')
            else:
                result.append('trasero')
                result.append('izquierdo')
            i += 2
        # Handle REAR + RIGHT patterns (T DER, TRAS DERECH, etc.)
        elif is_rear and is_right:
            if gender == 'feminine':
                result.append('trasera')
                result.append('derecha')
            else:
                result.append('trasero')
                result.append('derecho')
            i += 2
        # Special case: Handle "D D" as FRONT + RIGHT (since D can be both)
        elif current_word == 'd' and next_word == 'd':
            if gender == 'feminine':
                result.append('delantera')
                result.append('derecha')
            else:
                result.append('delantero')
                result.append('derecho')
            i += 2
        else:
            # No pattern match, keep original word
            result.append(words[i])
            i += 1

    return result


def find_immediate_noun_for_adjective(words: list, current_index: int) -> str:
    """
    Finds the immediate noun that an adjective should agree with in Spanish automotive terms.

    CORRECT Spanish Grammar Rule:
    Each adjective agrees with its IMMEDIATE noun, not the first noun in the phrase.

    Examples:
    - "GUIA LATERAL IZQUIERDA PARAGOLPES DELANTERO"
      * "LATERAL IZQUIERDA" agree with "GUIA" (feminine)
      * "DELANTERO" agrees with "PARAGOLPES" (masculine)

    - "BROCHES GUARDAPOLVO PLASTICO DELANTERO DERECHO"
      * "PLASTICO" agrees with "GUARDAPOLVO" (masculine)
      * "DELANTERO DERECHO" agree with "GUARDAPOLVO" (masculine)

    Args:
        words: List of words in the phrase
        current_index: Index of the current adjective being processed

    Returns:
        The immediate noun that should determine gender agreement for this adjective
    """
    # Look backwards from current position to find the nearest noun
    for i in range(current_index - 1, -1, -1):
        word = words[i].lower()

        # Check if this word is a known automotive noun
        if word in {'guia', 'farola', 'luz', 'puerta', 'aleta', 'chapa', 'rejilla', 'parrilla', 'mascara',
                   'guardafango', 'paragolpes', 'espejo', 'faro', 'absorbedor', 'radiador', 'soporte',
                   'bomper', 'bumper', 'capo', 'tapa', 'cubierta', 'moldura', 'maneta', 'cerradura',
                   'guardapolvo', 'broches', 'broche', 'remache', 'remaches', 'tornillo', 'tornillos',
                   'perno', 'pernos', 'tuerca', 'tuercas', 'arandela', 'arandelas', 'emblema', 'portaplaca',
                   'puntera'}:
            return word

        # Check if it's a noun based on Spanish grammar rules
        if (word.endswith(('o', 'a', 'or', 'aje', 'an', 'en', 'in', 'on', 'un', 'ion', 'dad', 'tad', 'tud', 'ez', 'eza'))
            and len(word) > 2):  # Avoid single letters and very short words
            # Additional check: make sure it's not an adjective we just processed
            if word not in {'lateral', 'izquierdo', 'izquierda', 'derecho', 'derecha',
                           'delantero', 'delantera', 'trasero', 'trasera', 'superior', 'inferior',
                           'plastico', 'plastica', 'metalico', 'metalica', 'cromado', 'cromada'}:
                return word

    # Final fallback: use the immediately preceding word if it exists
    if current_index > 0:
        return words[current_index - 1].lower()

    return ""


def expand_gender_dependent_abbreviation(abbrev: str, context_word: str, all_words: list = None, word_index: int = -1) -> str:
    """
    Expands gender-dependent abbreviations based on the gender of the IMMEDIATE noun.

    FIXED: Now uses correct Spanish grammar - each adjective agrees with its immediate noun,
    not the first noun in the phrase.

    Args:
        abbrev: The abbreviation ('i', 'iz', 'izq', 'der', 'del', 'tra', etc.)
        context_word: The immediately preceding word (for backward compatibility)
        all_words: Complete list of words in the phrase (for better context analysis)
        word_index: Index of the current abbreviation in all_words

    Returns:
        The expanded form with proper gender agreement
    """
    if not abbrev:
        return abbrev

    # Determine the gender using IMMEDIATE noun analysis (FIXED)
    if all_words and word_index >= 0:
        immediate_noun = find_immediate_noun_for_adjective(all_words, word_index)
        gender = get_noun_gender(immediate_noun) if immediate_noun else 'masculine'
        # print(f"    Gender agreement: '{abbrev}' → immediate noun: '{immediate_noun}' ({gender}) → ", end="")  # Disabled for performance
    else:
        # Fallback to old behavior for backward compatibility
        gender = get_noun_gender(context_word) if context_word else 'masculine'
        # print(f"    Gender agreement (fallback): '{abbrev}' → context: '{context_word}' ({gender}) → ", end="")  # Disabled for performance

    # Map abbreviations AND full words to their correct gender forms
    if abbrev in ['i', 'iz', 'izq', 'izquierdo', 'izquierda']:
        result = 'izquierdo' if gender == 'masculine' else 'izquierda'
        # print(f"'{result}'")  # Disabled for performance
        return result
    elif abbrev in ['der', 'dere', 'derec', 'derech', 'derecho', 'derecha']:
        result = 'derecho' if gender == 'masculine' else 'derecha'
        # print(f"'{result}'")  # Disabled for performance
        return result
    elif abbrev in ['del', 'dl', 'delan', 'delant', 'delante', 'delantero', 'delantera']:
        result = 'delantero' if gender == 'masculine' else 'delantera'
        # print(f"'{result}'")  # Disabled for performance
        return result
    elif abbrev in ['tra', 'tras', 'trase', 'traser', 'trasero', 'trasera']:
        result = 'trasero' if gender == 'masculine' else 'trasera'
        # print(f"'{result}'")  # Disabled for performance
        return result

    # Return unchanged if not handled
    # print(f"'{abbrev}' (unchanged)")  # Disabled for performance
    return abbrev


def expand_context_dependent_abbreviation(abbrev: str, context_word: str) -> str:
    """
    Expands context-dependent single-letter abbreviations based on the automotive part type.

    Args:
        abbrev: The abbreviation ('d' or 't')
        context_word: The preceding word that provides context (e.g., 'farola', 'paragolpes')

    Returns:
        The expanded form based on context
    """
    if not abbrev or not context_word:
        return abbrev

    # Define part categories and their abbreviation meanings
    part_categories = {
        # Parts with LEFT/RIGHT positioning (d = derecha, i = izquierda)
        'lateral_parts': {
            'espejo', 'espejos', 'guardafango', 'guardafangos',
            'guardabarro', 'guardabarros', 'puerta', 'puertas',
            'farola', 'farolas', 'faro', 'faros',  # FIXED: Headlights are primarily LEFT/RIGHT positioned
            'guia', 'guias'  # FIXED: GUIA is a lateral part (left/right positioning)
        },

        # Parts with FRONT/REAR positioning (d = delantero, t = trasero)
        'longitudinal_parts': {
            'paragolpes', 'paragolpe', 'bomper', 'defensa',
            'traviesa', 'traviesas', 'refuerzo', 'refuerzos'
        },

        # Special case: Compound light descriptions where context matters
        # e.g., "luz antiniebla delantera" vs "farola derecha"
        'compound_light_parts': {
            'luz', 'luces'  # Only generic "luz" needs context analysis
        }
    }

    # Determine part category with enhanced context analysis
    part_category = None

    # Standard category detection - check all categories
    for category, parts in part_categories.items():
        if context_word in parts:
            part_category = category
            break

    # Special handling for compound light descriptions (e.g., "luz antiniebla")
    # Only generic "luz" needs special context analysis, not specific lights like "farola"
    if context_word in part_categories.get('compound_light_parts', set()):
        # For generic "luz", we need more context to determine if it's front/rear or left/right
        # Default to front/rear for compound light descriptions
        part_category = 'longitudinal_parts'

    # Expand based on context with proper gender agreement
    if abbrev == 'd':
        if part_category == 'lateral_parts':
            # Apply gender agreement for lateral positioning (derecho/derecha)
            gender = get_noun_gender(context_word)
            return 'derecho' if gender == 'masculine' else 'derecha'
        elif part_category == 'longitudinal_parts':
            # Apply gender agreement for longitudinal positioning (delantero/delantera)
            gender = get_noun_gender(context_word)
            return 'delantero' if gender == 'masculine' else 'delantera'
        else:
            # Default to 'derecha' for unknown contexts (most common in automotive)
            gender = get_noun_gender(context_word)
            return 'derecho' if gender == 'masculine' else 'derecha'

    elif abbrev == 'i':
        # 'i' means 'izquierdo/izquierda' (left) - apply gender agreement
        gender = get_noun_gender(context_word)
        return 'izquierdo' if gender == 'masculine' else 'izquierda'

    elif abbrev == 't':
        # 't' almost always means 'trasero' in automotive context - apply gender agreement
        gender = get_noun_gender(context_word)
        return 'trasero' if gender == 'masculine' else 'trasera'

    # Return unchanged if not handled
    return abbrev


def expand_single_word_linguistic(word: str) -> str:
    """
    Expands a single word for linguistic variations.
    Note: This function handles abbreviations and plurals, but NOT gender normalization.
    Gender variations are handled during similarity matching, not normalization.

    For context-dependent abbreviations, this function only handles clear cases.
    Ambiguous single letters are handled by expand_linguistic_variations_text()
    which has access to the full text context.
    """
    if not word:
        return word

    # 1. Abbreviation expansion (directional terms) - CLEAR CASES ONLY
    # Note: Gender-dependent abbreviations (i, iz, izq, der, etc.) are handled
    # by expand_gender_dependent_abbreviation() in the main text processing
    abbreviation_map = {
        # FRONT variations (gender-neutral or context will determine)
        'del': 'delantero',  # Default to masculine, context may override
        'delan': 'delantero',
        'delant': 'delantero',
        'delante': 'delantero',

        # REAR variations (gender-neutral or context will determine)
        'tra': 'trasero',  # Default to masculine, context may override
        'tras': 'trasero',
        'trase': 'trasero',
        'traser': 'trasero',

        # OTHER directional (these are typically gender-neutral)
        'sup': 'superior',
        'super': 'superior',
        'inf': 'inferior',
        'infer': 'inferior',
        'ant': 'anterior',
        'anter': 'anterior',
        'post': 'posterior',
        'poster': 'posterior',
    }

    # Check abbreviations first
    if word in abbreviation_map:
        return abbreviation_map[word]

    # 2. Plural normalization (context-independent)
    plural_map = {
        'farolas': 'farola',
        'luces': 'luz',
        'espejos': 'espejo',
        'puertas': 'puerta',
        'paragolpe': 'paragolpes',  # This one goes to plural (standard form)
        'guardafangos': 'guardafango',
        'guardabarros': 'guardabarro',
    }

    if word in plural_map:
        return plural_map[word]

    # No expansion needed - ambiguous cases handled at text level
    return word


def are_gender_variants(word1: str, word2: str) -> bool:
    """
    Checks if two words are gender variants of each other.
    Returns True if they are masculine/feminine versions of the same word.

    Examples:
    - derecho/derecha -> True
    - izquierdo/izquierda -> True
    - farola/farola -> False (same word)

    CASE-INSENSITIVE: All comparisons are done in lowercase.
    """
    if not word1 or not word2:
        return False

    # Convert to lowercase for case-insensitive comparison
    word1 = word1.lower()
    word2 = word2.lower()

    if word1 == word2:
        return False

    # Define gender pairs (masculine, feminine)
    gender_pairs = [
        ('derecho', 'derecha'),
        ('izquierdo', 'izquierda'),
        ('delantero', 'delantera'),
        ('trasero', 'trasera'),
    ]

    for masculine, feminine in gender_pairs:
        if (word1 == masculine and word2 == feminine) or (word1 == feminine and word2 == masculine):
            return True

    return False


if __name__ == '__main__':
    # Test cases
    test_strings = {
        "  Texto CON Ácentos y Múltiples   Espacios!!  ": "texto con acentos y multiples espacios",
        "CAPÓ DELANTERO": "capo delantero",
        "Lámpara Trasera Izquierda (Stop)": "lampara trasera izquierda stop",
        "Rin 17\" Lujo": "rin 17 lujo",
        "GUARDABARRO DEL. DER.": "guardabarro del der",
        "Puerta Delantera Izquierda": "puerta delantera izquierda",
        "  Múltiples   \t\n   espacios  ": "multiples espacios",
        "SinPuntuaciónNiAcentos": "sinpuntuacionniacentos",
        "Número123": "numero123",
        "BOMPER TRASERO C/HUECOS SENSORES": "bomper trasero chuecos sensores",  # c/ is removed
        "Fáröla Ízquíérdá": "farola izquierda"
    }

    for original, expected in test_strings.items():
        normalized = normalize_text(original)
        print(f"Original: '{original}'")
        print(f"Normalized: '{normalized}'")
        print(f"Expected:   '{expected}'")
        print(f"Match: {normalized == expected}\n")

    # Test with None or non-string
    print(f"Normalizing None: '{normalize_text(None)}'")
    # print(f"Normalizing a number (123): '{normalize_text(123)}'") # This would error if not handled
