# Small helpers if needed (e.g., safe truncation)

def safe_truncate(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit-12] + '\n\n...[truncated]'
