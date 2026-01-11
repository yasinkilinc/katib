import json
from .llm import LLMService

class Planner:
    def __init__(self):
        self.llm = LLMService()

    def generate_plan(self, user_command: str, failure_context: list = None) -> dict:
        """
        Converts Raw User Command -> List of Steps (Plan)
        """
        
        system_prompt = """
        You are a rigid JSON command generator for a voice assistant named Katib.
        Input: "User Command"
        Output: JSON Object matching the strict schema below.

        TOOLS:
        - app.open(app_name)
        - app.close(app_name)
        - app.focus(app_name)
        - web.navigate(url)
        - web.close_tab(title_match)
        - tts.speak(text)
        - system.volume(level)
        - system.stop() -> Exit the assistant.
        
        CORRECTION RULES:
        1. Fix phonetic errors (e.g. "uframda"->"Chrome", "kom"->".com").
        2. "sitesini kapat" -> web.close_tab(title_match="...").
        3. "Katib'i kapat" -> system.stop().
        
        STRICT JSON OUTPUT FORMAT:
        {
          "steps": [
            {"action": "tool.name", "parameters": {"param": "value"}}
          ],
          "reasoning": "Concise explanation"
        }

        EXAMPLES:
        User: "Google'ı aç"
        JSON: {"steps": [{"action": "web.navigate", "parameters": {"url": "google.com"}}], "reasoning": "Navigate to google"}
        
        User: "Chrome'da sahibinden.com sitesini kapat"
        JSON: {"steps": [{"action": "web.close_tab", "parameters": {"title_match": "sahibinden"}}], "reasoning": "Close tab"}
        
        User: "Katib'i kapat"
        JSON: {"steps": [{"action": "system.stop", "parameters": {}}], "reasoning": "Exit"}
        """
        
        # Add failure context if exists
        failures = ""
        if failure_context:
            failures = f"\nAvoid these (failed previously): {json.dumps(failure_context)}"
        
        user_prompt = f"""
        COMMAND: "{user_command}"
        {failures}
        
        Generate JSON:
        """
        
        response = self.llm.generate_response(system_prompt, user_prompt)
        
        # Validations could go here
        if "steps" not in response:
            response["steps"] = []
            
        return response
            
        return response
