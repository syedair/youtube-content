"""Namespaces shared by every step."""
from rdflib import Namespace

FAM = Namespace("https://family.example/id/")
CN = Namespace("https://data.cloudnova.example/")


def short(term) -> "str | None":
    """fam: prefixed form of a fam IRI, or None for anything else."""
    s = str(term)
    return "fam:" + s[len(FAM):] if s.startswith(str(FAM)) else None
