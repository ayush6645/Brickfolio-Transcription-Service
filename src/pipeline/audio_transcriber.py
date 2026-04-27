"""
Stage 04: Multimodal Transcription

This stage leverages Gemini 2.5 Pro's native multimodal capabilities to 
directly 'hear' and transcribe the audio files. 

Benefits of Gemini-Native Transcription:
1. Native Diarization: Automatically identifies Speaker A and Speaker B.
2. Contextual Accuracy: Better at identifying real-estate specific terms and 
   locations within the audio stream.
3. Roman Script Preservation: Transcribes Hindi/Marathi phonetically into 
   English letters, making it cost-effective for LLM analysis.

Process:
1. Upload standardized audio fragment to Gemini File API.
2. Poll for processing completion.
3. Execute generation with transcription-specific prompts.
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from google import genai
from google.genai import types

# Ensure internal modules are discoverable
sys.path.append(str(Path(__file__).parent.parent))
from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger
from ..infrastructure.utils.gemini_client import resilient_generate

# Stage-specific logger for monitoring transcription quality
logger = get_logger("audio_transcriber")

def transcribe_with_gemini(input_file_path: Path) -> Any:
    """
    Directly uploads audio to Gemini and requests a diarized transcript.

    Args:
        input_file_path: Path to the standardized/cleaned WAV file.

    Returns:
        The full Gemini response object.

    Raises:
        ValueError: If API keys are missing or File API upload fails.
    """
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not defined in the workspace environment.")
        
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    logger.info(f"Uploading '{input_file_path.name}' to Gemini File System...")
    
    # Upload to Gemini's ephemeral file storage
    uploaded_file = client.files.upload(path=str(input_file_path))
    
    # Multimodal files require a 'PROCESSING' wait period before they can be used in prompts
    while uploaded_file.state == 'PROCESSING':
        logger.debug("Gemini is still indexing audio content...")
        time.sleep(5)
        uploaded_file = client.files.get(name=uploaded_file.name)
        
    if uploaded_file.state == 'FAILED':
        raise RuntimeError(f"Gemini File Engine failed to process audio: {uploaded_file.error.message}")
        
    logger.info(f"Gemini Audio indexing complete. Size: {uploaded_file.size_bytes} bytes.")

    # Execute structured transcription
    # We use a strict system prompt defined in config to ensure Roman script and JSON format.
    response = resilient_generate(
        client=client,
        model=config.AUDIT_TRANSCRIPTION_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=config.STRUCTURED_TRANSCRIPTION_PROMPT),
                    types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
                ]
            )
        ],
        config_params=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )
    
    # Optionally delete the file from Gemini to save project quota
    try:
        client.files.delete(name=uploaded_file.name)
    except Exception:
        pass # Not critical if deletion fails
        
    return response

def transcribe_full_audio(input_clean_file_path: Path, output_dir: Path) -> Path:
    """
    Primary orchestrator for the transcription stage.
    Handles AI communication and local artifact persistence.

    Args:
        input_clean_file_path: Path to the studio-restored audio.
        output_dir: Directory to save the transcript artifacts.

    Returns:
        Path: Path to the generated JSON transcript.
    """
    input_clean_file_path = Path(input_clean_file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        response = transcribe_with_gemini(input_clean_file_path)
        
        # Parse result with robust multi-tier fallback for raw/JSON text
        raw_text = response.text
        result_data = {}
        try:
            # Tier 1: Strict JSON parsing
            result_data = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("Gemini returned non-standard JSON. Attempting text recovery.")
            # Fallback: Treat as raw transcript if it's not JSON
            result_data = {"transcript": raw_text}

        # Standardization: Ensure we have a string field for the full text
        # 'turns' is the modern structured format, 'transcript' is the legacy/fallback.
        
        # If the model returned a list directly, wrap it in a dict
        if isinstance(result_data, list):
            result_data = {"turns": result_data}
            
        full_text = ""
        if isinstance(result_data, dict) and "turns" in result_data and isinstance(result_data["turns"], list):
            for turn in result_data["turns"]:
                speaker = turn.get("speaker", "Unknown")
                text = turn.get("text", "")
                full_text += f"{speaker}: {text}\n"
        else:
            # Safely handle dict or string fallback
            full_text = result_data.get("transcript", result_data.get("text", raw_text)) if isinstance(result_data, dict) else str(result_data)
        
        output_json_path = output_dir / f"{input_clean_file_path.stem}_transcript.json"
        
        # Prepare the pipeline-compatible intelligence artifact
        final_output = {
            "source": f"Gemini Multimodal ({config.AUDIT_TRANSCRIPTION_MODEL})",
            "full_text": full_text.strip(),
            "structured_turns": result_data.get("turns", []),
            "segment_summary": result_data.get("segment_summary", ""),
            "metadata": {
                "model": config.AUDIT_TRANSCRIPTION_MODEL,
                "timestamp": time.time()
            }
        }
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
            
        # Export a human-readable text version for quick manual auditing
        output_txt_path = output_dir / f"{input_clean_file_path.stem}_transcript.txt"
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text.strip())
            
        logger.info(f"Transcription Complete: artifacts saved to '{output_dir.name}'.")
        return output_json_path
        
    except Exception as e:
        logger.error(f"Critical failure in Transcription Stage: {e}")
        raise
