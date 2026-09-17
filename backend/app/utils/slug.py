import re
import unicodedata


def slugify(text: str) -> str:
    """
    Generates a deterministic URL-friendly slug from text.
    - Converts to lowercase
    - Normalizes unicode characters
    - Replaces spaces and non-alphanumeric characters with hyphens
    - Trims leading and trailing hyphens
    
    Examples:
        "Power Supply" -> "power-supply"
        "Solid State Drive" -> "solid-state-drive"
        "Intel® Core™ i9" -> "intel-core-i9"
    """
    if not text:
        return ""

    # Normalize unicode characters to ASCII equivalent
    normalized = (
        unicodedata.normalize("NFKD", str(text))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    # Convert to lowercase and strip outer whitespace
    cleaned = normalized.lower().strip()
    # Replace non-alphanumeric characters with a hyphen
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    # Replace consecutive spaces or hyphens with a single hyphen
    cleaned = re.sub(r"[-\s]+", "-", cleaned)
    # Strip any leading or trailing hyphens
    return cleaned.strip("-")
