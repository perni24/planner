import re

from services.locale_service import is_valid_language, load_dictionary


ALLOWED_THEMES = ("light", "dark", "system", "custom")
COLOR_KEYS = ("background", "foreground", "card", "border", "hover", "hoverText")
COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")


def validate_language_settings(data):
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    language = data.get("language")
    if not is_valid_language(language):
        return None, "language must be a valid language code, such as it or pt-BR"

    try:
        load_dictionary(language)
    except (OSError, ValueError):
        return None, "language dictionary is unavailable or invalid"

    return {"language": language}, None


def validate_theme_settings(data):
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    theme = data.get("theme")
    if not isinstance(theme, str) or theme not in ALLOWED_THEMES:
        return None, "theme must be one of: light, dark, system, custom"

    colors = data.get("custom_colors")
    if not isinstance(colors, dict):
        return None, "custom_colors must be a JSON object"

    if set(colors) != set(COLOR_KEYS):
        return None, "custom_colors must contain exactly: " + ", ".join(COLOR_KEYS)

    for key in COLOR_KEYS:
        value = colors[key]
        if not isinstance(value, str) or not COLOR_RE.fullmatch(value):
            return None, f"custom_colors.{key} must be a color in #RRGGBB format"

    return {"theme": theme, "custom_colors": {key: colors[key] for key in COLOR_KEYS}}, None
