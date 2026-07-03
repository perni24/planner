import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import APP_VERSION, GITHUB_LATEST_RELEASE_API, GITHUB_RELEASES_URL


def normalize_version(version):
    return version.removeprefix("v")


def parse_version(version):
    return tuple(int(part) for part in normalize_version(version).split("."))


def is_newer_version(latest_version, current_version):
    return parse_version(latest_version) > parse_version(current_version)


def get_latest_release():
    request = Request(
        GITHUB_LATEST_RELEASE_API,
        headers={"Accept": "application/vnd.github+json"},
    )

    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def check_update():
    try:
        latest_release = get_latest_release()
        latest_version = normalize_version(latest_release["tag_name"])
        release_url = latest_release.get("html_url", GITHUB_RELEASES_URL)

        return {
            "current_version": APP_VERSION,
            "latest_version": latest_version,
            "update_available": is_newer_version(latest_version, APP_VERSION),
            "release_url": release_url,
            "error": None,
        }
    except (HTTPError, URLError, KeyError, ValueError):
        return {
            "current_version": APP_VERSION,
            "latest_version": None,
            "update_available": False,
            "release_url": GITHUB_RELEASES_URL,
            "error": "Impossibile controllare aggiornamenti",
        }
