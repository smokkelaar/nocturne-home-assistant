"""Keep isolated HA test identities with independently pinned PR builds in A and B."""
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
    pr1293 = read("upstream-google-health-pr1293.json")
    test_a = read("upstream-test-a.json")
    if google["base_commit"] != latest["commit"] or personal["upstream"] != latest:
        raise ValueError("All development channels must use the approved Latest base")
    if google["repository"] != update_personal.REPO:
        raise ValueError("Unexpected Google Health repository")
    if (pr1293.get("channel") != "google-health-pr" or
            pr1293.get("repository") != update_personal.REPO or
            pr1293.get("pull_request") != 1293):
        raise ValueError("Unexpected Google Health PR source")
    for field in ("commit", "base_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", pr1293.get(field, "")):
            raise ValueError("Invalid Google Health PR commit")
    if not re.fullmatch(r"[0-9a-f]{64}", pr1293.get("archive_sha256", "")):
        raise ValueError("Invalid Google Health PR archive checksum")
    for field in ("commit_at", "base_commit_at"):
        if not pr1293.get(field):
            raise ValueError("Missing Google Health PR timestamp")
    google_lock = {**personal, "commit": google["commit"],
                   "commit_at": google["commit_at"], "archive_sha256": google["archive_sha256"]}
    google_files = update_personal.files(google_lock, personal["version"] + "-1")
    generated = {}
    for letter, port, source in (("a", 8451, test_a), ("b", 8452, pr1293), ("c", 8453, google)):
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
            if (source.get("channel") != "google-health-pr" or
                    source.get("repository") != update_personal.REPO or
                    source.get("pull_request") != 1293):
                raise ValueError("Unexpected Google Health PR source")
            source_lock = {**personal, "commit": source["commit"],
                           "commit_at": source["commit_at"],
                           "archive_sha256": source["archive_sha256"],
                           "upstream": {**latest, "commit": source["base_commit"],
                                        "commit_at": source["base_commit_at"]}}
            recipe = update_personal.files(source_lock, personal["version"] + "-1")["Dockerfile"].decode()
        elif letter == "c":
            recipe = google_files["Dockerfile"].decode()
        else:
            recipe = (ROOT / "nocturne_personal" / "Dockerfile").read_text(encoding="utf-8")
        recipe = recipe.replace("Nocturne Personal Release", name).replace("Nocturne Latest Release", name)
        if letter in ("a", "b", "c"):
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
        if letter in ("a", "b"):
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
                       test_plan=("Open Settings → Connectors → Google Health, autoriseer Google, test paging en herstel vanaf een datum voor steps, heart rate, weight en sleep."
                                  if letter in ("a", "b") else
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
    print("Test A and B=independently pinned Google Health PR #1293; Test C=Google Health verified.")


if __name__ == "__main__":
    main()
