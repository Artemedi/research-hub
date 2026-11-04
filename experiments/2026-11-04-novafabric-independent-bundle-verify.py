#!/usr/bin/env python3
"""Independent NovaFabric Evidence Bundle verifier (no novafabric import).

Checks ZIP member allowlist, manifest SHA-256, artifact digests, Ed25519 DSSE
signatures, subject hashes, the run-capsule Merkle root and members statement.
A pinned public-key fingerprint establishes continuity, not human identity.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

BUNDLE_OWN = {
    "attestations/bundle.intoto.json",
    "signatures/bundle.sig",
    "signatures/bundle.cert",
}
PREFIX = "sha256:"


def digest(data):
    return PREFIX + hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def merkle(items):
    leaves = []
    for path, data in sorted(items, key=lambda pair: pair[0].split("/")):
        name = path.encode()
        leaf = (b"\x02" + len(name).to_bytes(4, "big")
                + name + hashlib.sha256(data).digest())
        leaves.append(hashlib.sha256(leaf).digest())

    def root(values):
        if not values:
            return hashlib.sha256(b"").digest()
        if len(values) == 1:
            return values[0]
        mid = 1 << ((len(values)-1).bit_length()-1)
        return hashlib.sha256(b"\x01" + root(values[:mid]) + root(values[mid:])).digest()

    return PREFIX + root(leaves).hex()


def inspect_bundle(path, pin=None):
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names):
            raise ValueError("duplicate ZIP entries")
        if any((not name or name.endswith("/") or name.startswith("/")
                or "\\" in name or any(seg in (".", "..") for seg in name.split("/")))
               for name in names):
            raise ValueError("unsafe ZIP paths")
        present = set(names)
        if "manifest.json" not in present:
            raise ValueError("missing manifest")
        manifest = json.loads(archive.read("manifest.json"))
        mh = manifest.pop("manifest_hash")
        if digest(canonical(manifest)) != mh:
            raise ValueError("manifest hash mismatch")
        manifest["manifest_hash"] = mh

        artifacts = manifest["artifacts"]
        entries = {item["path"]: item for item in artifacts}
        if len(entries) != len(artifacts):
            raise ValueError("duplicate manifest artifacts")
        if set(entries) != present - {"manifest.json"}:
            raise ValueError("unsigned additional/missing ZIP members")
        for name, entry in entries.items():
            body = archive.read(name)
            if len(body) != entry["size_bytes"] or digest(body) != entry["sha256"]:
                raise ValueError("artifact digest/size mismatch: " + name)

        attestations = manifest["attestations"]
        refs = {x["envelope_path"]: x for x in manifest["signatures"]}
        if len(refs) != len(manifest["signatures"]):
            raise ValueError("duplicate signature references")
        statements = {}
        pubkey_fingerprints = set()
        for att in attestations:
            name = att["path"]
            signature_ref = refs[name]
            envelope = json.loads(archive.read(name))
            body = base64.b64decode(envelope["payload"], validate=True)
            kind = envelope["payloadType"].encode()
            pae = (b"DSSEv1 " + str(len(kind)).encode() + b" " + kind +
                   b" " + str(len(body)).encode() + b" " + body)
            key_pem = archive.read(signature_ref["certificate_path"])
            pubkey = serialization.load_pem_public_key(key_pem)
            if not isinstance(pubkey, Ed25519PublicKey):
                raise ValueError("wrong signing algorithm")
            pubkey_der = pubkey.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            pubkey_fingerprints.add(digest(pubkey_der))
            for signature in envelope["signatures"]:
                signed = base64.b64decode(signature["sig"], validate=True)
                if archive.read(signature_ref["signature_path"]) != signed:
                    raise ValueError("signature reference mismatch")
                pubkey.verify(signed, pae)
            statement = json.loads(body)
            statements[name] = statement
            actual_subjects = [PREFIX + x["digest"]["sha256"]
                               for x in statement["subject"]]
            if actual_subjects != att["subject_hashes"]:
                raise ValueError("subject hash mismatch: " + name)
            if statement["predicateType"] != att["predicate_type"]:
                raise ValueError("predicate type mismatch: " + name)

        if len(pubkey_fingerprints) != 1:
            raise ValueError("multiple signer public keys")
        fingerprint = next(iter(pubkey_fingerprints))
        if pin is not None and fingerprint != pin:
            raise ValueError("signer public key not pinned/trusted")

        run_members = [(name[len("run-capsule/"):], archive.read(name))
                       for name in names if name.startswith("run-capsule/")]
        assert run_members, "no run-capsule files"
        root = merkle(run_members)
        if root != manifest["subject"]["capsule_hash"]:
            raise ValueError("run capsule root mismatch")
        run_stmt = statements["attestations/run.intoto.json"]
        if root != run_stmt["predicate"]["capsule_hash"]:
            raise ValueError("run attestation root mismatch")

        redaction = json.loads(archive.read("run-capsule/redaction-proof.json"))
        red = statements["attestations/redaction.intoto.json"]
        if red["subject"][0]["digest"]["sha256"] != redaction["chain_hash"].split(":")[-1]:
            raise ValueError("redaction evidence digest mismatch")

        lin_stmt = statements["attestations/lineage.intoto.json"]
        if lin_stmt["subject"][0]["digest"]["sha256"] != hashlib.sha256(
            archive.read("lineage-subgraph/edges.jsonl")
        ).hexdigest():
            raise ValueError("lineage evidence digest mismatch")

        members_stmt = statements["attestations/bundle.intoto.json"]
        predicate = members_stmt["predicate"]
        covered = set(names) - BUNDLE_OWN - {"manifest.json"}
        member_map = predicate["members"]
        if set(member_map) != covered:
            raise ValueError("unsigned extra/missing bundle members")
        for name, hash_expected in member_map.items():
            if digest(archive.read(name)) != hash_expected:
                raise ValueError("members attestation digest mismatch: " + name)
        core = {k: v for k, v in manifest.items() if k != "manifest_hash"}
        own = BUNDLE_OWN
        core["artifacts"] = [x for x in core["artifacts"] if x["path"] not in own]
        core["attestations"] = [
            x for x in core["attestations"] if x["path"] not in own
        ]
        core["signatures"] = [
            x for x in core["signatures"] if x["envelope_path"] not in own
        ]
        if digest(canonical(core)) != predicate["manifest_core_sha256"]:
            raise ValueError("members manifest core hash mismatch")
        if digest(canonical(member_map)) != PREFIX + members_stmt["subject"][0]["digest"]["sha256"]:
            raise ValueError("members map subject digest mismatch")
        return {
            "status": "PASS",
            "archive_members": len(names),
            "artifacts_verified": len(artifacts),
            "ed25519_attestations_verified": len(attestations),
            "capsule_root": root,
            "signer_public_key_sha256": fingerprint,
            "pin_matched": pin is not None,
            "trusted_timestamp": False,
            "signer_identity": "only the public key; no independently verified owner",
            "novafabric_imported": False,
        }


def mutation_tests(path, fingerprint):
    """Fail-close checks for four modified archives and an incorrect trust pin."""
    outcomes = {}
    variants = (
        "output_data", "tool_order", "added_unsigned_file", "changed_manifest",
    )
    with tempfile.TemporaryDirectory(prefix="novafabric-independent-negative-") as td:
        for mutation in variants:
            target = Path(td) / f"{mutation}.zip"
            with ZipFile(path) as original, ZipFile(target, "w", ZIP_DEFLATED) as altered:
                for member in original.infolist():
                    data = original.read(member.filename)
                    if mutation == "output_data" and member.filename == (
                        "run-capsule/outputs/stdout.txt"
                    ):
                        data += b"CHANGED"
                    if mutation == "tool_order" and member.filename == (
                        "run-capsule/tool-calls.jsonl"
                    ):
                        lines = data.splitlines(keepends=True)
                        if len(lines) != 2:
                            raise ValueError("tool-order negative test requires two calls")
                        data = lines[1] + lines[0]
                    if mutation == "changed_manifest" and member.filename == (
                        "manifest.json"
                    ):
                        obj = json.loads(data)
                        obj["created_at"] = "2026-10-01T00:00:00Z"
                        data = json.dumps(obj).encode()
                    altered.writestr(member, data)
                if mutation == "added_unsigned_file":
                    altered.writestr("rogue-after-export.txt", "UNREGISTERED")
            try:
                inspect_bundle(target, pin=fingerprint)
            except Exception as exc:
                outcomes[mutation] = f"REJECTED:{type(exc).__name__}"
            else:
                raise AssertionError(f"tampering not rejected: {mutation}")
    try:
        inspect_bundle(path, pin="sha256:" + "0" * 64)
    except Exception as exc:
        outcomes["wrong_signer_pin"] = f"REJECTED:{type(exc).__name__}"
    else:
        raise AssertionError("incorrect signer fingerprint was accepted")
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle")
    parser.add_argument("--trusted-public-key-sha256")
    parser.add_argument("--self-test", action="store_true",
                        help="Test rejection of changed ZIP members and wrong signer pin")
    args = parser.parse_args()
    try:
        result = inspect_bundle(args.bundle, args.trusted_public_key_sha256)
        if args.self_test:
            result["negative_controls"] = mutation_tests(
                args.bundle, result["signer_public_key_sha256"]
            )
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"VERIFY_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
