import base64
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

OPENAI_API_URL = "https://api.openai.com/v1"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class AIProviderError(RuntimeError):
    """Raised when the configured AI provider cannot generate a response."""


def _openai_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "Content-Type": "application/json",
    }


SYSTEM_PROMPT = "You are Echo, a capable ChatGPT-style AI assistant. Be helpful, accurate, clear, and conversational. Ask a focused clarifying question when the user's request is ambiguous."


def _provider_error(response: httpx.Response, provider: str) -> AIProviderError:
    try:
        provider_error = response.json().get("error", {})
    except (TypeError, ValueError):
        provider_error = {}
    error_code = provider_error.get("code")
    error_type = provider_error.get("type")
    if (
        error_code in ("insufficient_quota", "credit_balance_exhausted")
        or error_type == "insufficient_quota"
    ):
        return AIProviderError(
            f"The {provider} account has no remaining credits. Add credits or use a funded API key."
        )
    if response.status_code in (401, 403):
        return AIProviderError(
            f"The {provider} API key was rejected. Replace it with a valid key."
        )
    if response.status_code == 404:
        return AIProviderError(
            f"The configured {provider} model was not found. Check the model setting in backend/.env."
        )
    return AIProviderError(
        f"The {provider} provider rejected the request. Check the API key and model settings."
    )


def _openai_payload(message: str, history: list[dict[str, str]]) -> dict:
    return {
        "model": os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": message},
        ],
    }


def _gemini_payload(message: str, history: list[dict[str, str]]) -> dict:
    contents = [
        {
            "role": "model" if item["role"] == "assistant" else "user",
            "parts": [{"text": item["content"]}],
        }
        for item in history
    ]
    contents.append({"role": "user", "parts": [{"text": message}]})
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
    }


async def _generate_openai_reply(message: str, history: list[dict[str, str]]) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        raise AIProviderError("OPENAI_API_KEY is not configured in backend/.env.")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{OPENAI_API_URL}/chat/completions",
                headers=_openai_headers(),
                json=_openai_payload(message, history),
            )
            response.raise_for_status()
            data = response.json()
        reply = data["choices"][0]["message"]["content"]
    except httpx.TimeoutException as error:
        raise AIProviderError("The AI provider took too long to respond.") from error
    except httpx.HTTPStatusError as error:
        raise _provider_error(error.response, "OpenAI") from error
    except (httpx.RequestError, KeyError, IndexError, TypeError, ValueError) as error:
        raise AIProviderError(
            "The OpenAI provider returned an invalid response."
        ) from error

    if not isinstance(reply, str) or not reply.strip():
        raise AIProviderError("The OpenAI provider returned an empty response.")
    return reply.strip()


async def _generate_gemini_reply(message: str, history: list[dict[str, str]]) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AIProviderError("GEMINI_API_KEY is not configured in backend/.env.")
    model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
    url = f"{GEMINI_API_URL}/{model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                json=_gemini_payload(message, history),
            )
            response.raise_for_status()
            data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except httpx.TimeoutException as error:
        raise AIProviderError("The AI provider took too long to respond.") from error
    except httpx.HTTPStatusError as error:
        raise _provider_error(error.response, "Gemini") from error
    except (httpx.RequestError, KeyError, IndexError, TypeError, ValueError) as error:
        raise AIProviderError(
            "The Gemini provider returned an invalid response."
        ) from error
    if not isinstance(reply, str) or not reply.strip():
        raise AIProviderError("The Gemini provider returned an empty response.")
    return reply.strip()


async def generate_chat_reply(
    message: str, history: list[dict[str, str]]
) -> tuple[str, str]:
    provider = os.getenv("AI_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return await _generate_openai_reply(message, history), provider
    if provider in {"gemini", "google"}:
        return await _generate_gemini_reply(message, history), "gemini"
    raise AIProviderError(
        "Unsupported AI_PROVIDER. Set it to 'openai' or 'gemini' in backend/.env."
    )


async def generate_image(prompt: str, output_dir: Path) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    image_id = os.urandom(8).hex()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{image_id}.svg"

    if not api_key:
        escaped = prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        output_path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024"><rect width="100%" height="100%" fill="#18212f"/><text x="50%" y="48%" fill="#f5efe5" text-anchor="middle" font-size="28">Echo demo image</text><text x="50%" y="54%" fill="#b5c1d1" text-anchor="middle" font-size="18">{escaped}</text></svg>',
            encoding="utf-8",
        )
        return f"/media/{output_path.name}", "demo"

    payload = {
        "model": os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        "prompt": prompt,
        "size": "1024x1024",
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{OPENAI_API_URL}/images/generations", headers=_headers(), json=payload
        )
        response.raise_for_status()
    image_data = response.json()["data"][0]
    if image_data.get("b64_json"):
        png_path = output_dir / f"{image_id}.png"
        png_path.write_bytes(base64.b64decode(image_data["b64_json"]))
        return f"/media/{png_path.name}", "openai"
    return image_data["url"], "openai"
