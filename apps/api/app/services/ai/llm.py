import asyncio
from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path
from threading import Thread
from typing import Protocol

from app.core.config import PROJECT_ROOT, Settings, get_settings


class ModelNotReadyError(RuntimeError):
    pass


class LLMProvider(Protocol):
    async def complete(self, messages: list[dict[str, str]]) -> str:
        ...

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        ...


class MockLLM:
    """Development-safe local provider used until a 7B model is configured."""

    async def complete(self, messages: list[dict[str, str]]) -> str:
        user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return (
            "Aegis AI local development response.\n\n"
            f"I received: {user_message}\n\n"
            "Switch `LLM_PROVIDER=transformers` and set `LOCAL_MODEL_ID` to a local "
            "Mistral 7B or Qwen 2.5 7B path to enable real generation."
        )

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        response = await self.complete(messages)
        for token in response.split(" "):
            yield token + " "
            await asyncio.sleep(0.01)


class LocalTransformerLLM:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._loaded = False
        self._tokenizer = None
        self._model = None
        self._torch = None

    @property
    def model_id_or_path(self) -> str:
        model_path = Path(self.settings.local_model_id)
        if not model_path.is_absolute():
            model_path = PROJECT_ROOT / model_path
        if model_path.exists():
            incomplete_files = list(model_path.rglob("*.incomplete"))
            safetensor_files = list(model_path.glob("*.safetensors"))
            if incomplete_files or not safetensor_files:
                raise ModelNotReadyError(
                    "Mistral is still downloading. Wait for `python download_model.py` to print "
                    "`Download complete`, then send the message again."
                )
            return str(model_path)
        return self.settings.local_model_id

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        dtype = "auto"
        if self.settings.model_dtype == "float16":
            dtype = torch.float16
        elif self.settings.model_dtype == "bfloat16":
            dtype = torch.bfloat16

        model_id_or_path = self.model_id_or_path
        self._tokenizer = AutoTokenizer.from_pretrained(model_id_or_path)
        self._model = AutoModelForCausalLM.from_pretrained(
            model_id_or_path,
            device_map=self.settings.model_device,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
        )
        self._torch = torch
        self._loaded = True

    async def complete(self, messages: list[dict[str, str]]) -> str:
        chunks = [chunk async for chunk in self.stream_chat(messages)]
        return "".join(chunks)

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        self._ensure_loaded()
        from transformers import TextIteratorStreamer

        assert self._tokenizer is not None
        assert self._model is not None
        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer([prompt], return_tensors="pt").to(self._model.device)
        streamer = TextIteratorStreamer(
            self._tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=30
        )
        kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": self.settings.max_new_tokens,
            "temperature": self.settings.temperature,
            "top_p": self.settings.top_p,
            "do_sample": self.settings.temperature > 0,
        }
        Thread(target=self._model.generate, kwargs=kwargs, daemon=True).start()
        for text in streamer:
            yield text
            await asyncio.sleep(0)


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider.lower() == "transformers":
        return LocalTransformerLLM(settings)
    return MockLLM()
