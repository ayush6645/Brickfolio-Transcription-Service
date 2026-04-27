
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
import os
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.infrastructure.config import settings as config

def export_logs(output_name: str = None) -> Path:
    """
    Bundles all relevant logs and metadata into a single ZIP file for export.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = output_name or f"brickfolio_logs_{timestamp}.zip"
    
    export_dir = config.BASE_DIR / "exports"
    export_dir.mkdir(exist_ok=True)
    
    zip_path = export_dir / output_name
    
    log_files_to_include = [
        (config.LOGS_DIR, "logs"),
        (config.METADATA_DIR, "metadata"),
    ]
    
    print(f"Starting log export to {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for source_dir, arc_name in log_files_to_include:
            if not source_dir.exists():
                continue
                
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    # Skip massive temporary files if any
                    if file_path.suffix in ['.wav', '.mp3', '.tmp']:
                        continue
                        
                    # Calculate arc path
                    rel_path = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname=Path(arc_name) / rel_path)
    
    print(f"Export successful: {zip_path}")
    return zip_path

if __name__ == "__main__":
    export_logs()
