import re
from typing import Any, Dict, List, Optional

from openai import APIError

CHUNK_TEXT_SIZE = 3500  # Maximum number of characters in each text chunk.
REASONING_MODELS = ["o4-mini", "o3", "o3-mini", "o1", "o1-mini"]
RICH_TTS_MODELS = ["gpt-4o-tts", "gpt-4o-mini-tts"]

RICH_TTS_VOICES = {"ash", "ballad", "coral", "sage", "verse"}
STANDARD_TTS_VOICES = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
DEFAULT_TTS_VOICE = "alloy"
MODEL_SUPPORTED_TTS_VOICES = {
    "tts-1": STANDARD_TTS_VOICES,
    "tts-1-hd": STANDARD_TTS_VOICES,
    "gpt-4o-tts": STANDARD_TTS_VOICES | RICH_TTS_VOICES,
    "gpt-4o-mini-tts": STANDARD_TTS_VOICES | RICH_TTS_VOICES,
}
DEFAULT_SUPPORTED_TTS_VOICES = STANDARD_TTS_VOICES | RICH_TTS_VOICES



class ChatCompletionParameters:
    def __init__(
        self,
        messages: Optional[List[dict]] = None,
        model: str = "gpt-5",
        persona: str = "You are a helpful assistant.",
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        conversation_starter: Optional[str] = None,
        conversation_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        paused: Optional[bool] = False,
    ):
        self.messages = [msg.copy() for msg in messages] if messages is not None else []
        self.model = model
        self.persona = persona
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.seed = seed

        # Define the models that do not support custom temperature and top_p.
        if model in REASONING_MODELS:
            # For reasoning models, force the default temperature (1.0) and ignore top_p.
            self.temperature = 1.0
            self.top_p = None
        else:
            self.temperature = temperature
            self.top_p = top_p

        self.conversation_starter = conversation_starter
        self.conversation_id = conversation_id
        self.channel_id = channel_id
        self.paused = paused

    def to_dict(self):
        # Create a copy of messages to avoid mutating the original list.
        messages_copy = [msg.copy() for msg in self.messages]
        for message in messages_copy:
            if "content" in message:
                # Ensure the content is a list of dictionaries if not already.
                if not isinstance(message["content"], list):
                    message["content"] = [message["content"]]

        payload = {
            "messages": messages_copy,
            "model": self.model,
        }
        if self.frequency_penalty is not None:
            payload["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            payload["presence_penalty"] = self.presence_penalty
        if self.seed is not None:
            payload["seed"] = self.seed
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.top_p is not None:
            payload["top_p"] = self.top_p

        return payload


class ImageGenerationParameters:
    def __init__(
        self,
        prompt: str = "",
        model: str = "gpt-image-1",
        n: int = 1,
        quality: Optional[str] = "medium",
        size: Optional[str] = "1024x1024",
        style: Optional[str] = None,
        response_format: Optional[str] = None,
    ):
        self.prompt = prompt
        self.model = model
        self.n = n

        # Set appropriate quality based on model if using default
        if quality == "medium":
            if model == "dall-e-3":
                self.quality = "hd"  # DALL-E 3 uses "hd" as default for better quality
            elif model == "dall-e-2":
                self.quality = "standard"  # DALL-E 2 only supports "standard"
            else:
                self.quality = quality  # Keep "medium" for gpt-image-1
        else:
            self.quality = quality

        self.size = size
        self.style = style

        # Only set response_format for models that support it (DALL-E models)
        if model in ["dall-e-2", "dall-e-3"] and response_format is not None:
            self.response_format = response_format
        else:
            self.response_format = None

    def to_dict(self):
        payload = {
            "prompt": self.prompt,
            "model": self.model,
            "n": self.n,
        }
        if self.quality is not None:
            payload["quality"] = self.quality
        if self.size is not None:
            payload["size"] = self.size
        if self.style is not None:
            payload["style"] = self.style
        # Only include response_format if it's set (for DALL-E models)
        if self.response_format is not None:
            payload["response_format"] = self.response_format
        return payload


class TextToSpeechParameters:
    def __init__(
        self,
        input: str = "",
        model: str = "gpt-4o-mini-tts",
        voice: str = "alloy",
        instructions: str = "",
        response_format: str = "mp3",
        speed: float = 1.0,
    ):
        self.input = input
        self.model = model

        supported_voices = MODEL_SUPPORTED_TTS_VOICES.get(
            model, DEFAULT_SUPPORTED_TTS_VOICES
        )
        if voice in supported_voices:
            self.voice = voice
        else:
            self.voice = DEFAULT_TTS_VOICE

        if model in RICH_TTS_MODELS:
            self.instructions = instructions
        else:
            self.instructions = None

        self.response_format = response_format
        self.speed = speed

    def to_dict(self):
        return {
            "input": self.input,
            "model": self.model,
            "voice": self.voice,
            "instructions": self.instructions,
            "response_format": self.response_format,
            "speed": self.speed,
        }


def chunk_text(text, size=CHUNK_TEXT_SIZE):
    """Yield successive size chunks from text."""
    return list(text[i : i + size] for i in range(0, len(text), size))


def extract_urls(text):
    url_pattern = (
        r"http[s]?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    urls = re.findall(url_pattern, text)
    return urls


def _parse_error_payload(payload: Any) -> Dict[str, str]:
    """Pull standard OpenAI error fields from a payload structure."""
    if not isinstance(payload, dict):
        return {}

    candidate = payload.get("error")
    if isinstance(candidate, dict):
        payload = candidate

    extracted: Dict[str, str] = {}
    for key in ("message", "type", "code", "param"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            extracted[key] = value.strip()
    return extracted


def _extract_response_error_info(response: Any) -> Dict[str, str]:
    """Attempt to parse error details from an HTTP-like response object."""
    info: Dict[str, str] = {}
    if response is None:
        return info

    if hasattr(response, "json"):
        try:
            payload = response.json()
        except Exception:
            payload = None
        else:
            info = _parse_error_payload(payload)
            if not info and isinstance(payload, dict):
                for key in ("detail", "message", "error"):
                    value = payload.get(key)
                    if isinstance(value, str) and value.strip():
                        info["message"] = value.strip()
                        break

    if "message" not in info:
        text_value = getattr(response, "text", None)
        if isinstance(text_value, str) and text_value.strip():
            info.setdefault("message", text_value.strip())

    return info


def format_openai_error(error: Exception) -> str:
    """Return a readable description for exceptions raised by OpenAI operations."""
    message = getattr(error, "message", None)
    if not isinstance(message, str) or not message.strip():
        message = str(error).strip()

    status = getattr(error, "status_code", None)
    error_type = getattr(error, "type", None)
    code = getattr(error, "code", None)
    param = getattr(error, "param", None)

    if isinstance(error, APIError):
        extracted = _parse_error_payload(getattr(error, "body", None))
    else:
        response = getattr(error, "response", None)
        if response is not None and status is None:
            status = getattr(response, "status_code", None)
        extracted = _extract_response_error_info(response)

    if extracted.get("message"):
        message = extracted["message"]
    error_type = error_type or extracted.get("type")
    code = code or extracted.get("code")
    param = param or extracted.get("param")

    message = message or "An unexpected error occurred."

    details = []
    if status is not None:
        details.append(f"Status: {status}")

    error_name = type(error).__name__
    if error_name and error_name != "Exception":
        details.append(f"Error: {error_name}")

    if error_type:
        details.append(f"Type: {error_type}")
    if code:
        details.append(f"Code: {code}")
    if param:
        details.append(f"Param: {param}")

    if details:
        return f"{message}\n\n" + "\n".join(details)
    return message

