
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.infrastructure.config import settings as config

def export_to_excel(output_path: str = None):
    """
    Exports all logs and metadata into a single multi-sheet Excel file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_path or config.BASE_DIR / "exports" / f"brickfolio_full_audit_{timestamp}.xlsx"
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 1. Pipeline State
        if config.PIPELINE_STATE_FILE.exists():
            try:
                state_data = json.loads(config.PIPELINE_STATE_FILE.read_text(encoding="utf-8"))
                rows = []
                for file_id, info in state_data.items():
                    row = {
                        "File ID": file_id,
                        "Filename": info.get("input_filename"),
                        "Status": info.get("status"),
                        "Lead ID": info.get("lead_id"),
                        "Agent ID": info.get("agent_id"),
                        "Duration (s)": info.get("total_audio_duration_sec"),
                        "Updated At": info.get("updated_at"),
                        "Source": info.get("source"),
                    }
                    # Flatten metrics if present
                    metrics = info.get("metrics", {})
                    if metrics:
                        for k, v in metrics.items():
                            row[f"Metric_{k}"] = v
                    rows.append(row)
                df_state = pd.DataFrame(rows)
                df_state.to_excel(writer, sheet_name='Pipeline_Status', index=False)
            except Exception as e:
                print(f"Error processing pipeline state: {e}")

        # 2. Performance Report
        if config.PERFORMANCE_REPORT_FILE.exists():
            try:
                df_perf = pd.read_csv(config.PERFORMANCE_REPORT_FILE)
                df_perf.to_excel(writer, sheet_name='Performance', index=False)
            except Exception as e:
                print(f"Error processing performance report: {e}")

        # 3. Billing / Usage
        usage_files = list(config.BILLING_DIR.glob("usage_*.jsonl"))
        usage_rows = []
        for uf in usage_files:
            try:
                with uf.open('r', encoding='utf-8') as f:
                    for line in f:
                        usage_rows.append(json.loads(line))
            except:
                pass
        if usage_rows:
            df_usage = pd.DataFrame(usage_rows)
            df_usage.to_excel(writer, sheet_name='Usage_Billing', index=False)

        # 4. System Logs (Last 2000 lines)
        log_file = config.LOGS_DIR / "pipeline.log"
        if log_file.exists():
            try:
                lines = log_file.read_text(encoding="utf-8").splitlines()
                # Simple parsing of log lines: [Timestamp] | [Level] | [Component] Message
                log_data = []
                for line in lines[-2000:]:
                    parts = line.split(" | ", 2)
                    if len(parts) == 3:
                        log_data.append({
                            "Timestamp": parts[0],
                            "Level": parts[1],
                            "Content": parts[2]
                        })
                    else:
                        log_data.append({"Timestamp": "", "Level": "", "Content": line})
                df_logs = pd.DataFrame(log_data)
                df_logs.to_excel(writer, sheet_name='System_Logs', index=False)
            except Exception as e:
                print(f"Error processing system logs: {e}")

    print(f"Audit report created: {output_path}")
    return output_path

if __name__ == "__main__":
    export_to_excel()
