import asyncio
from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path
import threading
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
    _load_lock = threading.Lock()

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
        with self._load_lock:
            if self._loaded:
                return
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            dtype = "auto"
            quant_config = None
            if self.settings.model_dtype in ["4bit", "int4", "q4"]:
                from transformers import BitsAndBytesConfig
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                dtype = torch.float16
            elif self.settings.model_dtype == "float16":
                dtype = torch.float16
            elif self.settings.model_dtype == "bfloat16":
                dtype = torch.bfloat16

            model_id_or_path = self.model_id_or_path
            self._tokenizer = AutoTokenizer.from_pretrained(model_id_or_path)
            load_kwargs = {
                "device_map": self.settings.model_device,
                "torch_dtype": dtype,
                "low_cpu_mem_usage": True,
            }
            if quant_config is not None:
                load_kwargs["quantization_config"] = quant_config

            self._model = AutoModelForCausalLM.from_pretrained(
                model_id_or_path,
                **load_kwargs,
            )
            self._torch = torch
            self._loaded = True

    async def complete(self, messages: list[dict[str, str]]) -> str:
        chunks = [chunk async for chunk in self.stream_chat(messages)]
        return "".join(chunks)

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        await asyncio.to_thread(self._ensure_loaded)
        from transformers import TextIteratorStreamer

        assert self._tokenizer is not None
        assert self._model is not None
        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer([prompt], return_tensors="pt").to(self._model.device)
        streamer = TextIteratorStreamer(
            self._tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=60
        )
        kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": min(512, self.settings.max_new_tokens),
            "temperature": self.settings.temperature,
            "top_p": self.settings.top_p,
            "do_sample": self.settings.temperature > 0,
        }

        generation_error: list[Exception] = []

        def run_generation() -> None:
            try:
                self._model.generate(**kwargs)
            except Exception as exc:
                print(f"[LLM] Error in model.generate: {exc}")
                generation_error.append(exc)

        Thread(target=run_generation, daemon=True).start()

        # Non-blocking streamer iteration using asyncio.to_thread so ASGI loop is NEVER blocked
        while True:
            try:
                token = await asyncio.to_thread(lambda: next(streamer))
                yield token
            except StopIteration:
                break
            except Exception as exc:
                print(f"[LLM] Streamer ended: {exc}")
                break

        if generation_error:
            raise RuntimeError(f"Model generation failed: {generation_error[0]}")


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider.lower() == "transformers":
        try:
            import torch
            import transformers
            return LocalTransformerLLM(settings)
        except ImportError:
            return MockLLM()
    return MockLLM()
