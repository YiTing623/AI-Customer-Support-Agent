import os


OPENAI_MODE = "openai"
DETERMINISTIC_MODE = "deterministic_demo"
OPENAI_MODE_NOTICE = "OpenAI Responses API tool-calling mode is enabled."
DETERMINISTIC_MODE_NOTICE = "LLM mode disabled: OPENAI_API_KEY is missing. Running deterministic demo mode."
OPENAI_FALLBACK_NOTICE = "OpenAI mode was requested but failed; deterministic demo mode completed the run."


def current_agent_mode() -> tuple[str, str]:
    if os.getenv("OPENAI_API_KEY"):
        return OPENAI_MODE, OPENAI_MODE_NOTICE
    return DETERMINISTIC_MODE, DETERMINISTIC_MODE_NOTICE
