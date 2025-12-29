# from __future__ import annotations
# from dotenv import load_dotenv
# load_dotenv()

# import os
# import time
# from dataclasses import dataclass
# from typing import Any, Dict, Optional

# import httpx


# @dataclass
# class LLMResult:
#     text: str
#     latency_ms: float
#     model: str


# class HFInferenceClient:
#     """
#     Hugging Face Inference API client (free tier works, but rate-limited).
#     Uses the universal /models/{repo_id} endpoint.
#     """
#     def __init__(self, token: Optional[str] = None, timeout_s: int = 120):
#         self.token = token or os.getenv("HF_API_TOKEN", "")
#         self.timeout_s = timeout_s
#         if not self.token:
#             raise ValueError("HF_API_TOKEN is missing. Put it in your .env")

#     def generate(self, model: str, prompt: str, max_new_tokens: int = 300, temperature: float = 0.2) -> LLMResult:
#         # url = f"https://api-inference.huggingface.co/models/{model}"
#         url = "https://api-inference.huggingface.co/v1/chat/completions"

#         headers = {"Authorization": f"Bearer {self.token}"}
#         payload: Dict[str, Any] = {
#             "inputs": prompt,
#             "parameters": {
#                 "max_new_tokens": max_new_tokens,
#                 "temperature": temperature,
#                 "return_full_text": False,
#             }
#         }

#         t0 = time.perf_counter()
#         with httpx.Client(timeout=self.timeout_s) as client:
#             r = client.post(url, headers=headers, json=payload)
#             r.raise_for_status()
#             data = r.json()
#         t1 = time.perf_counter()

#         # HF sometimes returns list[{"generated_text": "..."}]
#         if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
#             text = data[0]["generated_text"]
#         elif isinstance(data, dict) and "generated_text" in data:
#             text = data["generated_text"]
#         else:
#             text = str(data)

#         return LLMResult(text=text.strip(), latency_ms=(t1 - t0) * 1000.0, model=model)

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Optional

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


@dataclass
class HFText:
    text: str


class HFInferenceClient:
    """
    Minimal wrapper around huggingface_hub.InferenceClient for chat-style LLM calls.

    We use HF Inference Providers through the huggingface_hub client (recommended path).
    """

    def __init__(self) -> None:
        load_dotenv()  # reads .env from repo root

        token = os.getenv("HF_API_TOKEN", "").strip()
        if not token:
            raise ValueError("HF_API_TOKEN is missing. Put it in your .env (file name must be exactly .env).")

        # Provider is optional. If omitted, HF uses your account/provider routing defaults.
        self.provider = os.getenv("HF_PROVIDER", "").strip() or None
        self.token = token

        # Create a single client. We will pass `model=` per request.
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

        # InferenceClient.chat_completion is the supported interface for LLM chat
        out = self.client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=int(max_new_tokens),
            temperature=float(temperature),
        )

        text = ""
        if out and out.choices and out.choices[0].message and out.choices[0].message.content:
            text = out.choices[0].message.content

        return HFText(text=text.strip())
