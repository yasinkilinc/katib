# -*- coding: utf-8 -*-
import time
import sys
import os
import argparse
import warnings
from typing import List, Dict

# Suppress warnings
warnings.filterwarnings("ignore", module="torchaudio")
warnings.filterwarnings("ignore", message=".*TorchCodec.*")
warnings.filterwarnings("ignore", category=UserWarning)

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports from new architecture
from src.core.planner import Planner
from src.core.memory import MemoryEngine
from src.core.policy import PolicyEngine
from src.core.logger import get_logger
from src.config import Config
from src.perception.audio import AudioListener
from src.perception.transcribe import Transcriber
from src.perception.speaker import SpeakerVerifier
from src.mcp.resolver import get_resolver
from src.mcp.capabilities import CapabilityRequest, Origin
from src.executors.macos_executor import MacOSExecutor
from src.executors.terminal_executor import TerminalExecutor
from src.executors.windsurf_executor import WindsurfExecutor
from src.executors.interpreter_executor import InterpreterExecutor
from src.executors.system_executor import SystemExecutor
from src.executors.llm_executor import LLMExecutor

logger = get_logger("Main")

class KatibSystem:
    def __init__(self):
        logger.info("\n🚀 Katib v2 (Controlled Autonomous) başlatılıyor...")
        
        # 1. Initialize Core
        self.memory_engine = MemoryEngine()
        self.planner = Planner(memory_engine=self.memory_engine)
        self.policy_engine = PolicyEngine()
        
        # 2. Initialize Perception
        self.audio_listener = AudioListener()
        self.transcriber = Transcriber()
        self.verifier = SpeakerVerifier()
        
        # 3. Initialize MCP & Executors
        # Resolver is a singleton that holds Policy + Registry
        self.resolver = get_resolver()
        # Inject Policy Engine into Resolver (if not already handled by logging)
        self.resolver.policy = self.policy_engine 
        
        # Register Executors
        self.resolver.register_executor("macos_executor", MacOSExecutor())
        self.resolver.register_executor("terminal_executor", TerminalExecutor())
        self.resolver.register_executor("windsurf_executor", WindsurfExecutor())
        self.resolver.register_executor("interpreter_executor", InterpreterExecutor())
        self.resolver.register_executor("system_executor", SystemExecutor())
        self.resolver.register_executor("llm_executor", LLMExecutor())
        
        logger.info("[✓] Sistem Hazır. Komut bekleniyor... (Çıkış için Ctrl+C)")

    def start_loop(self):
        audio_file = "input.wav"
        
        try:
            while True:
                # --- PHASE 1: SENSE ---
                try:
                    has_audio = self.audio_listener.listen_and_record(audio_file)
                except Exception as e:
                    logger.error(f"[!] Audio hatası: {e}")
                    has_audio = False
                
                if not has_audio:
                    continue
                    
                print("[*] Kimlik doğrulanıyor...", end='\r') 
                if not self.verifier.verify(audio_file):
                    logger.warning("\n[!] Ses reddedildi: Kimlik doğrulanamadı.")
                    continue
                logger.info("[✓] Kimlik doğrulandı.")
                
                command_text = self.transcriber.transcribe(audio_file)
                if not command_text:
                    continue
                    
                # --- PHASE 2: PLAN (Integrated Reasoning) ---
                print("[...] Planlanıyor (Reasoning)...", end='\r')
                
                try:
                    plan = self.planner.generate_plan(command_text)
                    steps = plan.steps
                except Exception as e:
                    logger.error(f"[!] Planlama hatası: {e}")
                    continue
                
                if not steps:
                     logger.warning(f"[!] Plan oluşturulamadı: {getattr(plan, 'reasoning', 'Sebep yok')}")
                     continue

                # --- PHASE 3: AUDIT & ACT ---
                if self._execute_plan(steps, command_text, plan):
                    logger.info("[!] Katib kapatılıyor...")
                    break
                
        except KeyboardInterrupt:
            logger.info("\n[!] Kapatılıyor...")
        except Exception as e:
            logger.critical(f"\n[!] Kritik Hata: {e}")

    def _execute_plan(self, steps: List, command_text, plan):
        logger.info(f"[i] Plan ({len(steps)} adım): {plan.reasoning}")
        
        executed_actions = []
        all_success = True
        step_outputs = {}  # Store outputs: {step_id: result.data}
        
        for step in steps:
            # step is now a Step object
            # New Step Schema: id, name, capability, params, requires_feedback
            action_name = step.capability
            params = step.params.copy()  # Copy to avoid mutating original
            
            # --- CONTEXT RESOLUTION ---
            # If params contains 'context_from_step', resolve it
            if "context_from_step" in params:
                context_step_id = params["context_from_step"]
                if context_step_id in step_outputs:
                    params["context"] = str(step_outputs[context_step_id])
                    logger.info(f"  [→] Resolved context from step {context_step_id}")
                else:
                    logger.warning(f"  [!] Step {context_step_id} output not found, using empty context")
                    params["context"] = ""
                # Remove the reference key
                del params["context_from_step"]
            
            logger.info(f"  • {action_name} -> {params}")
            
            # Create MCP Request
            request = CapabilityRequest(
                name=action_name,
                parameters=params,
                origin=Origin.VOICE
            )

            # Create Serializable Request Dict for logging
            req_dict = request.__dict__.copy()
            if "origin" in req_dict and hasattr(req_dict["origin"], "value"):
                req_dict["origin"] = req_dict["origin"].value

            # Resolve & Execute (Policy check inside)
            result = self.resolver.resolve_and_execute(request)
            
            # Store step output for future reference
            step_outputs[step.id] = result.data
            
            executed_actions.append({
                "request": req_dict, 
                "result": result.__dict__
            })
            
            if not result.success:
                logger.error(f"[X] Hata ({action_name}): {result.error}")
                all_success = False
                break
            else:
                 logger.info(f"[✓] Tamamlandı ({result.execution_time_ms:.0f}ms)")
                 if result.data == "STOP_SIGNAL":
                     logger.info("[!] Çıkış sinyali alındı.")
                     return True # Should exit
                 
                 if result.data:
                     logger.info(f"    -> {str(result.data)[:100]}...")
                     
        # --- PHASE 4: LEARN ---
        if all_success:
            logger.info("[✓] Tüm görevler başarıyla tamamlandı.")
        else:
            logger.warning("[!] Görev tamamlanamadı.")
            
        outcome = {
            "command": command_text,
            "pipeline": "planner_only",
            "plan": plan.model_dump(),
            "actions": executed_actions,
            "success": all_success,
            "error": None if all_success else "Execution failed"
        }
        self.memory_engine.record_execution(outcome)
        
        # TTS Feedback
        self._speak_feedback(all_success)
        
        return False # Should not exit
    
    def _speak_feedback(self, success: bool):
        """Provide voice feedback after command execution"""
        if not Config.TTS_FEEDBACK_ENABLED:
            return
            
        import random
        if success:
            messages = ["Tamam", "Bitti", "Yapıldı"]
        else:
            messages = ["Anlamadım", "Bir sorun oldu", "Başarısız"]
        
        message = random.choice(messages)
        try:
            self.macos_executor.execute("tts.speak", {"text": message})
        except Exception as e:
            logger.debug(f"TTS feedback failed: {e}")

if __name__ == "__main__":
    app = KatibSystem()
    app.start_loop()
