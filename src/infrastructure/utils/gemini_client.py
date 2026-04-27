"""
Gemini API Interaction Utilities

This module provides high-level wrappers around the Google Generative AI SDK.
It implements robust execution patterns including:
1. Thread-guarded timeouts to prevent process hangs.
2. Exponential backoff retry logic for 503/429 status codes.
3. Automated usage tracking and billing integration.
"""

import time
import concurrent.futures
import sys
from typing import Any, List, Optional

from google.genai import types
from .logger import get_logger
from .billing import billing_tracker

# Standard logger for API interaction events
logger = get_logger("gemini_client")

def generate_with_timeout(client: Any, model: str, contents: Any, config_params: Any, timeout_sec: int, audio_duration_sec: float = 0) -> Any:
    """
    Executes a Gemini generation call within a strict execution thread.
    This prevents the entire process from freezing if the API holds a socket open indefinitely.

    Args:
        client: The Google GenAI client instance.
        model: The model string (e.g., 'gemini-2.5-pro').
        contents: The prompt data (text or list of parts).
        config_params: Validated generation config.
        timeout_sec: Maximum time to wait for a response before killing the thread.
        audio_duration_sec: Used for billing calculations if processing audio.

    Returns:
        The Gemini response object.

    Raises:
        TimeoutError: If the API does not respond within the timeframe.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            client.models.generate_content,
            model=model,
            contents=contents,
            config=config_params
        )
        try:
            response = future.result(timeout=timeout_sec)
            
            # Extract and log token usage metadata for audit trails
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                logger.info(f"Gemini Usage [{model}]: Prompt: {usage.prompt_token_count}, Candidate: {usage.candidates_token_count}")
                
                # Update the persistent billing tracker
                billing_tracker.add_usage(
                    model=model, 
                    prompt_tokens=usage.prompt_token_count, 
                    candidate_tokens=usage.candidates_token_count,
                    audio_duration_sec=audio_duration_sec,
                    context_tag="standard_generation"
                )
        except concurrent.futures.TimeoutError:
            # Cleanly interrupt the hanging future if possible
            future.cancel()
            raise TimeoutError(f"API TIMEOUT: Gemini did not respond within {timeout_sec}s.")
        
        return response

def resilient_generate(client: Any, model: str, contents: Any, config_params: Any, max_retries: int = 50, timeout_sec: int = 300, audio_duration_sec: float = 0) -> Any:
    """
    Orchestrates a robust API call with automated retries and exponential backoff.
    Specially tuned for handling 503 (Server Busy) and 429 (Rate Limit) errors
    common during high-volume real-estate data batching.

    Args:
        client: The GenAI client.
        model: Model name.
        contents: Input contents.
        config_params: GenConfig parameters.
        max_retries: Maximum attempts before giving up.
        timeout_sec: Timeout for each individual attempt.
        audio_duration_sec: Multi-modal metadata for billing.

    Returns:
        A successful Gemini response object.
    """
    for attempt in range(max_retries):
        try:
            response = generate_with_timeout(client, model, contents, config_params, timeout_sec, audio_duration_sec)
            return response
        except Exception as e:
            err_msg = str(e).lower()
            
            # Check for retriable errors: 503 (Unavail), 429 (Quota), or generic timeouts
            is_retriable = any(m in err_msg for m in ["503", "429", "timeout", "capacity", "unavailable", "high demand"])
            
            if is_retriable:
                # Progressive backoff: wait longer as more attempts fail
                wait_time = min(60 + (attempt * 10), 400)
                logger.warning(f"Gemini Transient Error ({err_msg[:60]}). Retrying in {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                # Non-retriable errors (e.g., 400 Bad Request) should fail immediately to save time
                logger.error(f"Critical API failure (Non-retriable): {e}")
                raise e
                
    raise RuntimeError(f"Exhausted all {max_retries} attempts for model {model}. API remained unavailable.")
