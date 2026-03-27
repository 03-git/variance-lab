#!/usr/bin/env python3
"""Run a single prompt against a local model via OpenAI-compatible API (Ollama or LM Studio).

Usage: python3 run-local-single.py --model <model> --prompt-file <path> --output-dir <path>
           [--endpoint ollama|lmstudio|<url>] [--tier execution|reasoning|research]
           [--max-tokens 4096] [--temperature 0.7] [--dry-run]
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

ENDPOINTS = {
    "ollama": "http://localhost:11434/v1/chat/completions",
    "lmstudio": "http://localhost:1234/v1/chat/completions",
}


def call_model(endpoint_url, model, prompt, max_tokens=4096, temperature=0.7):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return None, {"error": str(e), "wall_seconds": time.time() - start}
    except Exception as e:
        return None, {"error": str(e), "wall_seconds": time.time() - start}

    wall_seconds = time.time() - start
    choices = body.get("choices", [])
    content = choices[0]["message"]["content"] if choices else ""
    usage = body.get("usage", {})

    comp_tokens = usage.get("completion_tokens", 0)
    metrics = {
        "model": model,
        "endpoint": endpoint_url,
        "wall_seconds": round(wall_seconds, 2),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": comp_tokens,
        "total_tokens": usage.get("total_tokens", 0),
        "tokens_per_second": round(comp_tokens / wall_seconds, 1) if wall_seconds > 0 else 0,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_length_chars": len(content),
        "finish_reason": choices[0].get("finish_reason", "unknown") if choices else "no_response",
    }

    return content, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--endpoint", default="ollama")
    parser.add_argument("--tier", default="unknown", help="execution, reasoning, or research")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    endpoint_url = ENDPOINTS.get(args.endpoint, args.endpoint)

    with open(args.prompt_file, "r") as f:
        prompt = f.read().strip()

    safe_model = args.model.replace("/", "_").replace(":", "_")
    out = os.path.join(args.output_dir, safe_model)
    os.makedirs(out, exist_ok=True)

    config = {
        "model": args.model,
        "endpoint": endpoint_url,
        "tier": args.tier,
        "prompt_file": args.prompt_file,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }

    if args.dry_run:
        print("[DRY RUN] [%s] %s via %s" % (args.tier, args.model, endpoint_url))
        with open(os.path.join(out, "config.json"), "w") as f:
            json.dump(config, f, indent=2)
        return

    sys.stdout.write("  [%s] %s... " % (args.tier, args.model))
    sys.stdout.flush()

    content, metrics = call_model(
        endpoint_url, args.model, prompt,
        max_tokens=args.max_tokens, temperature=args.temperature,
    )

    # Embed tier in metrics
    metrics["tier"] = args.tier

    with open(os.path.join(out, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    if content:
        with open(os.path.join(out, "response.md"), "w") as f:
            f.write(content)
        ws = metrics["wall_seconds"]
        tps = metrics["tokens_per_second"]
        tt = metrics["total_tokens"]
        print("%ss | %.1f tok/s | %d tokens" % (ws, tps, tt))
    else:
        err = metrics.get("error", "unknown")
        print("ERROR: %s" % err)

    with open(os.path.join(out, "config.json"), "w") as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    main()
