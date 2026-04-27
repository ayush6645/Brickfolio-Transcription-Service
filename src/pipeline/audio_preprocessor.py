"""
Stage 03: Audio Preprocessing (Speech Restoration)

This stage applies Brickfolio's 'Studio-Grade' restorative audio processing 
to standardized recordings. The goal is to aggressively isolate human speech 
from background field noise (traffic, wind, call-center static) without 
introducing digital artifacts.

Features:
- Adaptive Cleaning: Automatically selects a noise-reduction profile (BYPASS, 
  SAFE, or STRONG) based on Real-Time Signal-to-Noise Ratio (SNR) analysis.
- Multi-Pass Restoration: If the aggressive filter causes speech degradation, 
  the stage automatically falls back to safer profiles.
- Spectral Re-masking: Reconstructs high-frequency speech components lost 
  during noise subtraction.

Dependencies:
- librosa: For spectral and SNR analysis.
- utils.restoration_engine: Core DSP implementation.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import librosa

# Ensure internal modules are discoverable for imports
sys.path.append(str(Path(__file__).parent.parent))
from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger
from ..infrastructure.utils.restoration_engine import restore_speech, analyze_audio_metrics

# Stage-specific logger for monitoring restoration quality
logger = get_logger("audio_preprocessor")

def preprocess_full_file(input_wav_path: Path, output_dir: Path) -> Path:
    """
    Analyzes and restores human speech in a standardized WAV file.

    Args:
        input_wav_path: Path to the standardized source recording.
        output_dir: Destination for the 'Studio-Clean' WAV file.

    Returns:
        Path: The file path to the cleaned audio artifact.

    Raises:
        RuntimeError: If DSP processing fails or audio metrics cannot be extracted.
    """
    input_wav_path = Path(input_wav_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cleaned_output = output_dir / f"{input_wav_path.stem}_cleaned.wav"
    
    # 1. Idempotency Check: Don't re-clean if already done. 
    # This saves significant CPU time in large batches.
    if cleaned_output.exists():
        logger.info(f"Skipping preprocessing: Studio-Clean file already exists for '{input_wav_path.name}'.")
        return cleaned_output

    try:
        logger.info(f"Analyzing audio profile for Speech Restoration: '{input_wav_path.name}'")
        
        if config.ENABLE_ADAPTIVE_CLEANING:
            # Load file to analyze signal quality
            raw_audio, sr = librosa.load(str(input_wav_path), sr=config.TARGET_SAMPLE_RATE, mono=True)
            snr_db, clipping_rate, speech_ratio = analyze_audio_metrics(raw_audio, sr)
            
            logger.info(f"Signal Analysis: SNR: {snr_db:.2f}dB | Clipping: {clipping_rate:.4f} | Voice: {speech_ratio:.2f}")

            # Profile Selection Logic:
            # - BYPASS: For already clean studio-grade recordings.
            # - SAFE: For moderate office/home noise.
            # - STRONG: For high-noise field calls (Road, Construction, Crowds).
            if snr_db > config.SNR_BYPASS_THRESHOLD and clipping_rate < config.MAX_CLIPPING_RATE:
                profile = "BYPASS"
            elif snr_db >= config.SNR_SAFE_THRESHOLD:
                profile = "SAFE"
            else:
                profile = "STRONG"
                
            logger.info(f"Adaptive Profile Selection: {profile}")
            
            # First Attempt: Apply selected profile
            output_file, is_preserved, is_clear = restore_speech(input_wav_path, cleaned_output, profile=profile)
            
            # Quality Assurance Fallback Loop
            # If the filter is too aggressive and cuts into speech (loss of continuity), 
            # we retry with a gentler profile.
            if profile == "STRONG" and (not is_preserved or not is_clear):
                logger.warning(f"Restoration Quality Alert: STRONG profile degraded speech in '{input_wav_path.name}'. Recalibrating to SAFE.")
                output_file, is_preserved, is_clear = restore_speech(input_wav_path, cleaned_output, profile="SAFE")

            if profile == "SAFE" and (not is_preserved or not is_clear):
                logger.warning(f"Final Quality Warning: SAFE profile still degrading speech in '{input_wav_path.name}'. Falling back to original signal (BYPASS).")
                output_file, _, _ = restore_speech(input_wav_path, cleaned_output, profile="BYPASS")
        else:
            # Forced cleaning if adaptive mode is disabled (useful for extremely noisy sets)
            logger.info(f"Adaptive mode OFF. Applying STATIC-STRONG profile to '{input_wav_path.name}'.")
            output_file, _, _ = restore_speech(input_wav_path, cleaned_output, profile="STRONG")
        
        logger.info(f"Studio Speech Restoration complete for '{cleaned_output.name}'.")
        return cleaned_output
        
    except Exception as e:
        logger.error(f"Critical DSP Failure during restoration of {input_wav_path.name}: {e}")
        raise
