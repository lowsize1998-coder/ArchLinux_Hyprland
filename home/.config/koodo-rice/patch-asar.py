#!/usr/bin/env python3
"""Attach the local theme hook, retaining the untouched upstream ASAR."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys

MARKER = b"// Symphony Koodo local hook\n"


def read_header(handle):
    prefix = handle.read(16)
    if len(prefix) != 16:
        raise ValueError("Truncated ASAR")
    size_payload, header_size, payload_size, json_size = struct.unpack("<IIII", prefix)
    if size_payload != 4 or header_size != payload_size + 4 or json_size > header_size - 8:
        raise ValueError("Invalid ASAR header")
    if header_size > 128 * 1024 * 1024:
        raise ValueError("Unexpectedly large ASAR header")
    header = json.loads(handle.read(json_size))
    return header, 8 + header_size


def entries(tree, prefix=""):
    for name, entry in tree["files"].items():
        path = f"{prefix}/{name}" if prefix else name
        if "files" in entry:
            yield from entries(entry, path)
        elif "offset" in entry and not entry.get("unpacked"):
            yield path, entry


def patch(archive):
    backup = archive.with_name("app.asar.upstream")
    source = backup if backup.exists() else archive
    temporary = archive.with_name("app.asar.rice-tmp")
    with source.open("rb") as upstream:
        header, data_start = read_header(upstream)
        files = list(entries(header))
        lookup = dict(files)
        package = lookup["package.json"]
        upstream.seek(data_start + int(package["offset"]))
        metadata = json.loads(upstream.read(package["size"]))
        if metadata.get("type") == "module":
            raise ValueError("This installer requires a CommonJS Koodo entry point")
        main = metadata.get("main", "index.js").removeprefix("./")
        entry = lookup[main]
        upstream.seek(data_start + int(entry["offset"]))
        original = upstream.read(entry["size"])
        if original.startswith(b"#!"):
            raise ValueError("Unexpected shebang in Koodo entry point")
        addition = MARKER + (
            b"try { if (process.env.KOODO_RICE_DIR) require(process.env.KOODO_RICE_DIR + '/electron-hook.cjs'); }"
            b" catch (error) { console.error('[Koodo rice]', error.message); }\n"
        )
        directive = re.match(rb"\s*(?:(?://[^\n]*\n|/\*[\s\S]*?\*/)\s*)*['\"]use strict['\"];", original)
        position = directive.end() if directive else 0
        modified = original[:position] + b"\n" + addition + original[position:]
        sources = []
        offset = 0
        for name, file in files:
            sources.append((name, int(file["offset"]), file["size"]))
            file["offset"] = str(offset)
            if name == main:
                file["size"] = len(modified)
                if "integrity" in file:
                    block = int(file["integrity"].get("blockSize", 4 * 1024 * 1024))
                    if block < 1:
                        raise ValueError("Invalid ASAR integrity block size")
                    file["integrity"] = {
                        "algorithm": "SHA256", "hash": hashlib.sha256(modified).hexdigest(),
                        "blockSize": block,
                        "blocks": [hashlib.sha256(modified[i:i+block]).hexdigest() for i in range(0, len(modified), block)],
                    }
            offset += file["size"]
        raw = json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode()
        payload = struct.pack("<I", len(raw)) + raw
        payload += b"\0" * (-len(payload) % 4)
        packed_header = struct.pack("<I", len(payload)) + payload
        try:
            with temporary.open("wb") as output:
                output.write(struct.pack("<II", 4, len(packed_header)))
                output.write(packed_header)
                for name, old_offset, size in sources:
                    if name == main:
                        output.write(modified)
                    else:
                        upstream.seek(data_start + old_offset)
                        remaining = size
                        while remaining:
                            chunk = upstream.read(min(1024 * 1024, remaining))
                            if not chunk:
                                raise ValueError(f"Truncated ASAR file: {name}")
                            output.write(chunk)
                            remaining -= len(chunk)
            if not backup.exists():
                shutil.copy2(archive, backup)
            os.chmod(temporary, archive.stat().st_mode & 0o777)
            os.replace(temporary, archive)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    patch(Path(sys.argv[1]))
