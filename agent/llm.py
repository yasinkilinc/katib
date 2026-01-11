"""
LLM Wrapper for Agent - Handles tool selection reasoning.
"""
import json
import httpx
from typing import Dict, Any, List, Optional

class LLMToolSelector:
    """
    LLM wrapper that decides which tools to use.
    Platform-agnostic - doesn't know about macOS.
    """
    
    def __init__(self, api_url: str = "http://localhost:11434/api/chat", model: str = "llama3.2"):
        self.api_url = api_url
        self.model = model
    
    def decide_tools(self, user_intent: str, available_tools: List[Dict[str, Any]], 
                      context: str = "") -> List[Dict[str, Any]]:
        """
        Given user intent and available tools, decide which tools to call.
        Returns a list of tool calls with parameters.
        """
        # Build prompt with available tools
        tools_desc = self._format_tools(available_tools)
        
        context_section = f"\nCONTEXT: {context}\n" if context else ""
        # Build prompt with available tools
        tools_desc = self._format_tools(available_tools)
        
        system_prompt = f"""You are a tool selection agent. Your job is to select the right tools to accomplish the user's request.

AVAILABLE TOOLS:
{tools_desc}

RULES:
- Output JSON only
- Select minimum tools needed
- Parameters must match tool input schema
- PREFER SAFE TOOLS over fallback/unsafe tools (like ui_click, ui_type) unless absolutely necessary
- If unsure, use tts_speak to ask for clarification

OUTPUT FORMAT:
{{
  "tool_calls": [
    {{"name": "tool_name", "parameters": {{"param1": "value1"}}}}
  ]
}}

EXAMPLES:

User: "Safari'yi aç"
{{"tool_calls": [{{"name": "open_application", "parameters": {{"app_name": "Safari"}}}}]}}

User: "sahibinden.com'a git"
{{"tool_calls": [{{"name": "web_navigate", "parameters": {{"url": "sahibinden.com"}}}}]}}

User: "sesi %50 yap"
{{"tool_calls": [{{"name": "set_volume", "parameters": {{"level": 50}}}}]}}
"""
        
        user_prompt = f"User intent: {user_intent}\n\nSelect the appropriate tools:"
        
        # Call LLM
        response = self._call_llm(system_prompt, user_prompt)
        
        # Parse response
        return self._parse_response(response)
    
    def _format_tools(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools for LLM prompt"""
        lines = []
        for tool in tools:
            params = tool.get("parameters", {}).get("properties", {})
            param_str = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in params.items())
            lines.append(f"- {tool['name']}: {tool['description']} (params: {param_str})")
        return "\n".join(lines)
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama API"""
        try:
            response = httpx.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "num_predict": 200,
                        "temperature": 0.1
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"[!] LLM call failed: {e}")
            return '{"tool_calls": []}'
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract tool calls"""
        import re
        
        try:
            # Try to find JSON object in response
            # Method 1: Look for markdown code block
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1]
            
            # Method 2: Find JSON object with regex
            # Look for "tool_calls" key specifically
            json_match = re.search(r'\{.*"tool_calls"\s*:\s*\[.*?\].*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            else:
                # Use a wider net if the first one failed, looking for any valid JSON structure starting with { and having "tool_calls"
                json_match_wide = re.search(r'\{[\s\S]*"tool_calls"[\s\S]*\}', response)
                if json_match_wide:
                    response = json_match_wide.group(0)
            
            data = json.loads(response.strip())
            return data.get("tool_calls", [])
        except json.JSONDecodeError:
            # Try to extract just the array part
            try:
                # Find array pattern
                array_match = re.search(r'\[\s*\{[^]]+\}\s*\]', response, re.DOTALL)
                if array_match:
                    return json.loads(array_match.group(0))
            except:
                pass
            
            print(f"[!] Failed to parse LLM response")
            return []


# Singleton
_llm: Optional[LLMToolSelector] = None

def get_llm_tool_selector() -> LLMToolSelector:
    global _llm
    if _llm is None:
        _llm = LLMToolSelector()
    return _llm
