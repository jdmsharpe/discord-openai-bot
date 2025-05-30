import re
from typing import List, Optional

CHUNK_TEXT_SIZE = 3500  # Maximum number of characters in each text chunk.
REASONING_MODELS = ["o4-mini", "o3", "o3-mini", "o1", "o1-mini"]
RICH_TTS_MODELS = ["gpt-4o-tts", "gpt-4o-mini-tts"]
RICH_TTS_VOICES = ["ash", "ballad", "coral", "sage", "verse"]


class ChatCompletionParameters:
    def __init__(
        self,
        messages: List[dict] = [],
        model: str = "gpt-4.1",
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
        self.messages = messages
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
        model: str = "dall-e-3",
        n: int = 1,
        quality: str = "standard",
        size: str = "1024x1024",
        style: Optional[str] = None,
    ):
        self.prompt = prompt
        self.model = model
        self.n = n
        self.quality = quality
        self.size = size
        self.style = style

    def to_dict(self):
        return {
            "prompt": self.prompt,
            "model": self.model,
            "n": self.n,
            "quality": self.quality,
            "size": self.size,
            "style": self.style,
        }


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

        # Older models do not support all voices.
        if model not in RICH_TTS_MODELS:
            if voice not in RICH_TTS_VOICES:
                # User picked a voice that is not supported by the model.
                # For TTS-1 and TTS-1-HD, force the default voice (Alloy).
                self.voice = "alloy"

            self.instructions = None
        else:
            self.voice = voice
            self.instructions = instructions

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
