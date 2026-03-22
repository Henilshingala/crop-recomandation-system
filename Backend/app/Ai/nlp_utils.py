import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import re

# These will download when the module is first imported if not present
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except:
    pass

ENGLISH_STOPWORDS = set(stopwords.words('english'))

CUSTOM_STOPWORDS = {
    'hi', 'the', 'a', 'an', 'is', 'are', 'was', 'were',
    'i', 'me', 'my', 'we', 'you', 'your', 'it', 'this',
    'that', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
    'for', 'of', 'with', 'as', 'by', 'from'
}

ALL_STOPWORDS = ENGLISH_STOPWORDS.union(CUSTOM_STOPWORDS)

def tokenize_and_clean(text):
    """
    Step 1: Take input sentence
    Step 2: Split all words → store in list
    Step 3: Remove stopwords, lowercase, remove English punctuation safely
    Step 4: Return cleaned meaningful string
    """
    if not text:
        return ""
        
    # Lowercase
    text = text.lower().strip()
    
    # Safe punctuation removal that doesn't destroy Unicode combining characters (like Hindi matras)
    # We only strip standard ASCII punctuation
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # Use simple whitespace split instead of NLTK word_tokenize 
    # because NLTK destroys non-English text by splitting on Unicode boundaries
    tokens = text.split()
    
    # Remove stopwords
    cleaned_tokens = []
    for token in tokens:
        # For non-English scripts, length 1 is valid (e.g. "न"). For English, we keep len > 1.
        # But to be safe across all 23 languages, we just keep all non-stopwords.
        if token not in ALL_STOPWORDS:
            cleaned_tokens.append(token)
    
    # If cleaning removed everything, return original (lowercased)
    if not cleaned_tokens:
        return text
    
    return ' '.join(cleaned_tokens)


def detect_language(text):
    """Detect language of user input"""
    try:
        from langdetect import detect
        lang = detect(text)
        return lang
    except:
        return 'en'
