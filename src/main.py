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
from src.core.intent import IntentEngine
from src.core.planner import Planner
from src.core.memory import MemoryEngine
from src.core.policy import PolicyEngine
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

class KatibSystem:
    def __init__(self):
        print("\n🚀 Katib v2 (Controlled Autonomous) başlatılıyor...")
        
        # 1. Initialize Core
        self.memory_engine = MemoryEngine()
        self.intent_engine = IntentEngine()
        self.planner = Planner()
        self.policy_engine = PolicyEngine()
        
        # 2. Initialize Perception
        self.audio_listener = AudioListener()
        self.transcriber = Transcriber()
        self.verifier = SpeakerVerifier()
        
        # 3. Initialize MCP & Executors
        # Resolver is a singleton that holds Policy + Registry
        self.resolver = get_resolver()
        # Inject Policy Engine into Resolver (if not already handled by logging)
        # Note: Resolver lazy-loads its own policy engine, or we can force inject if we want shared state
        self.resolver.policy = self.policy_engine 
        
        # Register Executors
        self.resolver.register_executor("macos_executor", MacOSExecutor())
        self.resolver.register_executor("terminal_executor", TerminalExecutor())
        self.resolver.register_executor("windsurf_executor", WindsurfExecutor())
        self.resolver.register_executor("interpreter_executor", InterpreterExecutor())
        self.resolver.register_executor("system_executor", SystemExecutor())
        
        # Warmup
        self.intent_engine.warmup()
        print("[✓] Sistem Hazır. Komut bekleniyor... (Çıkış için Ctrl+C)")

    def start_loop(self):
        audio_file = "input.wav"
        
        try:
            while True:
                # --- PHASE 1: SENSE ---
                try:
                    has_audio = self.audio_listener.listen_and_record(audio_file)
                except Exception as e:
                    print(f"[!] Audio hatası: {e}")
                    has_audio = False
                
                if not has_audio:
                    continue
                    
                print("[*] Kimlik doğrulanıyor...", end='\r')
                if not self.verifier.verify(audio_file):
                    print("\n[!] Ses reddedildi: Kimlik doğrulanamadı.")
                    continue
                print("[✓] Kimlik doğrulandı.")
                
                command_text = self.transcriber.transcribe(audio_file)
                if not command_text:
                    continue
                    
                # --- PHASE 2: PLAN (Merged Intent & Planning) ---
                print("[...] Planlanıyor (Reasoning)...", end='\r')
                
                # Single pass: Correction + Planning
                try:
                    plan_data = self.planner.generate_plan(command_text)
                    steps = plan_data.get("steps", [])
                except Exception as e:
                    print(f"[!] Planlama hatası: {e}")
                    continue
                
                if not steps:
                     print(f"[!] Plan oluşturulamadı.")
                     continue

                # --- PHASE 3: AUDIT & ACT ---
                if self._execute_plan(steps, command_text, None, plan_data):
                    print("[!] Katib kapatılıyor...")
                    break
                
        except KeyboardInterrupt:
            print("\n[!] Kapatılıyor...")
        except Exception as e:
            print(f"\n[!] Kritik Hata: {e}")

    def _execute_plan(self, steps: List[Dict], command_text, intent_data, plan_data):
        print(f"[i] Plan ({len(steps)} adım):")
        
        executed_actions = []
        all_success = True
        
        for step in steps:
            # step structure matches Planner output: {"action": "web.navigate", "parameters": {...}}
            action_name = step.get("action")
            params = step.get("parameters", {})
            
            print(f"  • {action_name} -> {params}")
            
            # Create MCP Request
            request = CapabilityRequest(
                name=action_name,
                parameters=params,
                origin=Origin.VOICE
            )

            # Create Serializable Request Dict
            req_dict = request.__dict__.copy()
            if "origin" in req_dict and hasattr(req_dict["origin"], "value"):
                req_dict["origin"] = req_dict["origin"].value

            # Resolve & Execute (Policy check inside)
            result = self.resolver.resolve_and_execute(request)
            
            executed_actions.append({
                "request": req_dict, 
                "result": result.__dict__
            })
            
            if not result.success:
                print(f"[X] Hata ({action_name}): {result.error}")
                all_success = False
                break
            else:
                 print(f"[✓] Tamamlandı ({result.execution_time_ms:.0f}ms)")
                 if result.data == "STOP_SIGNAL":
                     print("[!] Çıkış sinyali alındı.")
                     return True # Should exit
                 
                 if result.data:
                     print(f"    -> {str(result.data)[:100]}...")
                     
        return False # Should not exit

        # --- PHASE 4: LEARN ---
        if all_success:
            print("[✓] Tüm görevler başarıyla tamamlandı.")
        else:
            print("[!] Görev tamamlanamadı.")
            
        outcome = {
            "command": command_text,
            "intent": None, # Merged into plan
            "plan": plan_data,
            "actions": executed_actions,
            "success": all_success,
            "error": None if all_success else "Execution failed"
        }
        self.memory_engine.record_execution(outcome)

if __name__ == "__main__":
    app = KatibSystem()
    app.start_loop()
