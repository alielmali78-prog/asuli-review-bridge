"""Text-only adapters. No tools, shell execution, automatic retries or custom URLs."""
import json
import os
from urllib.request import Request, urlopen

SYSTEM = ("You are an advisory reviewer, not an approver. Separate supplied observations "
          "from independently verified evidence. You have no tools or system access. "
          "Give a concise critique, strongest counterargument and a discriminating test. "
          "Never claim a deployment or test passed without supplied evidence.")


class ProviderError(RuntimeError):
    pass


def _post(url, headers, payload):
    request = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def ask(provider, body, *, allow_network=False, transport=None):
    provider = provider.upper()
    if provider == "MOCK":
        return {"text": "OFFLINE FIXTURE — not a real model opinion.\nThe supplied delivery claim needs an automatic-run trace. A manual readback alone does not prove scheduled delivery.",
                "provider": "MOCK", "model": "offline-fixture", "usage": {}}
    if provider not in {"GEMINI", "ABDUR", "KIMI"}:
        raise ValueError("Unsupported provider")
    if not allow_network:
        raise ProviderError("Network disabled; explicit --allow-network required")
    prefix = {"GEMINI": "GEMINI", "ABDUR": "ANTHROPIC", "KIMI": "KIMI"}[provider]
    key = os.environ.get(prefix + "_API_KEY", "")
    model = os.environ.get(prefix + "_MODEL", "")
    # Models are deliberately not pinned to private runtime aliases. The owner
    # selects a currently available model and checks pricing before opting in.
    if not key or not model:
        raise ProviderError("Provider key and model must be explicitly configured")
    if any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in model):
        raise ProviderError("Invalid model identifier")
    transport = transport or _post
    try:
        if provider == "GEMINI":
            url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"
            data = transport(url, {"x-goog-api-key": key}, {
                "systemInstruction": {"parts": [{"text": SYSTEM}]},
                "contents": [{"role": "user", "parts": [{"text": body}]}],
                "generationConfig": {"maxOutputTokens": 1200}})
            candidate = data["candidates"][0]
            if candidate.get("finishReason") != "STOP":
                raise ProviderError("Provider output incomplete or blocked")
            text = "\n".join(p.get("text", "") for p in candidate["content"]["parts"] if not p.get("thought"))
            usage = data.get("usageMetadata", {})
        elif provider == "ABDUR":
            data = transport("https://api.anthropic.com/v1/messages",
                             {"x-api-key": key, "anthropic-version": "2023-06-01"},
                             {"model": model, "max_tokens": 1200, "system": SYSTEM,
                              "messages": [{"role": "user", "content": body}]})
            if data.get("stop_reason") != "end_turn":
                raise ProviderError("Provider output incomplete or blocked")
            text = "\n".join(p.get("text", "") for p in data["content"] if p.get("type") == "text")
            usage = data.get("usage", {})
        else:
            data = transport("https://api.moonshot.ai/v1/chat/completions",
                             {"Authorization": "Bearer " + key},
                             {"model": model, "max_tokens": 1200,
                              "thinking": {"type": "disabled"},
                              "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": body}]})
            choice = data["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise ProviderError("Provider output incomplete or blocked")
            text = choice["message"]["content"]
            usage = data.get("usage", {})
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("Empty provider output")
        return {"text": text.strip(), "provider": provider, "model": model, "usage": usage}
    except ProviderError:
        raise
    except Exception:
        # Never include raw HTTP errors, credentials, URLs or response bodies.
        raise ProviderError("Provider call failed or response schema was invalid; no automatic retry") from None
