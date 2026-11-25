"""Offline validation of the immutable November 9 research basis."""
import hashlib
import json


def scope_hash(entities, ids):
    """Hash only the entities of the snapshot's studies; later catalog growth must not change it."""
    ids = set(ids)
    subset = {
        "studies": sorted((s for s in entities["studies"] if s["id"] in ids), key=lambda r: r["id"]),
        "versions": sorted((v for v in entities["versions"] if v["study_id"] in ids), key=lambda r: r["id"]),
        "reviews": sorted((r for r in entities["reviews"] if ids & set(r["study_ids"])), key=lambda r: r["id"]),
        "assessments": sorted((a for a in entities["assessments"] if a["study_id"] in ids), key=lambda r: r["id"]),
        "current_assessments": sorted((c for c in entities["current_assessments"] if c["study_id"] in ids), key=lambda r: (r["study_id"], r["project_id"])),
    }
    encoded = json.dumps(subset, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()



def load_basis(root, ids):
    directory = root / "data/results/research-portfolio"
    manifest = json.loads((directory / "2026-11-09-basis-manifest.json").read_bytes())
    raw = (directory / "2026-11-09-basis-entities.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest["historical_entities_file_sha256"], "Frozen entities file hash mismatch"
    historical = json.loads(raw)
    assert scope_hash(historical, ids) == manifest["scope_entities_sha256"], "Frozen entities scope hash mismatch"

    live = json.loads((root / "catalog/entities.json").read_bytes())
    ids = set(ids)
    live_studies = {record["id"] for record in live["studies"]}
    assert ids <= live_studies, "Historical study missing from current catalog"
    for key, in_scope in (
        ("versions", lambda record: record["study_id"] in ids),
        ("reviews", lambda record: bool(ids.intersection(record["study_ids"]))),
        ("assessments", lambda record: record["study_id"] in ids),
    ):
        current = {record["id"]: record for record in live[key]}
        for record in historical[key]:
            if in_scope(record):
                assert current.get(record["id"]) == record, f"Historical {key} record changed: {record['id']}"
    return manifest, historical
