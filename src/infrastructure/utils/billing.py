"""
Gemini API Cost and Usage Tracker

This module provides a reliable way to monitor API consumption and estimated 
costs in USD. It handles multi-process concurrency by writing individual 
usage fragments to separate JSONL files, which are later aggregated for report_generator.

Pricing is based on Gemini 2.5 Pro and Flash token rates, including multimodal
audio duration charges.
"""

import os
import json
import threading
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path to ensure config is importable
# sys.path.append removed
from ..config import settings as config

class BillingTracker:
    """
    Manages API usage tracking and cost auditing.
    Uses process-specific fragments to avoid write contention in parallel runs.
    """
    
    # Official Gemini Pricing (USD) as of last audit
    PRICING = {
        "gemini-2.5-pro": {
            "input_1m": 1.25,     # Per 1 million input tokens
            "output_1m": 5.00,    # Per 1 million output tokens
            "audio_min": 0.125    # Per minute of audio processed
        },
        "gemini-2.5-flash": {
            "input_1m": 0.075,
            "output_1m": 0.30,
            "audio_min": 0.0125
        }
    }

    def __init__(self):
        """Initializes the tracker and creates process-specific usage files."""
        self._lock = threading.Lock()
        self.billing_dir = config.METADATA_DIR / "billing"
        self.billing_dir.mkdir(parents=True, exist_ok=True)
        # Use PID to differentiate logs between parallel workers
        self.process_file = self.billing_dir / f"usage_{os.getpid()}.jsonl"

    def add_usage(self, model: str, prompt_tokens: int, candidate_tokens: int, audio_duration_sec: float = 0, context_tag: str = ""):
        """
        Records a single API interaction and its estimated cost.

        Args:
            model: Name of the Gemini model used.
            prompt_tokens: Count of tokens sent in the prompt.
            candidate_tokens: Count of tokens received in the response.
            audio_duration_sec: Length of audio processed in seconds.
            context_tag: A descriptive label for the call (e.g. 'transcription').
        """
        model_key = model.lower()
        base_model = "gemini-2.5-pro" if "pro" in model_key else "gemini-2.5-flash"
        rates = self.PRICING.get(base_model, self.PRICING["gemini-2.5-flash"])
        
        # Calculate Costs based on 1M token benchmarks
        input_cost = (prompt_tokens / 1_000_000.0) * rates["input_1m"]
        output_cost = (candidate_tokens / 1_000_000.0) * rates["output_1m"]
        # Audio is billed per minute
        audio_cost = (audio_duration_sec / 60.0) * rates["audio_min"]
        
        total_call_cost = input_cost + output_cost + audio_cost
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "context": context_tag,
            "tokens_in": prompt_tokens,
            "tokens_out": candidate_tokens,
            "audio_sec": audio_duration_sec,
            "cost_usd": round(total_call_cost, 6)
        }
        
        # Thread-safe write to our process-specific log
        with self._lock:
            try:
                with open(self.process_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                # Log to stderr if disk write fails to avoid interrupting the pipeline
                print(f"BILLING ERROR: Could not write fragment to {self.process_file}: {e}", file=sys.stderr)

    def aggregate_and_report(self, output_path: Path) -> Dict[str, Any]:
        """
        Aggregates all process-level fragments into a single master audit report.
        This should be called once by the main orchestrator after all workers finish.

        Args:
            output_path: Destination for the aggregated JSON report.

        Returns:
            Dict: Summary statistics including total cost.
        """
        all_items = []
        total_cost = 0.0
        
        # Scan for all active fragments in the billing directory
        for p_file in self.billing_dir.glob("usage_*.jsonl"):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            item = json.loads(line)
                            all_items.append(item)
                            total_cost += item.get("cost_usd", 0)
            except Exception as e:
                print(f"Failed to read billing fragment {p_file}: {e}", file=sys.stderr)

        summary = {
            "report_generated": datetime.now().isoformat(),
            "total_cost_usd": round(total_cost, 4),
            "total_calls_monitored": len(all_items),
            "usage_details": all_items
        }

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            print(f"CRITICAL: Failed to save final billing report: {e}", file=sys.stderr)
            
        return summary

# Global singleton for easy import across pipeline stages
billing_tracker = BillingTracker()
