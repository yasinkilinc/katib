from typing import Dict, Any

class UIFallbackGate:
    """
    Decides whether to block execution and fallback to UI.
    Does NOT execute actions.
    """
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold

    def should_fallback(self, intent_data: Dict[str, Any]) -> bool:
        """
        Returns True if confidence is low or risk is high.
        """
        confidence = intent_data.get("confidence", 1.0)
        
        # If intent is very uncertain, fallback (return True)
        if confidence < self.confidence_threshold:
            return True
            
        return False

    def decide(self, plan_step: Dict[str, Any]) -> bool:
        """
        Decide if a specific step requires UI fallback intervention
        (e.g. if it's too risky for headless execution).
        """
        # Placeholder for deeper logic
        return False
