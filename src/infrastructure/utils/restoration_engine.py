import os
import librosa
import numpy as np
import soundfile as sf
import noisereduce as nr
import torch
from pathlib import Path
from pedalboard import Pedalboard, NoiseGate, Compressor, Gain, HighpassFilter, LowpassFilter, PeakFilter, HighShelfFilter
import sys
import gc

# Add parent dir to path so we can from ..config import settings as config
# sys.path.append removed
from ..config import settings as config

# Global model cache (SpeechBrain)
_ENHANCER_MODEL = None

def get_enhancer_model():
    """
    Lazy loader for SpeechBrain MetricGAN+ model.
    Optimized for speech intelligibility and clarity.
    """
    global _ENHANCER_MODEL
    if _ENHANCER_MODEL is None:
        try:
            from speechbrain.inference.enhancement import SpectralMaskEnhancement
            # Model trained on Voicebank-Demand dataset for robust denoising
            _ENHANCER_MODEL = SpectralMaskEnhancement.from_hparams(
                source="speechbrain/metricgan-plus-voicebank",
                savedir="pretrained_models/metricgan-plus",
                run_opts={"device":"cpu"}
            )
        except Exception as e:
            print(f"Error loading SpeechBrain model: {e}")
            return None
    return _ENHANCER_MODEL

def analyze_audio_metrics(audio: np.ndarray, sr: int):
    """
    Returns estimated SNR, clipping rate, and speech ratio.
    """
    if len(audio) == 0:
        return 0.0, 0.0, 0.0

    # Clipping rate
    clipping_threshold = 0.99
    clipping_rate = np.mean(np.abs(audio) >= clipping_threshold)

    # 1. Separate "Speech" (active) from "Silence" (gated background)
    intervals = librosa.effects.split(audio, top_db=35)
    
    # Calculate speech ratio
    active_samples = sum(end - start for start, end in intervals)
    speech_ratio = active_samples / len(audio) if len(audio) > 0 else 0.0
    
    if len(intervals) == 0:
        return 0.0, clipping_rate, speech_ratio
        
    # Concatenate only the active audio for noise analysis
    active_segments = [audio[start:end] for start, end in intervals]
    active_audio = np.concatenate(active_segments)
    
    # Estimate SNR on active parts using RMS percentiles
    rms = librosa.feature.rms(y=active_audio, frame_length=2048, hop_length=512)[0]
    if len(rms) == 0:
        return 0.0, clipping_rate, speech_ratio
        
    signal_rms = np.percentile(rms, 95)
    noise_rms = np.percentile(rms, 10)  # Noise floor within active segments

    if noise_rms == 0:
        snr_db = 50.0 
    else:
        snr = signal_rms / noise_rms
        snr_db = 20 * np.log10(snr) if snr > 0 else 0.0

    return snr_db, clipping_rate, speech_ratio

def speech_preservation_check(original: np.ndarray, cleaned: np.ndarray) -> bool:
    """
    Compares energy in active voice regions to see if speech was truncated.
    Returns True if speech was preserved, False if heavily gated.
    """
    if len(original) == 0 or len(cleaned) == 0:
        return True

    min_length = min(len(original), len(cleaned))
    orig = original[:min_length]
    clnd = cleaned[:min_length]

    rms_orig = librosa.feature.rms(y=orig, frame_length=2048, hop_length=512)[0]
    threshold = np.percentile(rms_orig, 75)
    active_frames = rms_orig > threshold

    if not np.any(active_frames):
        return True # Nothing to preserve

    rms_clean = librosa.feature.rms(y=clnd, frame_length=2048, hop_length=512)[0]
    
    orig_energy = 20 * np.log10(np.mean(rms_orig[active_frames]) + 1e-9)
    clean_energy = 20 * np.log10(np.mean(rms_clean[active_frames]) + 1e-9)

    drop = orig_energy - clean_energy
    if drop > abs(config.SPEECH_DROP_THRESHOLD_DB):
        return False
        
    return True


def _band_energy_db(audio: np.ndarray, sr: int, low_hz: float = 1800.0, high_hz: float = 6200.0) -> float:
    """
    Returns average band energy in dB for a speech-critical high-frequency band.
    """
    if len(audio) == 0:
        return -120.0
    stft = np.abs(librosa.stft(audio, n_fft=1024, hop_length=256))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return -120.0
    band = stft[mask, :]
    return 20 * np.log10(np.mean(band) + 1e-9)


def clarity_preservation_check(original: np.ndarray, cleaned: np.ndarray, sr: int) -> bool:
    """
    Ensures we do not over-smooth consonants by dropping too much HF speech detail.
    """
    if len(original) == 0 or len(cleaned) == 0:
        return True

    min_length = min(len(original), len(cleaned))
    orig = original[:min_length]
    clnd = cleaned[:min_length]

    orig_hf = _band_energy_db(orig, sr)
    clean_hf = _band_energy_db(clnd, sr)
    hf_drop_db = orig_hf - clean_hf

    return hf_drop_db <= config.CLARITY_DROP_THRESHOLD_DB

