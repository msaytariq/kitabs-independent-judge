"""Content identity and honest model-family provenance."""
from dataclasses import asdict
import hashlib
import json


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def identity(scope, config, code_sha: str, prompts: dict) -> str:
    return digest({'scope':asdict(scope),'config':asdict(config),'code_sha':code_sha,'prompts':prompts})


def independence(judge_model: str, translator_vendor: str | None) -> str:
    if not translator_vendor: return 'unknown'
    return 'same_vendor' if judge_model.split('/')[0]==translator_vendor else 'different_vendor'
