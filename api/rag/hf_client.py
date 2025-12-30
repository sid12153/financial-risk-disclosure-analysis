from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import random


@dataclass
class HFText:
    text: str
    latency_ms: float


class HFInferenceClient:
    """
    Minimal wrapper around huggingface_hub.InferenceClient for chat-style LLM calls.
    Returns both text and measured latency_ms.
    """

    def __init__(self) -> None:
        load_dotenv()  # reads .env from repo root

        token = os.getenv("HF_API_TOKEN", "").strip()
        if not token:
            raise ValueError("HF_API_TOKEN is missing. Put it in your .env (file name must be exactly .env).")

        self.provider = os.getenv("HF_PROVIDER", "").strip() or None
        self.token = token

        if self.provider:
            self.client = InferenceClient(provider=self.provider, api_key=self.token)
        else:
            self.client = InferenceClient(api_key=self.token)

    def generate(
        self,
        model: str,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
    ) -> HFText:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        t0 = time.perf_counter()
        out = self.client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=int(max_new_tokens),
            temperature=float(temperature),
        )
        t1 = time.perf_counter()

        text = ""
        if out and out.choices and out.choices[0].message and out.choices[0].message.content:
            text = out.choices[0].message.content

        return HFText(text=text.strip(), latency_ms=(t1 - t0) * 1000.0)
