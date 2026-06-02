from typing import Dict, Any
import time
from .base_executor import BaseExecutor
from ..mcp.capabilities import ExecutionResult
from ..core.llm import LLMService
from ..core.logger import get_logger

logger = get_logger("LLMExecutor")

class LLMExecutor(BaseExecutor):
    """
    Executor for LLM-based capabilities.
    Enables multi-step plans to use LLM for summarization, generation, etc.
    """
    
    def __init__(self):
        self.llm = LLMService()
        logger.info("LLMExecutor initialized")
    
    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        """
        Execute LLM capabilities:
        - llm.summarize: Summarize provided context
        - llm.generate: Generate text based on prompt
        """
        start_time = time.time()
        
        try:
            if action == "llm.summarize":
                return self._summarize(params, start_time)
            elif action == "llm.generate":
                return self._generate(params, start_time)
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unknown LLM action: {action}",
                    execution_time_ms=0
                )
        except Exception as e:
            logger.error(f"LLM execution error: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _summarize(self, params: Dict[str, Any], start_time: float) -> ExecutionResult:
        """
        Summarize context from a previous step.
        Expected params:
        - context: The text to summarize (resolved by main loop)
        - instruction: Optional custom instruction (default: "summarize this")
        """
        context = params.get("context", "")
        instruction = params.get("instruction", "Bu metni kısaca özetle")
        
        if not context:
            return ExecutionResult(
                success=False,
                error="No context provided for summarization",
                execution_time_ms=0
            )
        
        system_prompt = """Sen bir metni özetleyen asistansın.
Kullanıcının verdiği metni kısa, net ve öz bir şekilde özetle.
Sadece özeti dön, başka açıklama yapma.
JSON formatında dön: {"summary": "özet metni"}"""
        
        user_prompt = f"{instruction}:\n\n{context}"
        
        logger.info(f"Summarizing {len(context)} characters...")
        response = self.llm.generate_response(system_prompt, user_prompt)
        
        if "error" in response:
            return ExecutionResult(
                success=False,
                error=response["error"],
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        summary = response.get("summary", str(response))
        
        return ExecutionResult(
            success=True,
            data=summary,
            execution_time_ms=(time.time() - start_time) * 1000
        )
    
    def _generate(self, params: Dict[str, Any], start_time: float) -> ExecutionResult:
        """
        Generate text based on prompt.
        Expected params:
        - prompt: The generation prompt
        """
        prompt = params.get("prompt", "")
        
        if not prompt:
            return ExecutionResult(
                success=False,
                error="No prompt provided for generation",
                execution_time_ms=0
            )
        
        system_prompt = """Sen yardımcı bir asistansın.
Kullanıcının isteğine göre metin üret.
JSON formatında dön: {"text": "üretilen metin"}"""
        
        logger.info(f"Generating text for prompt: {prompt[:50]}...")
        response = self.llm.generate_response(system_prompt, prompt)
        
        if "error" in response:
            return ExecutionResult(
                success=False,
                error=response["error"],
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        text = response.get("text", str(response))
        
        return ExecutionResult(
            success=True,
            data=text,
            execution_time_ms=(time.time() - start_time) * 1000
        )
