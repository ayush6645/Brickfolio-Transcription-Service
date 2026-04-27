from pydub import AudioSegment
from pathlib import Path
import math

def split_audio_into_segments(file_path: Path, output_dir: Path, segment_length_sec: int = 900, overlap_sec: int = 30):
    """
    Split a large audio file into segments with overlap.
    Default: 15-minute segments with 30-second overlap.
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    audio = AudioSegment.from_wav(file_path)
    duration_sec = len(audio) / 1000.0
    
    segment_length_ms = segment_length_sec * 1000
    overlap_ms = overlap_sec * 1000
    
    segments_paths = []
    
    start_ms = 0
    seg_idx = 1
    
    while start_ms < len(audio):
        end_ms = start_ms + segment_length_ms
        
        # If this isn't the first segment, include overlap from the start
        # If it's not the last segment, include overlap at the end
        chunk = audio[start_ms:end_ms]
        
        chunk_name = f"{file_path.stem}_part{seg_idx:02d}.wav"
        chunk_path = output_dir / chunk_name
        chunk.export(chunk_path, format="wav")
        segments_paths.append(chunk_path)
        
        # Move start pointer forward, subtracting overlap
        if end_ms >= len(audio):
            break
            
        start_ms = end_ms - overlap_ms
        seg_idx += 1
        
    return segments_paths
