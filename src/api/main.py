import asyncio
import json
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from src.infrastructure.config import settings as config
from src.infrastructure.utils.environment_validator import init_directories
from src.infrastructure.utils.logger import get_logger
from src.pipeline.transcription_runner import TranscriptionRunner

logger = get_logger("transcription_api")
app = FastAPI(title="Brickfolio Transcription Service")

TEMP_DIR = config.TEMP_PROCESSING_DIR
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    lead_id: str | None = None,
    agent_id: str | None = None,
    recording_id: str | None = None,
):
    """
    Run the shared pipeline on an uploaded audio file and return the final artifact.
    """
    init_directories()
    session_id = str(uuid.uuid4())
    raw_path = TEMP_DIR / session_id / file.filename

    try:
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with raw_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Processing API transcription request for {file.filename} [Session: {session_id}]")
        runner = TranscriptionRunner(session_id=session_id)
        result = await asyncio.to_thread(
            runner.run_pipeline,
            raw_path,
            source="api",
            session_id=session_id,
            lead_id=lead_id,
            agent_id=agent_id,
            recording_id=recording_id,
        )
        return json.loads(result.final_json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error(f"Transcription failed for {file.filename}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if raw_path.exists():
            try:
                raw_path.unlink()
            except OSError:
                pass
        if raw_path.parent.exists():
            try:
                raw_path.parent.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
