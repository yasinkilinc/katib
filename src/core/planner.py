import json
from typing import Dict, Optional
from .llm import LLMService
from .logger import get_logger
from src.schemas.plan import Plan

logger = get_logger("Planner")

class Planner:
    def __init__(self, memory_engine=None):
        self.llm = LLMService()
        self.memory = memory_engine

    def generate_plan(self, user_command: str, failure_context: list = None) -> Plan:
        """
        Converts Raw User Command -> Structured Plan (Plan object)
        """
        logger.info(f"Generating plan for command: '{user_command}'")
        
        # Base system prompt
        system_prompt = """You are a senior task planner for 'Katib', an advanced local AI agent.

GOAL: Convert user voice commands into a structured, multi-step execution plan.

CAPABILITIES:
- web.search(query): Search Google/Web.
- web.navigate(url): Go to a specific URL.
- web.extract(selector): Extract text from page.
- app.open(app_name): Open a macOS application.
- app.close(app_name): Close a macOS application.
- system.volume(level): Set volume (0-100).
- tts.speak(text): Speak to the user.
- llm.summarize(context_from_step, instruction): Summarize content from a previous step.
- llm.generate(prompt): Generate text based on a prompt.
- terminal.execute(command): Execute a terminal command.

OUTPUT FORMAT (JSON ONLY):
{
  "goal": "Brief summary of what the user wants",
  "reasoning": "Why you chose these steps",
  "steps": [
    {
      "id": 1,
      "name": "step_name",
      "capability": "capability.name",
      "params": {"param_key": "param_value"},
      "requires_feedback": true/false
    }
  ]
}

RULES:
1. **Multi-step:** Break down complex tasks. (e.g. "Find news and summarize" -> Search -> Extract -> Summarize).
2. **Feedback:** distinct 'search' steps generally require feedback (requires_feedback=true) to get results before proceeding.
3. **Context Passing:** Use "context_from_step": <step_id> in params to reference output from a previous step.
4. **Phonetic Fix:** "uframda" -> "Chrome", "kom" -> ".com".
5. **Safety:** Do not hallucinate capabilities not listed.

EXAMPLES:

User: "Google'ı aç ve dolar ne kadar diye bak"
JSON:
{
  "goal": "Check dollar rate on Google",
  "reasoning": "Open browser, go to Google, and search for dollar rate.",
  "steps": [
    {
      "id": 1, 
      "name": "open_browser", 
      "capability": "app.open", 
      "params": {"app_name": "Safari"}, 
      "requires_feedback": false
    },
    {
      "id": 2, 
      "name": "search_dollar", 
      "capability": "web.search", 
      "params": {"query": "dolar ne kadar"}, 
      "requires_feedback": true
    }
  ]
}

User: "Sistem durumunu kontrol et ve özetle"
JSON:
{
  "goal": "Check system status and summarize",
  "reasoning": "Run system check command, then summarize the output using LLM.",
  "steps": [
    {
      "id": 1,
      "name": "check_system",
      "capability": "terminal.execute",
      "params": {"command": "top -l 1 -s 0 | head -20"},
      "requires_feedback": false
    },
    {
      "id": 2,
      "name": "summarize_status",
      "capability": "llm.summarize",
      "params": {"context_from_step": 1, "instruction": "Bu sistem durumunu özetle"},
      "requires_feedback": false
    }
  ]
}
"""
        
        # Dynamic Learning: Add recent successful examples
        if self.memory:
            dynamic_examples = self._get_dynamic_examples()
            if dynamic_examples:
                system_prompt += f"\n\nRECENT SUCCESSFUL COMMANDS:\n{dynamic_examples}"
        
        # Add failure context if exists
        failures = ""
        if failure_context:
            failures = f"\nAvoid strategies that led to: {json.dumps(failure_context)}"
        
        user_prompt = f'COMMAND: "{user_command}"{failures}\n\nJSON:'
        
        response_dict = self.llm.generate_response(system_prompt, user_prompt)
        
        # Validations and Parsing
        try:
            # LLM might return just the dict, we need to ensure it matches Plan schema
            # If LLM returns raw json string inside the dict or something unexpected, handle it.
            # Assuming self.llm.generate_response returns a DICT parsed from JSON.
            
            # Validation for Plan schema
            plan = Plan(**response_dict)
            
            logger.info(f"Plan generated: {len(plan.steps)} steps")
            return plan

        except Exception as e:
            logger.error(f"Failed to parse plan: {e}. Response: {response_dict}")
            # Fallback empty plan
            return Plan(goal="Error parsing plan", steps=[], reasoning=str(e))
    
    def _get_dynamic_examples(self) -> str:
        """Format recent successful plans as examples for LLM"""
        # Note: This logic might need update to match new schema structure in memory
        # For now, keeping it basic or assuming memory stores raw JSONs that are compatible-ish
        # or skipping if memory engine isn't updated for new schema yet.
        if not self.memory:
            return ""

        successful = self.memory.get_successful_plans(limit=3)
        if not successful:
            return ""
        
        examples = []
        for entry in successful:
            cmd = entry.get("command", "")
            plan_data = entry.get("plan", {})
            if cmd and plan_data:
                examples.append(f'User: "{cmd}"\n{json.dumps(plan_data, ensure_ascii=False)}')
        
        return "\n\n".join(examples)
