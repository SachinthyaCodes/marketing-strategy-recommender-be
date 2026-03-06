from supabase import Client, create_client

from app.config.settings import get_settings


def get_supabase_client() -> Client:
    """Create and return a Supabase client instance.

    Uses application settings to configure the connection.
    The client is lightweight and safe to re-create per request,
    but callers may cache it if desired.

    Returns:
        Supabase Client instance.

    Raises:
        Exception: If connection to Supabase fails.
    """
    settings = get_settings()
    try:
        client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return client
    except Exception as exc:
        raise ConnectionError(
            f"Failed to connect to Supabase: {exc}"
        ) from exc
