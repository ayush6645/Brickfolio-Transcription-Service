from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid
import json
import os
import sys

# Ensure the src directory is in the path for internal imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline import (
    audio_standardizer as standardize,
    audio_preprocessor as preprocess,
    audio_transcriber as transcribe
)
from src.infrastructure.config import settings as config
from src.infrastructure.utils.logger import get_logger

logger = get_logger("transcription_api")
app = FastAPI(title="Brickfolio Transcription Service")

# Create temporary directories if they don't exist
TEMP_DIR = Path("temp_processing")
TEMP_DIR.mkdir(exist_ok=True)

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Standardize, Preprocess and Transcribe an audio file.
    """
    session_id = str(uuid.uuid4())
    raw_path = TEMP_DIR / f"{session_id}_{file.filename}"
    std_path = TEMP_DIR / f"{session_id}_std.wav"
    cleaned_dir = TEMP_DIR / f"{session_id}_cleaned"
    cleaned_dir.mkdir(exist_ok=True)

    try:
        # 1. Save uploaded file
        with raw_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Processing transcription request for {file.filename} [Session: {session_id}]")

        # 2. Standardize
        await asyncio.to_thread(standardize.standardize_audio, raw_path, std_path)

        # 3. Preprocess
        await asyncio.to_thread(preprocess.preprocess_full_file, std_path, cleaned_dir)
        cleaned_wav = cleaned_dir / f"{std_path.stem}_cleaned.wav"

        # 4. Transcribe
        output_dir = TEMP_DIR / f"{session_id}_output"
        trans_json_path = await asyncio.to_thread(transcribe.transcribe_full_audio, cleaned_wav, output_dir)

        # 5. Load and return result
        with open(trans_json_path, 'r', encoding='utf-8') as f:
            result = json.load(f)

        return result

    except Exception as e:
        logger.error(f"Transcription failed for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup (optional, maybe keep for debugging if needed, but usually good to clean)
        # shutil.rmtree(cleaned_dir, ignore_errors=True)
        # if raw_path.exists(): raw_path.unlink()
        # if std_path.exists(): std_path.unlink()
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
