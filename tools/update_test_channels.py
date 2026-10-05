"""Keep isolated HA test identities with independently pinned sources."""
import argparse
import json
from datetime import datetime
import re
from pathlib import Path

import update_personal

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate_test_b_source(source):
    pr = source.get("pull_request")
    if (source.get("channel") != "test-pr" or
            source.get("repository") != update_personal.REPO or
            type(pr) is not int or pr <= 0 or
            source.get("pull_request_url") != f"https://github.com/nightscout/nocturne/pull/{pr}"):
        raise ValueError("Unexpected Test B PR source")
    for field in ("commit", "base_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", source.get(field, "")):
            raise ValueError("Invalid Test B commit")
    if not re.fullmatch(r"[0-9a-f]{64}", source.get("archive_sha256", "")):
        raise ValueError("Invalid Test B archive checksum")
    for field in ("commit_at", "base_commit_at"):
        stamp = datetime.fromisoformat(source.get(field, "").replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("Test B timestamps must include a timezone")


def files():
    personal = read("upstream-personal.json")
    latest = read("upstream-latest.json")
    google = read("upstream-google-health.json")
    test_b = read("upstream-test-b.json")
    test_a = read("upstream-test-a.json")
    if google["base_commit"] != latest["commit"] or personal["upstream"] != latest:
        raise ValueError("All development channels must use the approved Latest base")
    if google["repository"] != update_personal.REPO:
        raise ValueError("Unexpected Google Health repository")
    validate_test_b_source(test_b)
    google_lock = {**personal, "commit": google["commit"],
                   "commit_at": google["commit_at"], "archive_sha256": google["archive_sha256"]}
    google_files = update_personal.files(google_lock, personal["version"] + "-1", maintenance=False)
    generated = {}
    for letter, port, source in (("a", 8451, test_a), ("b", 8452, test_b), ("c", 8453, google)):
        package = "nocturne_test_" + letter
        config = read(package + "/config.json")
        # One visible schema for every variant; the old Test A flag is read-only migration input.
        config["options"].pop("verify_native_auth", None)
        config["schema"].pop("verify_native_auth", None)
        config["options"]["skip_gateway_check"] = False
        config["schema"]["skip_gateway_check"] = "bool"
        version = config["version"]
        name = "Nocturne Test " + letter.upper()
        if letter in ("a", "b"):
            if letter == "a" and (source.get("channel") != "google-health-pr" or
                    source.get("repository") != update_personal.REPO or
                    source.get("pull_request") != 1293):
                raise ValueError("Unexpected Google Health PR source")
            source_lock = {**personal, "commit": source["commit"],
                           "commit_at": source["commit_at"],
                           "archive_sha256": source["archive_sha256"],
                           "upstream": {**latest, "commit": source["base_commit"],
                                        "commit_at": source["base_commit_at"]}}
            recipe = update_personal.files(source_lock, personal["version"] + "-1", maintenance=False)["Dockerfile"].decode()
        elif letter == "c":
            recipe = google_files["Dockerfile"].decode()
        else:
            recipe = (ROOT / "nocturne_personal" / "Dockerfile").read_text(encoding="utf-8")
        recipe = recipe.replace("Nocturne Personal Release", name).replace("Nocturne Latest Release", name)
        if letter in ("a", "c"):
            recipe = recipe.replace("checksum-verified Personal source", "checksum-verified Google Health source")
        recipe = re.sub(r"ARG BUILD_VERSION=\S+", "ARG BUILD_VERSION=" + version, recipe)
        generated[package + "/Dockerfile"] = recipe
        parent = "nocturne_latest" if letter in ("a", "b") else "nocturne_personal"
        runtime = read(parent + "/rootfs/opt/nocturne-ha/version.json")
        base_commit = (source.get("base_commit") or source.get("upstream", {}).get("commit") or
                       latest["commit"])
        base_at = (source.get("base_commit_at") or source.get("upstream", {}).get("commit_at") or
                   latest["commit_at"])
        runtime.update(package=version, name=name, cookie_namespace="NocturneTest" + letter.upper() + "_",
                       default_public_url=f"https://homeassistant.local:{port}",
                       repository=source.get("repository", runtime.get("repository")),
                       source_commit=source["commit"], source_at=source.get("commit_at"),
                       base_commit=base_commit, commit_at=base_at,
                       nocturne="main@" + base_commit[:7])
        if letter == "b":
            label = f"A1c preferences PR #{source['pull_request']}"
            purpose = "Globale A1c/HbA1c-naam en %/mmol/mol-weergave testen; schattingen behouden de e-prefix."
            description = f"{label} {source['commit'][:7]} · main {source['base_commit'][:7]}"
            runtime.pop("personal", None)
            runtime["base"] = f"Nocturne main + PR #{source['pull_request']}"
            runtime["nocturne"] = f"main@{source['base_commit'][:7]} + PR #{source['pull_request']}"
            runtime["release"] = label
            recipe = recipe.replace("checksum-verified Personal source", "checksum-verified A1c preferences source")
            generated[package + "/Dockerfile"] = recipe
        elif letter == "a":
            purpose = f"Google Health PR #1293 testen vóór merge, op een geïsoleerde Test {letter.upper()}-instantie."
            description = f"Google Health PR #1293 {source['commit'][:7]} · main {source['base_commit'][:7]}"
            runtime.pop("personal", None)
            runtime["base"] = "Nocturne main + PR #1293"
            runtime["nocturne"] = "main@" + source["base_commit"][:7] + " + PR #1293"
            runtime["release"] = "Google Health PR #1293"
        else:
            purpose = "Google Health ontwikkelen en testen op de actuele main-basis."
            description = f"Google Health {source['commit'][:7]} · main {latest['commit'][:7]}"
            runtime.pop("personal", None)
            runtime["release"] = "Google Health development"
        runtime["release_url"] = (source.get("pull_request_url") if letter in ("a", "b") else
                                   f"https://github.com/{runtime['repository']}/tree/{source['commit']}")
        runtime.update(purpose=purpose, purpose_url=runtime["release_url"],
                       test_plan=("Open Settings → Appearance → Units & Formats; test beide namen en eenheden, e-prefix, labinvoer, rapporten en print; herlaad en controleer voorkeuren."
                                  if letter == "b" else "Open Settings → Connectors → Google Health, autoriseer Google, test paging en herstel vanaf een datum voor steps, heart rate, weight en sleep."
                                  if letter == "a" else
                                  "Start, rapporten, kanaalfuncties en sessiescheiding controleren met testgegevens."),
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
    print("Independently pinned Test A, Test B and Google Health Test C verified.")


if __name__ == "__main__":
    main()
