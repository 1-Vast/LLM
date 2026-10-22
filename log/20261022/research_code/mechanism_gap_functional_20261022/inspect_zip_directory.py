"""Read ZIP directory headers with HTTP ranges; never decompress payloads."""
from datetime import datetime, timezone
import hashlib
import json
import struct
import sys
import urllib.request

from search_sources import BASE


def get_range(url, start, end, label, receipts):
    rec = {"url": url, "utc": datetime.now(timezone.utc).isoformat(),
           "range": f"bytes={start}-{end}"}
    req = urllib.request.Request(url, headers={"Range": rec["range"],
        "User-Agent": "MAESTRO archive directory-only audit"})
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            rec["status"] = response.status
            rec["content_range"] = response.headers.get("Content-Range")
            if response.status != 206:
                raise ValueError("Range ignored: payload not read")
            data = response.read(end - start + 2)
        if len(data) != end - start + 1:
            raise ValueError("Unexpected range length")
        rec.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        (BASE / f"{label}.bin").write_bytes(data)
    except Exception as exc:
        rec["error"] = repr(exc)
        data = None
    receipts.append(rec)
    (BASE / f"{label}.receipt.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    accession, filename, label = sys.argv[1:]
    meta = json.loads((BASE / f"figshare_{accession}.metadata.json").read_bytes())
    entry = next(x for x in meta["files"] if x["name"] == filename)
    size, url = entry["size"], entry["download_url"]
    receipts = []
    start = size - 22
    tail = get_range(url, start, size-1, label + ".zip_tail", receipts)
    names = []
    if tail is not None:
        index = tail.find(b"PK\x05\x06")
        if index < 0:
            raise ValueError("No comment-free end directory record; stop")
        record = struct.unpack_from("<4s4H2LH", tail, index)
        directory_size, directory_offset = record[5:7]
        if directory_offset == 0xFFFFFFFF:
            locator = get_range(url, size-42, size-23, label + ".zip64_locator", receipts)
            locator_record = struct.unpack("<4sLQL", locator)
            if locator_record[0] != b"PK\x06\x07":
                raise ValueError("Missing ZIP64 locator")
            zip64_offset = locator_record[2]
            zip64 = get_range(url, zip64_offset, zip64_offset+55,
                              label + ".zip64_end", receipts)
            zip64_record = struct.unpack("<4sQ2H2L4Q", zip64)
            if zip64_record[0] != b"PK\x06\x06":
                raise ValueError("Missing ZIP64 end record")
            directory_size, directory_offset = zip64_record[8:10]
        if directory_size > 2_000_000:
            raise ValueError("Directory exceeds audit cap")
        if directory_offset >= start:
            directory = tail[directory_offset-start:directory_offset-start+directory_size]
        else:
            directory = get_range(url, directory_offset, directory_offset+directory_size-1,
                                  label + ".zip_directory", receipts)
        offset = 0
        if directory is not None:
            while offset < len(directory):
                header = struct.unpack_from("<4s6H3L5H2L", directory, offset)
                if header[0] != b"PK\x01\x02":
                    raise ValueError("Not a central directory header")
                length, extra, comment = header[10:13]
                name = directory[offset+46:offset+46+length].decode("utf-8")
                names.append(name)
                offset += 46 + length + extra + comment
    (BASE / f"{label}.ZIP_DIRECTORY_RECEIPTS.json").write_text(
        json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    (BASE / f"{label}.zip_names.json").write_text(
        json.dumps(names, indent=2) + "\n", encoding="utf-8")
    exposed = [x for x in names if not x.startswith("__MACOSX")]
    print(json.dumps({"receipts": receipts, "name_count": len(exposed),
                      "names": exposed[:80]}, indent=2))
