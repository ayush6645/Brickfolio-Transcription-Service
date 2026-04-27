"""
Adaptive preprocessing for speech restoration.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa

from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger

logger = get_logger("audio_preprocessor")


@dataclass(frozen=True)
class PreprocessResult:
    output_path: Path
    restoration_profile: str
    snr_db: float | None
    clipping_rate: float | None
    speech_ratio: float | None
    speech_preserved: bool
    clarity_preserved: bool
    used_cached_artifact: bool = False

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "restoration_profile": self.restoration_profile,
            "snr_db": self.snr_db,
            "clipping_rate": self.clipping_rate,
            "speech_ratio": self.speech_ratio,
            "speech_preserved": self.speech_preserved,
            "clarity_preserved": self.clarity_preserved,
            "used_cached_artifact": self.used_cached_artifact,
        }


def preprocess_full_file(input_wav_path: Path, output_dir: Path) -> PreprocessResult:
    input_wav_path = Path(input_wav_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_output = output_dir / f"{input_wav_path.stem}_cleaned.wav"

    if not config.ENABLE_SPEECH_RESTORATION:
        logger.info("Speech restoration disabled; standardized audio will be used directly.")
        return PreprocessResult(
            output_path=input_wav_path,
            restoration_profile="disabled",
            snr_db=None,
            clipping_rate=None,
            speech_ratio=None,
            speech_preserved=True,
            clarity_preserved=True,
        )

    if cleaned_output.exists():
        logger.info(f"Skipping preprocessing for '{input_wav_path.name}' because a cleaned artifact already exists.")
        return PreprocessResult(
            output_path=cleaned_output,
            restoration_profile="cached",
            snr_db=None,
            clipping_rate=None,
            speech_ratio=None,
            speech_preserved=True,
            clarity_preserved=True,
            used_cached_artifact=True,
        )

    logger.info(f"Analyzing audio profile for speech restoration: '{input_wav_path.name}'")
    from ..infrastructure.utils.restoration_engine import analyze_audio_metrics, restore_speech

    raw_audio, sr = librosa.load(str(input_wav_path), sr=config.TARGET_SAMPLE_RATE, mono=True)
    snr_db, clipping_rate, speech_ratio = analyze_audio_metrics(raw_audio, sr)
    logger.info(
        "Signal analysis for %s: SNR %.2fdB | clipping %.4f | voice %.2f",
        input_wav_path.name,
        snr_db,
        clipping_rate,
        speech_ratio,
    )

    if config.ENABLE_ADAPTIVE_CLEANING:
        if snr_db > config.SNR_BYPASS_THRESHOLD and clipping_rate < config.MAX_CLIPPING_RATE:
            profile = "BYPASS"
        elif snr_db >= config.SNR_SAFE_THRESHOLD:
            profile = "SAFE"
        else:
            profile = "STRONG"
    else:
        profile = "STRONG"

    logger.info(f"Adaptive profile selection for '{input_wav_path.name}': {profile}")
    output_path, speech_preserved, clarity_preserved = restore_speech(
        input_wav_path,
        cleaned_output,
        profile=profile,
    )

    if profile == "STRONG" and (not speech_preserved or not clarity_preserved):
        logger.warning(
            "STRONG restoration degraded speech for '%s'; retrying with SAFE profile.",
            input_wav_path.name,
        )
        profile = "SAFE"
        output_path, speech_preserved, clarity_preserved = restore_speech(
            input_wav_path,
            cleaned_output,
            profile=profile,
        )

    if profile == "SAFE" and (not speech_preserved or not clarity_preserved):
        logger.warning(
            "SAFE restoration still degraded speech for '%s'; falling back to BYPASS.",
            input_wav_path.name,
        )
        profile = "BYPASS"
        output_path, speech_preserved, clarity_preserved = restore_speech(
            input_wav_path,
            cleaned_output,
            profile=profile,
        )

    logger.info(f"Speech restoration complete for '{output_path.name}' using profile {profile}.")
    return PreprocessResult(
        output_path=output_path,
        restoration_profile=profile,
        snr_db=snr_db,
        clipping_rate=clipping_rate,
        speech_ratio=speech_ratio,
        speech_preserved=speech_preserved,
        clarity_preserved=clarity_preserved,
    )
