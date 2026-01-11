"""
Text Normalizer - Post-processing for transcribed text
Fixes common speech-to-text issues for Turkish
"""
import re
from typing import Optional

class TextNormalizer:
    """
    Normalizes transcribed text to fix common STT errors.
    Runs BEFORE sending to LLM.
    """
    
    # Turkish speech patterns that map to special characters
    # Order matters - more specific patterns first
    SPEECH_PATTERNS = [
        # Very specific site patterns first (handle Whisper errors)
        (r'sahibinden\s*nokta\s*komşu\s*tesine', 'sahibinden.com sitesine'),
        (r'sahibinden\s*nokta\s*komşu\s*desin\s*aç', 'sahibinden.com sitesini aç'),  # Specific fix for reported issue
        (r'sahibinden\s*nokta\s*komşu', 'sahibinden.com'),
        (r'komşu\s*desin', '.com sitesini'), # "com sitesini" -> "komşu desin"
        (r'kuronda', "Chrome'da"), # "Chrome'da" -> "Kuronda"
        (r'uframda', "Chrome'da"), # "Chrome'da" -> "Uframda"
        (r'tezin\s*aç', 'sitesini aç'), # "sitesini aç" -> "tezin aç"
        (r'sahibinden\s*\.\s*komşu\s*tesine', 'sahibinden.com sitesine'),
        (r'sahibinden\s*\.\s*komşu', 'sahibinden.com'),
        (r'sahibinden\s*nokta\s*kom', 'sahibinden.com'),
        
        # Common Whisper mistakes for ".com"
        (r'nokta\s*komşu', '.com'),
        (r'nokta\s*kom\b', '.com'),
        (r'nokta\s*come', '.com'),
        
        # Other TLDs
        (r'nokta\s*net\b', '.net'),
        (r'nokta\s*org\b', '.org'),
        (r'nokta\s*io\b', '.io'),
        (r'nokta\s*co\b', '.co'),
        
        # Generic "nokta" for remaining cases
        (r'\bnokta\b', '.'),
        
        # Other special chars
        (r'\bslash\b', '/'),
        (r'\bat\b', '@'),
        
        # Common site name fixes
        (r'youtube\s*nokta\s*kom', 'youtube.com'),
        (r'google\s*nokta\s*kom', 'google.com'),
        (r'github\s*nokta\s*kom', 'github.com'),
        
        # Cleanup: "tesine" often means "sitesine"
        (r'(\.\w+)\s*tesine', r'\1 sitesine'),
    ]
    
    # Patterns that indicate a URL intent
    URL_INDICATORS = [
        r'sitesine\s*(git|gir|aç)',
        r'sayfasına\s*(git|gir|aç)',
        r'adresine\s*(git|gir|aç)',
        r"'a\s*(git|gir|aç)",
        r"'e\s*(git|gir|aç)",
    ]
    
    def normalize(self, text: str) -> str:
        """Apply all normalizations to the text"""
        result = text
        
        # Apply speech pattern replacements (case insensitive)
        for pattern, replacement in self.SPEECH_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def detect_url_intent(self, text: str) -> Optional[str]:
        """
        Detect if the user is trying to navigate to a URL.
        Returns the detected URL or None.
        """
        # Check for URL indicators
        for pattern in self.URL_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                # Try to extract the URL
                # Look for patterns like "X.com" or "X sitesine"
                url_match = re.search(r'(\w+\.\w+)', text)
                if url_match:
                    return url_match.group(1)
        
        return None

# Global instance
_normalizer: Optional[TextNormalizer] = None

def get_normalizer() -> TextNormalizer:
    global _normalizer
    if _normalizer is None:
        _normalizer = TextNormalizer()
    return _normalizer
