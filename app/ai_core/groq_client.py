import logging

from groq import Groq

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a professional AI marketing strategist."
MODEL_NAME = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.3


def _get_groq_client() -> Groq:
    """Instantiate a Groq client with the configured API key."""
    settings = get_settings()
    return Groq(api_key=settings.GROQ_API_KEY)


def generate_strategy(prompt: str, system_prompt: str | None = None) -> str:
    """Send a prompt to the Groq LLM and return the raw text response.

    Args:
        prompt: The user prompt describing the strategy request.
        system_prompt: Optional override for the system role message.
            Falls back to the default SYSTEM_PROMPT if not provided.

    Returns:
        Raw string response from the LLM.

    Raises:
        RuntimeError: If the LLM call fails.
    """
    client = _get_groq_client()
    sys_msg = system_prompt or SYSTEM_PROMPT

    try:
        chat_completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=4096,
        )
        response_text = chat_completion.choices[0].message.content
        logger.info("Groq LLM response received successfully.")
        return response_text
    except Exception as exc:
        logger.error("Groq LLM call failed: %s", exc)
        raise RuntimeError(f"LLM generation failed: {exc}") from exc
