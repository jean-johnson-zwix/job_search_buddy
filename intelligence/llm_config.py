from typing import Dict, Any, List, Tuple

# LLM Task Directory
RESUME_SKILL_EXTRACTION = "resume_skill_extraction"
RESUME_CONDENSATION = "resume_condensation"

PROVIDER_TIMEOUTS = {
    "gemini":     30,
    "groq":       30,
    "openrouter": 90,
}

LLM_TASK_CONFIGS: Dict[str, Dict[str, Any]] = {
    RESUME_SKILL_EXTRACTION: {
        "description": "Strict JSON skill extraction from resume text",
        "provider": "gemini",
        "model": "gemini-3.1-flash-lite-preview",
        "fallbacks": [
            ("groq", "qwen/qwen3-32b"),
            ("openrouter", "z-ai/glm-4.5-air:free"),
            ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),
        ],
        "max_tokens": 2048,
        "temperature": 0.0,
        "response_format": "json",
    },
    RESUME_CONDENSATION: {
        "description": "Plain-text candidate profile condensation from resume text",
        "provider": "gemini",
        "model": "gemini-3.1-flash-lite-preview",
        "fallbacks": [
            ("groq",       "qwen/qwen3-32b"),
            ("openrouter", "z-ai/glm-4.5-air:free"),
            ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),
        ],
        "max_tokens": 1200,
        "temperature": 0.2,
        "response_format": "text",
    },
}


def get_llm_task_config(task_name: str) -> Dict[str, Any]:
    try:
        return LLM_TASK_CONFIGS[task_name]
    except KeyError as e:
        raise ValueError(f"Unknown LLM task config: {task_name}") from e