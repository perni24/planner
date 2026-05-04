import json
import os
import re

from config import LOCALES_DIR

LANGUAGE_RE = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")

def is_valid_language(language):
    return bool(LANGUAGE_RE.match(language))

def get_available_languages():
    if not os.path.exists(LOCALES_DIR):
        return []

    languages = []

    for filename in os.listdir(LOCALES_DIR):
        if filename.endswith(".json"):
            language = filename[:-5]

            if is_valid_language(language):
                languages.append(language)

    return sorted(languages)

def get_locale_path(language):
    if not is_valid_language(language):
        raise ValueError("Lingua non valida")

    return os.path.join(LOCALES_DIR, f"{language}.json")


def load_language(language):
    path = get_locale_path(language)

    if not os.path.exists(path):
        raise FileNotFoundError("Lingua non trovata")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)