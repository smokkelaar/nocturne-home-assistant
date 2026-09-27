"""Keep isolated HA test identities while pinning A=Personal, B=Latest, C=Google Health."""
import argparse
import json
import re
from pathlib import Path

import update_personal

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def files():
    personal = read("upstream-personal.json")
    latest = read("upstream-latest.json")
    google = read("upstream-google-health.json")
    if google["base_commit"] != latest["commit"] or personal["upstream"] != latest:
        raise ValueError("All development channels must use the approved Latest base")
    if google["repository"] != update_personal.REPO:
        raise ValueError("Unexpected Google Health repository")
    google_lock = {**personal, "commit": google["commit"],
                   "commit_at": google["commit_at"], "archive_sha256": google["archive_sha256"]}
    google_files = update_personal.files(google_lock, personal["version"] + "-1")
    generated = {}
    for letter, port, source in (("a", 8451, personal), ("b", 8452, latest), ("c", 8453, google)):
        package = "nocturne_test_" + letter
        config = read(package + "/config.json")
        version = config["version"]
        name = "Nocturne Test " + letter.upper()
        if letter == "c":
            recipe = google_files["Dockerfile"].decode()
        else:
            parent = "nocturne_personal" if letter == "a" else "nocturne_latest"
            recipe = (ROOT / parent / "Dockerfile").read_text(encoding="utf-8")
        recipe = recipe.replace("Nocturne Personal Release", name).replace("Nocturne Latest Release", name)
        if letter == "c":
            recipe = recipe.replace("checksum-verified Personal source", "checksum-verified Google Health source")
        recipe = re.sub(r"ARG BUILD_VERSION=\S+", "ARG BUILD_VERSION=" + version, recipe)
        generated[package + "/Dockerfile"] = recipe
        parent = "nocturne_latest" if letter == "b" else "nocturne_personal"
        runtime = read(parent + "/rootfs/opt/nocturne-ha/version.json")
        runtime.update(package=version, name=name, cookie_namespace="NocturneTest" + letter.upper() + "_",
                       default_public_url=f"https://homeassistant.local:{port}",
                       source_commit=source["commit"], source_at=source.get("commit_at"),
                       base_commit=latest["commit"], commit_at=latest["commit_at"],
                       nocturne="main@" + latest["commit"][:7])
        if letter == "a":
            purpose = "Dezelfde Personal-bron als poort 8450 testen, met eigen data en sessies."
            description = f"Personal {personal['version']} · main {latest['commit'][:7]}"
        elif letter == "b":
            purpose = "Dezelfde vastgezette upstream main als Latest testen, zonder Personal-uitbreidingen."
            description = f"Latest main {latest['commit'][:7]}"
        else:
            purpose = "Google Health ontwikkelen en testen op de actuele main-basis."
            description = f"Google Health {source['commit'][:7]} · main {latest['commit'][:7]}"
            runtime.pop("personal", None)
            runtime["release"] = "Google Health development"
        runtime["release_url"] = f"https://github.com/{runtime['repository']}/tree/{source['commit']}"
        runtime.update(purpose=purpose, purpose_url=runtime["release_url"],
                       test_plan="Start, rapporten, kanaalfuncties en sessiescheiding controleren met testgegevens.",
                       test_url="https://github.com/smokkelaar/nocturne-home-assistant")
        config["description"] = f"HA wrapper {runtime['app']} · {description}. Isolated test instance; not for clinical use."
        generated[package + "/config.json"] = json.dumps(config, indent=2) + "\n"
        generated[package + "/rootfs/opt/nocturne-ha/version.json"] = json.dumps(runtime, indent=2) + "\n"
    return {path: data.encode("utf-8") for path, data in generated.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, expected in files().items():
        target = ROOT / path
        if args.update:
            target.write_bytes(expected)
        elif target.read_bytes() != expected:
            raise ValueError("Test channel differs from pinned source: " + path)
    print("Test A=Personal, Test B=Latest and Test C=Google Health verified.")


if __name__ == "__main__":
    main()
