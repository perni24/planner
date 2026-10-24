import json
import os
import re
from db.repositories.setting_repo import get_current_language
from config import DEFAULT_LOCALES_DIR, LOCALES_DIR


LANGUAGE_RE = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")

def is_valid_language(language):
    return isinstance(language, str) and bool(LANGUAGE_RE.fullmatch(language))

def get_available_languages():
    try:
        filenames = os.listdir(LOCALES_DIR)
    except OSError:
        return []

    languages = []

    for filename in filenames:
        if filename.endswith(".json"):
            language = filename[:-5]

            if is_valid_language(language):
                try:
                    load_dictionary(language)
                except (OSError, ValueError):
                    continue
                languages.append(language)

    return sorted(languages)

def get_locale_path(language, directory=None):
    if not is_valid_language(language):
        raise ValueError("Invalid language code")

    return os.path.join(LOCALES_DIR if directory is None else directory, f"{language}.json")


def load_dictionary(language, directory=None):
    with open(get_locale_path(language, directory), "r", encoding="utf-8") as file:
        dictionary = json.load(file)

    if not isinstance(dictionary, dict) or not dictionary or not all(
        isinstance(key, str) and key and isinstance(value, str)
        for key, value in dictionary.items()
    ):
        raise ValueError("Language dictionary must be a non-empty JSON object of strings")

    return dictionary


def load_language():
    language = get_current_language()
    tried = set()

    # Il fallback e solo in lettura: conserva scelta nel DB e file dell'utente.
    for candidate in (language, "it", "en"):
        if not is_valid_language(candidate):
            continue
        for directory in (LOCALES_DIR, DEFAULT_LOCALES_DIR):
            path = get_locale_path(candidate, directory)
            if path in tried:
                continue
            tried.add(path)
            try:
                return load_dictionary(candidate, directory)
            except (OSError, ValueError):
                continue

    raise FileNotFoundError("No usable language dictionary is available")
