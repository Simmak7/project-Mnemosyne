"""
Ollama Model Update Checker - Compare local vs registry digests.

Checks each installed Ollama model against the OCI registry at
registry.ollama.com to detect available updates.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests

from core import config

logger = logging.getLogger(__name__)

# In-memory cache: model_name -> {result, timestamp}
_update_cache: dict = {}
CACHE_TTL = 3600  # 1 hour


def parse_model_name(name: str) -> tuple[str, str, str]:
    """Parse 'namespace/repo:tag' into (namespace, repo, tag)."""
    # Strip digest suffix if present (e.g. "qwen3:8b@sha256:...")
    name = name.split("@")[0]

    if "/" in name:
        namespace, rest = name.split("/", 1)
    else:
        namespace = "library"
        rest = name

    if ":" in rest:
        repo, tag = rest.split(":", 1)
    else:
        repo = rest
        tag = "latest"

    return namespace, repo, tag


def get_local_model_digests() -> dict[str, str]:
    """Fetch installed models from Ollama /api/tags, return {name: digest}."""
    try:
        resp = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=10)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        result = {}
        for m in models:
            name = m.get("name", "")
            digest = m.get("digest", "")
            if name and digest:
                result[name] = digest
        return result
    except Exception as e:
        logger.error(f"Failed to fetch local models: {e}")
        return {}


def _get_registry_token(namespace: str, repo: str) -> Optional[str]:
    """Get a pull-scoped bearer token from Ollama registry."""
    try:
        url = "https://registry.ollama.com/token"
        params = {
            "service": "registry.ollama.com",
            "scope": f"repository:{namespace}/{repo}:pull",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("token")
    except Exception as e:
        logger.debug(f"Token fetch failed for {namespace}/{repo}: {e}")
        return None


def _get_remote_digest(namespace: str, repo: str, tag: str) -> Optional[str]:
    """Fetch the OCI manifest digest from the Ollama registry."""
    token = _get_registry_token(namespace, repo)
    if not token:
        return None

    try:
        url = f"https://registry.ollama.com/v2/{namespace}/{repo}/manifests/{tag}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        }
        resp = requests.head(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.headers.get("Docker-Content-Digest")
        logger.debug(f"Registry returned {resp.status_code} for {namespace}/{repo}:{tag}")
        return None
    except Exception as e:
        logger.debug(f"Remote digest fetch failed for {namespace}/{repo}:{tag}: {e}")
        return None


def _check_single_model(name: str, local_digest: str, force: bool) -> dict:
    """Compare one model's local digest against the registry."""
    # Check cache first
    if not force and name in _update_cache:
        cached = _update_cache[name]
        if time.time() - cached["timestamp"] < CACHE_TTL:
            return cached["result"]

    namespace, repo, tag = parse_model_name(name)
    remote_digest = _get_remote_digest(namespace, repo, tag)

    if remote_digest is None:
        result = {
            "model": name,
            "update_available": False,
            "status": "unknown",
            "local_digest": local_digest[:16],
            "remote_digest": None,
        }
    else:
        has_update = remote_digest != f"sha256:{local_digest}" and local_digest not in (remote_digest or "")
        result = {
            "model": name,
            "update_available": has_update,
            "status": "update_available" if has_update else "up_to_date",
            "local_digest": local_digest[:16],
            "remote_digest": remote_digest[:16] if remote_digest else None,
        }

    _update_cache[name] = {"result": result, "timestamp": time.time()}
    return result


def check_all_updates(force: bool = False) -> list[dict]:
    """Check all installed Ollama models for updates concurrently."""
    local = get_local_model_digests()
    if not local:
        return []

    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(_check_single_model, name, digest, force): name
            for name, digest in local.items()
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                model = futures[future]
                logger.error(f"Update check failed for {model}: {e}")
                results.append({
                    "model": model,
                    "update_available": False,
                    "status": "error",
                    "local_digest": None,
                    "remote_digest": None,
                })

    results.sort(key=lambda r: r["model"])
    return results


def invalidate_update_cache(model_name: str = None):
    """Clear cached update status after pull/delete."""
    if model_name:
        _update_cache.pop(model_name, None)
        # Also clear with/without :latest suffix
        if ":" not in model_name:
            _update_cache.pop(f"{model_name}:latest", None)
        elif model_name.endswith(":latest"):
            _update_cache.pop(model_name.replace(":latest", ""), None)
    else:
        _update_cache.clear()
