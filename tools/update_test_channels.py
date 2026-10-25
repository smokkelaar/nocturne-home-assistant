"""Keep isolated HA test identities with independently pinned sources."""
import argparse
import json
from datetime import datetime
import re
from pathlib import Path

import update_personal
import personal_maintenance
from versioning import publication_mode

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate_test_pr_source(source, channel="Test B"):
    if source.get("channel") == "personal-pr":
        pr = source.get("pull_request")
        if (channel not in ("Test A", "Test B") or source.get("repository") != update_personal.REPO or
                type(pr) is not int or pr <= 0 or
                source.get("pull_request_url") != f"https://github.com/{update_personal.REPO}/pull/{pr}" or
                not re.fullmatch(r"[0-9a-f]{64}", source.get("archive_sha256", ""))):
            raise ValueError(f"Invalid {channel} Personal PR source")
        for field in ("commit", "base_commit"):
            if not re.fullmatch(r"[0-9a-f]{40}", source.get(field, "")):
                raise ValueError(f"Invalid {channel} Personal PR commit")
        for field in ("commit_at", "base_commit_at"):
            stamp = datetime.fromisoformat(source.get(field, "").replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError(f"{channel} Personal PR timestamps must include a timezone")
        return
    if source.get("channel") == "personal":
        personal = read("upstream-personal.json")
        if source != personal:
            raise ValueError(f"{channel} must use the exact approved Personal source")
        return
    if source.get("channel") == "main":
        latest = read("upstream-latest.json")
        if (source.get("repository") != update_personal.REPO or
                source.get("commit") != latest["commit"] or
                source.get("base_commit") != latest["commit"] or
                source.get("commit_at") != latest["commit_at"] or
                source.get("base_commit_at") != latest["commit_at"] or
                not re.fullmatch(r"[0-9a-f]{64}", source.get("archive_sha256", "")) or
                "pull_request" in source or "pull_request_url" in source):
            raise ValueError(f"Invalid {channel} main baseline")
        return
    pr = source.get("pull_request")
    if (source.get("channel") != "test-pr" or
            source.get("repository") != update_personal.REPO or
            type(pr) is not int or pr <= 0 or
            source.get("pull_request_url") != f"https://github.com/nightscout/nocturne/pull/{pr}"):
        raise ValueError(f"Unexpected {channel} PR source")
    for field in ("commit", "base_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", source.get(field, "")):
            raise ValueError(f"Invalid {channel} commit")
    if not re.fullmatch(r"[0-9a-f]{64}", source.get("archive_sha256", "")):
        raise ValueError(f"Invalid {channel} archive checksum")
    for field in ("commit_at", "base_commit_at"):
        stamp = datetime.fromisoformat(source.get(field, "").replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError(f"{channel} timestamps must include a timezone")


def validate_test_b_source(source):
    validate_test_pr_source(source, "Test B")


def files():
    personal = read("upstream-personal.json")
    latest = read("upstream-latest.json")
    test_b = read("upstream-test-b.json")
    test_a = read("upstream-test-a.json")
    test_c = read("upstream-test-c.json")
    if personal["upstream"] != latest:
        raise ValueError("All development channels must use the approved Latest base")
    validate_test_b_source(test_b)
    if test_a.get("channel") in ("main", "personal", "personal-pr"):
        validate_test_pr_source(test_a, "Test A")
    validate_test_pr_source(test_c, "Test C")
    generated = {}
    for letter, port, source in (("a", 8451, test_a), ("b", 8452, test_b), ("c", 8453, test_c)):
        package = "nocturne_test_" + letter
        for path in ("rootfs/opt/nocturne-ha/diagnostic_cli.py",
                     "rootfs/usr/local/bin/nocturne-ha"):
            generated[package + "/" + path] = (ROOT / "nocturne_latest" / path).read_bytes()
        # Keep per-channel gateway migration/logging choices, but own this common
        # metadata helper so a later source update cannot restore the old date bug.
        latest_settings = (ROOT / "nocturne_latest/rootfs/opt/nocturne-ha/settings.py").read_text(encoding="utf-8")
        helper = latest_settings[latest_settings.index("def api_build_metadata("):latest_settings.index("def service_environments(")]
        settings_path = package + "/rootfs/opt/nocturne-ha/settings.py"
        settings = (ROOT / settings_path).read_text(encoding="utf-8")
        if not re.search(r"(?m)^import os$", settings):
            settings = settings.replace("import json\n", "import json\nimport os\n")
        if "def api_build_metadata(" in settings:
            settings = re.sub(r"(?s)def api_build_metadata\(.*?(?=def service_environments\()", helper, settings)
        else:
            settings = settings.replace("def service_environments(", helper + "def service_environments(", 1)
        settings = settings.replace("api.update(GIT_COMMIT=versions['source_commit'], BUILD_DATE=versions['source_at'])",
                                    "api.update(api_build_metadata(versions))")
        generated[settings_path] = settings
        config = read(package + "/config.json")
        # One visible schema for every variant; the old Test A flag is read-only migration input.
        config["options"].pop("verify_native_auth", None)
        config["schema"].pop("verify_native_auth", None)
        config["options"]["skip_gateway_check"] = False
        config["schema"]["skip_gateway_check"] = "bool"
        version = config["version"]
        name = "Nocturne Test " + letter.upper()
        if letter in ("a", "b", "c"):
            if letter == "a" and source.get("channel") not in ("main", "personal", "personal-pr"):
                raise ValueError("Unexpected Test A source")
            source_lock = {**personal, "commit": source["commit"],
                           "commit_at": source["commit_at"],
                           "archive_sha256": source["archive_sha256"],
                           "upstream": source["upstream"] if source.get("channel") == "personal" else
                               {**latest, "commit": source["base_commit"],
                                "commit_at": source["base_commit_at"]}}
            recipe = update_personal.files(source_lock, personal["version"] + "-p1", maintenance=False)["Dockerfile"].decode()
        else:
            recipe = (ROOT / "nocturne_personal" / "Dockerfile").read_text(encoding="utf-8")
        recipe = recipe.replace("Nocturne Personal Release", name).replace("Nocturne Latest Release", name)
        if letter == "a" and source.get("channel") != "personal":
            recipe = recipe.replace("checksum-verified Personal source", "checksum-verified Google Health source")
        recipe = re.sub(r"ARG BUILD_VERSION=\S+", "ARG BUILD_VERSION=" + version, recipe)
        generated[package + "/Dockerfile"] = recipe
        parent = "nocturne_latest"
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
        if source.get("channel") == "personal":
            label = "Personal " + personal["version"]
            purpose = "Dezelfde bijgewerkte Personal-bron testen met een eigen database en sessie."
            description = label + " · main " + base_commit[:7]
            runtime.update(personal=personal["version"], base="Nocturne main + Personal",
                           nocturne=label, release=label, commit_at=source["commit_at"])
            generated[package + "/README.md"] = (
                f"# {name}\n\n{label}, exact source `{source['commit']}`, "
                f"based on official Nocturne main `{base_commit}`. "
                f"Default host port {port}, separate data and cookies.\n")
            docs = (ROOT / "nocturne_latest/DOCS.md").read_text(encoding="utf-8")
            generated[package + "/DOCS.md"] = docs.replace("Nocturne Latest Release", name).replace("8449", str(port)) + (
                f"\nThis isolated channel uses the same source as Personal {personal['version']}: `{source['commit']}`.\n")
        elif source.get("channel") == "main":
            purpose = "Ongewijzigde Nocturne main testen als basis voor nieuwe ontwikkeling."
            description = f"Nocturne main {base_commit[:7]}"
            runtime.pop("personal", None)
            runtime.update(base="Nocturne main", release="Nocturne main")
            generated[package + "/README.md"] = (
                f"# {name}\n\nUnmodified upstream main `{base_commit}`, without additional PR patches. "
                f"Default host port {port}, separate data and cookies.\n\n"
                "[Installation and source baseline](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).\n")
            docs = (ROOT / "nocturne_latest/DOCS.md").read_text(encoding="utf-8")
            docs = docs.replace("Nocturne Latest Release", name).replace("8449", str(port))
            generated[package + "/DOCS.md"] = docs + f"\nThis isolated channel uses unmodified upstream main `{base_commit}`, without additional PR patches.\n"
        elif source.get("channel") == "personal-pr":
            label = f"Personal PR #{source['pull_request']}"
            purpose = source.get("purpose", "Google Health instellen via Admin testen, inclusief toegang voor uitsluitend platformbeheerders.")
            description = f"{label} {source['commit'][:7]}"
            runtime.update(personal=source.get("personal_version", personal["version"]), base="Nocturne Personal + PR",
                           nocturne=label, release=label, commit_at=source["commit_at"])
            generated[package + "/README.md"] = (
                f"# {name}\n\n{label}, exact source `{source['commit']}`. "
                f"[Review the change]({source['pull_request_url']}). "
                f"Default host port {port}, separate data and cookies.\n")
            docs = (ROOT / "nocturne_latest/DOCS.md").read_text(encoding="utf-8")
            generated[package + "/DOCS.md"] = docs.replace("Nocturne Latest Release", name).replace("8449", str(port)) + (
                f"\nThis isolated channel tests [Personal PR #{source['pull_request']}]({source['pull_request_url']}) "
                f"at `{source['commit']}`. " + source.get(
                    "docs_note", "Configure Google Health under Settings → Admin → Integrations; "
                    "its former environment settings are no longer used.") + "\n")
        elif letter == "b":
            label = f"Hypo comparison PR #{source['pull_request']}"
            purpose = "Hypo Duration en Hypo Events tussen twee periodes vergelijken, naast de bestaande hyperinformatie."
            description = f"{label} {source['commit'][:7]} · main {source['base_commit'][:7]}"
            runtime.pop("personal", None)
            runtime["base"] = f"Nocturne main + PR #{source['pull_request']}"
            runtime["nocturne"] = f"main@{source['base_commit'][:7]} + PR #{source['pull_request']}"
            runtime["release"] = label
            recipe = recipe.replace("checksum-verified Personal source", "checksum-verified hypo comparison source")
            generated[package + "/Dockerfile"] = recipe
        elif letter == "c":
            label = f"Clock face units PR #{source['pull_request']}"
            purpose = "Klokface-eenheden en tijdnotatie per face testen: dezelfde weergave voor eigenaar, andere ingelogde kijkers en publieke kloklinks."
            description = f"{label} {source['commit'][:7]} · main {source['base_commit'][:7]}"
            runtime.pop("personal", None)
            runtime["base"] = f"Nocturne main + PR #{source['pull_request']}"
            runtime["nocturne"] = f"main@{source['base_commit'][:7]} + PR #{source['pull_request']}"
            runtime["release"] = label
            recipe = recipe.replace("checksum-verified Personal source", "checksum-verified clock face units source")
            generated[package + "/Dockerfile"] = recipe
        elif letter == "a":
            purpose = f"Google Health PR #1293 testen vóór merge, op een geïsoleerde Test {letter.upper()}-instantie."
            description = f"Google Health PR #1293 {source['commit'][:7]} · main {source['base_commit'][:7]}"
            runtime.pop("personal", None)
            runtime["base"] = "Nocturne main + PR #1293"
            runtime["nocturne"] = "main@" + source["base_commit"][:7] + " + PR #1293"
            runtime["release"] = "Google Health PR #1293"
        if source.get("channel") not in ("main", "personal") and letter in ("b", "c") and source["commit"] == source["base_commit"]:
            label += " (merged into main)"
            description = f"Nocturne main {base_commit[:7]} · {label}"
            runtime.update(base="Nocturne main", nocturne="main@" + base_commit[:7], release=label)
            purpose += " De oorspronkelijke PR is gemerged; dit kanaal valideert nu de actuele main."
        runtime["release_url"] = (f"https://github.com/{source['repository']}/tree/{source['commit']}"
                                  if source.get("channel") == "personal" else
                                  source.get("pull_request_url") or f"https://github.com/nightscout/nocturne/tree/{base_commit}")
        runtime.update(purpose=purpose, purpose_url=runtime["release_url"],
                       test_plan=("Open Reports → Comparison; kies twee periodes met metingen en controleer Hypo Duration (uren), Hypo Events en het verschil. Test ook nul hypo's, een periode zonder data, wisselen van periodes en print. Laag en zeer laag binnen één episode mogen niet dubbel tellen."
                                  if letter == "b" else "Open Settings → Connectors → Google Health, autoriseer Google, test paging en herstel vanaf een datum voor steps, heart rate, weight en sleep."
                                  if letter == "a" else
                                  "Maak of reset een klokface en kies per face mg/dL of mmol/L en 12/24 uur; open de face als eigenaar, als ingelogde kijker met andere voorkeuren en via de publieke kloklink; controleer de builder-preview en dat oude faces mg/dL en 12 uur tonen."),
                       test_url="https://github.com/smokkelaar/nocturne-home-assistant")
        if source.get("channel") == "personal-pr":
            runtime["test_plan"] = source.get("test_plan", (
                "Open Settings → Admin → Integrations → Google Health als platformbeheerder. "
                "Controleer client ID, gemaskeerd secret en exacte callback-URL. Sla op en verbind Google zonder herstart. "
                "Controleer dat een gewone gebruiker en tenantbeheerder geen toegang hebben tot Admin of de instellingen-API. "
                "Lege velden moeten bestaande sleutels behouden; wisselen van client ID moet opnieuw verbinden vragen. "
                "Test uitschakelen, herstart en opnieuw inschakelen; geïmporteerde data moet behouden blijven."))
        if source.get("channel") in ("main", "personal"):
            runtime["test_plan"] = "Basiswerking, containerstart en upgrade van de bestaande testinstantie controleren."
        if not publication_mode(ROOT):
            config["description"] = f"HA wrapper {runtime['app']} · {description}. Isolated test instance; not for clinical use."
        generated[package + "/config.json"] = json.dumps(config, indent=2) + "\n"
        generated[package + "/rootfs/opt/nocturne-ha/version.json"] = json.dumps(runtime, indent=2) + "\n"
    # Overlay each isolated package, including its own runtime and translations.
    for letter in ('a', 'b', 'c'):
        package = 'nocturne_test_' + letter
        shared = ('config.json', 'Dockerfile', 'DOCS.md', 'translations/nl.json',
                  'translations/en.json', 'rootfs/opt/nocturne-ha/run.py')
        inputs = {path: generated.get(package + '/' + path,
                  (ROOT / package / path).read_bytes()) for path in shared}
        for path, data in personal_maintenance.apply(inputs).items():
            generated[package + '/' + path] = data
    return {path: data if isinstance(data, bytes) else data.encode("utf-8")
            for path, data in generated.items()}


def follow_personal():
    personal = read('upstream-personal.json')
    update_personal.validate(personal)
    data = (json.dumps(personal, indent=2) + '\n').encode('utf-8')
    for letter in 'abc':
        if read(f'upstream-test-{letter}.json').get('channel') == 'personal-pr':
            continue
        (ROOT / f'upstream-test-{letter}.json').write_bytes(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--follow-personal", action="store_true")
    args = parser.parse_args()
    if args.follow_personal:
        if not args.update:
            parser.error('--follow-personal requires --update')
        follow_personal()
    for path, expected in files().items():
        target = ROOT / path
        if args.update:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
        elif target.read_bytes() != expected:
            raise ValueError("Test channel differs from pinned source: " + path)
    print("Independently pinned Test A, Test B and Test C verified.")


if __name__ == "__main__":
    main()