def ai_deep_denoise(audio: np.ndarray, sr: int, chunk_sec: int = 30):
    """
    Applies SpeechBrain MetricGAN+ enhancement in chunks for memory safety.
    Focuses on natural speech tone and higher intelligibility.
    """
    model = get_enhancer_model()
    if model is None:
        return audio, sr # Fallback to original if model fails to load
    
    # 1. Standardize input for model (Expects 16kHz mono)
    target_sr = 16000
    if sr != target_sr:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    
    wav = torch.from_numpy(audio).float()
    if wav.ndim == 1:
        wav = wav.unsqueeze(0)
    
    # 2. Chunking Logic
    chunk_size = chunk_sec * sr
    overlap = int(2 * sr) 
    total_samples = wav.shape[1]
    
    output_chunks = []
    
    # Process chunks with overlap
    for i in range(0, total_samples, chunk_size):
        start = i
        end = min(i + chunk_size + overlap, total_samples)
        
        chunk = wav[:, start:end]
        
        if chunk.shape[1] < 1000:
            continue
            
        with torch.no_grad():
            # SpeechBrain takes [batch, time]
            enhanced = model.enhance_batch(chunk, lengths=torch.tensor([1.0]))
            
        # Convert to numpy
        chunk_np = enhanced.cpu().numpy().flatten()
        
        if len(output_chunks) > 0:
            prev_chunk = output_chunks[-1]
            fade_len = min(overlap, len(prev_chunk), len(chunk_np))
            if fade_len > 0:
                fade_out = np.linspace(1.0, 0.0, fade_len)
                fade_in = np.linspace(0.0, 1.0, fade_len)
                prev_chunk[-fade_len:] = prev_chunk[-fade_len:] * fade_out + chunk_np[:fade_len] * fade_in
            output_chunks.append(chunk_np[fade_len:])
        else:
            output_chunks.append(chunk_np)
            
    final_audio = np.concatenate(output_chunks)
    return final_audio, sr

def restore_speech(input_path: Path, output_path: Path, profile: str = "STRONG") -> tuple[Path, bool, bool]:
    """
    Enhanced speech restoration using dynamic profiles.
    Returns (output_path, is_speech_preserved: bool, is_clarity_preserved: bool)
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load Audio
    raw_audio, sr = librosa.load(input_path, sr=config.TARGET_SAMPLE_RATE, mono=True)
    
    if profile == "BYPASS":
        # Only Normalize
        peak = np.max(np.abs(raw_audio))
        if peak > 0:
            final_audio = raw_audio * (0.92 / peak)
        else:
            final_audio = raw_audio
        sf.write(output_path, final_audio, sr)
        return output_path, True, True

    if profile in ["STRONG", "SAFE"]:
        # 2. AI-Driven High-Fidelity Enhancement or Safe fallback
        if profile == "STRONG":
            refined_audio, sr = ai_deep_denoise(raw_audio, sr)
        else:
            # For SAFE mode, use traditional noisereduce which is less likely to clip words.
            refined_audio = nr.reduce_noise(
                y=raw_audio,
                sr=sr,
                prop_decrease=config.SAFE_NOISE_REDUCTION,
                stationary=False,
            )

        # 3. Studio Chain (Pedalboard)
        pb_list = [HighpassFilter(cutoff_frequency_hz=config.HPF_CUTOFF)]

        # Keep LPF only for STRONG mode to avoid blurring clearer calls.
        if profile == "STRONG":
            pb_list.append(LowpassFilter(cutoff_frequency_hz=config.LPF_CUTOFF))

        pb_list.append(HighShelfFilter(cutoff_frequency_hz=3000, gain_db=2.0 if profile == "SAFE" else 3.0))
        
        if profile == "STRONG":
            pb_list.extend([
                NoiseGate(threshold_db=config.GATE_THRESHOLD, ratio=1.25, attack_ms=25.0, release_ms=500.0)
            ])
            
        pb_list.extend([
            PeakFilter(cutoff_frequency_hz=2500, gain_db=2.0, q=0.5), # Vocal presence
            Compressor(
                threshold_db=-24.0,
                ratio=config.STRONG_COMPRESSOR_RATIO if profile == "STRONG" else config.SAFE_COMPRESSOR_RATIO,
                attack_ms=12.0,
                release_ms=220.0,
            ),
            Gain(gain_db=config.STRONG_GAIN_DB if profile == "STRONG" else config.SAFE_GAIN_DB)
        ])

        board = Pedalboard(pb_list)
        effected = board(refined_audio.reshape(1, -1), sr)
        final_audio = effected.flatten()

        # 4. Final Normalization
        peak = np.max(np.abs(final_audio))
        if peak > 0:
            final_audio = final_audio * (0.92 / peak)

        # 5. Speech Preservation Check 
        is_preserved = speech_preservation_check(raw_audio, final_audio)
        is_clarity_preserved = clarity_preservation_check(raw_audio, final_audio, sr)

        # Export
        sf.write(output_path, final_audio, sr)
        
        # Explicitly free memory
        del raw_audio
        del refined_audio
        del final_audio
        gc.collect()
        
        return output_path, is_preserved, is_clarity_preserved

    # Defensive fallback for unknown profile values.
    sf.write(output_path, raw_audio, sr)
    return output_path, True, True
