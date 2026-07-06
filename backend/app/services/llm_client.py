"""LLM client — wraps Google Gemini API."""
import os
import json
from typing import Iterator, Optional
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_client = None
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


class QuotaExceededError(Exception):
    """Raised when Gemini returns 429/ResourceExhausted."""
    pass


def _get_client():
    global _client
    if _client is None:
        import google.generativeai as genai
        api_key = settings.gemini_api_key
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file")
        genai.configure(api_key=api_key)
        _client = genai
    return _client


def _is_quota_error(e: Exception) -> bool:
    err_str = str(e).lower()
    return "429" in err_str or "resource_exhausted" in err_str or "resourceexhausted" in err_str or "quota" in err_str


def generate(prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.1,
             max_output_tokens: int = 2048) -> str:
    """Generate a non-streaming response."""
    genai = _get_client()
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=system_instruction or "You are a meticulous case analyst.",
            generation_config={"temperature": temperature, "max_output_tokens": max_output_tokens}
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if _is_quota_error(e):
            raise QuotaExceededError("Gemini API quota exceeded. Please try again later or use a different API key.") from e
        logger.error(f"Gemini generate error: {e}")
        raise
def _extract_json_object(text: str) -> str:
    """Isolate the outermost JSON object/array from surrounding text via balanced-bracket matching."""
    text = text.strip()
    if text.startswith("```"):
        text = text[text.find("\n") + 1:]
        if text.endswith("```"):
            text = text[:-3]
    text = text.strip()

    start = None
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            open_ch, close_ch = ch, ("}" if ch == "{" else "]")
            break
    if start is None:
        return text

    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:] 


def generate_stream(prompt: str, system_instruction: Optional[str] = None,
                     temperature: float = 0.2) -> Iterator[str]:
    """Generate a streaming response, yielding text chunks."""
    genai = _get_client()
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=system_instruction or "You are a meticulous case analyst.",
            generation_config={"temperature": temperature, "max_output_tokens": 2048}
        )
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        if _is_quota_error(e):
            raise QuotaExceededError("Gemini API quota exceeded. Please try again later.") from e
        logger.error(f"Gemini stream error: {e}")
        raise


def generate_json(prompt: str, system_instruction: Optional[str] = None) -> dict:
    """Generate and parse a JSON response, with one retry on parse failure."""
    text = generate(prompt, system_instruction, temperature=0.0, max_output_tokens=8192)
    candidate = _extract_json_object(text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        logger.warning("JSON parse failed, retrying...")
        try:
            text2 = generate(
                prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON, no markdown, no explanation.",
                system_instruction, temperature=0.0, max_output_tokens=8192
            )
            candidate2 = _extract_json_object(text2)
            return json.loads(candidate2)
        except Exception as e2:
            logger.error(f"JSON retry failed: {e2}")
            return {}
