from typing import Dict, Any, List, Tuple

# LLM Task Directory
RESUME_SKILL_EXTRACTION = "resume_skill_extraction"
RESUME_CONDENSATION     = "resume_condensation"
JOB_SKILL_EXTRACTION    = "job_skill_extraction"
JOB_RESUME_MATCH        = "job_resume_match"

PROVIDER_TIMEOUTS = {
    "gemini":     30,
    "groq":       30,
    "cerebras":   30,
    "sambanova":  60,
    "openrouter": 90,
}

LLM_TASK_CONFIGS: Dict[str, Dict[str, Any]] = {
    RESUME_SKILL_EXTRACTION: {
        "description": "Strict JSON skill extraction from resume text",
        "provider": "sambanova",
        "model":    "Meta-Llama-4-Maverick-17B-128E-Instruct",
        "fallbacks": [
            ("gemini",     "gemini-3.1-flash-lite-preview"),
            ("groq",       "llama-3.3-70b-versatile"),
            ("cerebras",   "llama3.1-8b"),
        ],
        "max_tokens":      2048,
        "temperature":     0.0,
        "response_format": "json",
    },
    RESUME_CONDENSATION: {
        "description": "Plain-text candidate profile condensation from resume text",
        "provider": "cerebras",
        "model":    "llama3.1-8b",
        "fallbacks": [
            ("sambanova",  "Qwen3-32B"),
            ("gemini",     "gemini-3.1-flash-lite-preview"),
            ("groq",       "qwen/qwen3-32b"),
        ],
        "max_tokens":      1200,
        "temperature":     0.2,
        "response_format": "text",
    },
    JOB_SKILL_EXTRACTION: {
        "description": "Extract role_type, seniority, years_required, skills[] from a JD",
        "provider":    "sambanova",
        "model":       "Qwen3-32B",
        "fallbacks": [
            ("gemini",     "gemini-3.1-flash-lite-preview"),
            ("groq",       "llama-3.3-70b-versatile"),
            ("cerebras",   "llama3.1-8b"),
        ],
        "max_tokens":      2048,
        "temperature":     0.0,
        "response_format": "json",
    },
    JOB_RESUME_MATCH: {
        "description": "Score skill_fit, role_fit, experience_fit against candidate profile",
        "provider":    "sambanova",
        "model":       "Qwen3-235B-A22B-Instruct-2507",
        "fallbacks": [
            ("cerebras",   "qwen-3-235b-a22b-instruct-2507"),
            ("gemini",     "gemini-3.1-flash-lite-preview"),
            ("groq",       "llama-3.3-70b-versatile"),
        ],
        "max_tokens":      4096,
        "temperature":     0.1,
        "response_format": "json",
    },
}


def get_llm_task_config(task_name: str) -> Dict[str, Any]:
    try:
        return LLM_TASK_CONFIGS[task_name]
    except KeyError as e:
        raise ValueError(f"Unknown LLM task config: {task_name}") from e
