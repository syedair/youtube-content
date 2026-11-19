"""Episode 1: scattered facts. One grandma, five names, zero exact matches.
Then the fix, on Cloudnova's customer Acme Health: a who-is-who table gives its five names one ID.
The same fix works on Grandma's five names (section family-id)."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.io import number, sections, verdict  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "carter"
CLOUDNOVA = Path(__file__).resolve().parent.parent / "data" / "cloudnova"

# What each of Cloudnova's five systems calls its customer Acme Health (the CRM, billing, the consulting team's
# sheet and the SOW PDF spell it as in data/cloudnova/acme-names.csv, episode 6; the email thread says "the hospital").
ACME = [
    ("CRM", "Acme Health Inc."),
    ("consulting sheet", "Acme"),
    ("billing", "ACME-HLTH"),
    ("SOW PDF", "ACME Health"),
    ("email", "the hospital"),
]


def load():
    chat = json.loads((DATA / "family-chat.json").read_text(encoding="utf-8"))
    with open(DATA / "dad-spreadsheet.csv", encoding="utf-8", newline="") as f:
        sheet = list(csv.DictReader(f))
    passport = dict(
        line.split(": ", 1)
        for line in (DATA / "passport.txt").read_text(encoding="utf-8").splitlines()
        if ": " in line
    )
    with open(DATA / "census-1951.csv", encoding="utf-8", newline="") as f:
        census = list(csv.DictReader(f))
    album = json.loads((DATA / "photo-album.json").read_text(encoding="utf-8"))
    # (source, field, value) for the one person all five records are about
    return [
        ("Family group chat", "contact name", chat["members"][0]["contact name"]),
        ("Dad's spreadsheet", "name", sheet[0]["name"]),
        ("Her passport", "surname, given",
         f'{passport["surname"]}, {passport["given"]}'),
        ("1951 census", "name", census[0]["name"]),
        ("Maya's photo album", "caption", album["photos"][0]["caption"]),
    ]


def verdict_join(n_names: int, n_pairs: int):
    """What the exact-name join means, from its counts."""
    if n_pairs == 0:
        return False, f"The computer finds no match: {number(n_names)} names, zero links."
    pairs = "pair" if n_pairs == 1 else "pairs"
    return None, f"The computer links {number(n_pairs)} {pairs} of names, by exact spelling."


def who_is_who():
    """(source, name) -> ID: the hand-made table that says which real person each source's name means."""
    with open(DATA / "who-is-who.csv", encoding="utf-8", newline="") as f:
        return {(r["source"], r["name"]): r["id"] for r in csv.DictReader(f)}


def verdict_one_id(n_names: int, ids: set, thing: str = "person", one: str = "one grandma"):
    """What the lookup means: one ID for every name, or not yet."""
    if len(ids) == 1 and None not in ids:
        return True, f"{number(n_names).capitalize()} names, one ID: the computer now sees one {thing}."
    if None in ids:
        return False, "Some names are missing from who-is-who.csv: no ID, no link."
    return False, f"{number(len(ids)).capitalize()} IDs for {one}: the table needs fixing."


def main():
    """Run every section in order, or the ones named with --only. The sources, the naive join and the one-ID
    lookup are their own short files, each runnable by itself: sources.py, exact_match.py and lookup.py (they
    import from this file)."""
    from ep01_context import exact_match, lookup, sources

    only = sections(["sources", "naive-join", "one-id", "family-id"])
    records = load()
    if only is None:
        print("One grandma. Five names.\n")
    if only is None or "sources" in only:
        sources.main()
        print()
    if only is None or "naive-join" in only:
        exact_match.main()
    gap = only is None or "naive-join" in only
    if only is None or "one-id" in only:
        if gap:
            print()
        lookup.main()
        gap = True
    if only is None or "family-id" in only:
        if gap:
            print()
        family_id(records)


def family_id(records):
    """The same fix on Grandma's five names: data/carter/who-is-who.csv."""
    table = who_is_who()
    print("== family ID: the same fix for Grandma's five names ==")
    ids = set()
    for src, _field, name in sorted(records):
        rid = table.get((src, name))
        ids.add(rid)
        quoted = f'"{name}"'
        print(f"{src:<20} {quoted:<15} → {rid or '(no ID)'}")
    print(f"distinct people: {len({i for i in ids if i})}")
    verdict(*verdict_one_id(len(records), ids))


if __name__ == "__main__":
    main()
