"""Check 5: FREEZE.json digests of study files, built inputs and sources; MD5 and mtime of the 24Q2 matrix.

Files are hashed as opaque bytes; no content is printed. dev/ files are not hashed (out of the verifier's scope).
Writes VERIFY/check5_freeze.json.
"""
import datetime as dt
import hashlib
import json
import os

ROOT = "D:/MAESTRO/"
STUDY = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/"
OUT = STUDY + "VERIFY/check5_freeze.json"


def digests(path):
    h_raw, h_lf, h_md5 = hashlib.sha256(), hashlib.sha256(), hashlib.md5()
    n = 0
    carry = b""
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            n += len(b)
            h_raw.update(b)
            h_md5.update(b)
            # CRLF->LF across chunk boundaries: hold back a trailing CR
            buf = carry + b
            if buf.endswith(b"\r"):
                carry, buf = b"\r", buf[:-1]
            else:
                carry = b""
            h_lf.update(buf.replace(b"\r\n", b"\n"))
    if carry:
        h_lf.update(carry)
    return n, h_raw.hexdigest(), h_lf.hexdigest(), h_md5.hexdigest()


def mtime_utc(path):
    return dt.datetime.fromtimestamp(os.path.getmtime(path), tz=dt.timezone.utc)


def main():
    fr = json.load(open(STUDY + "FREEZE.json", encoding="utf-8"))
    frozen = dt.datetime.fromisoformat(fr["frozen_at_utc"])
    rows = []
    for section, base in [("study_files", STUDY), ("built_inputs", ROOT), ("sources", ROOT)]:
        for rel, rec in fr[section].items():
            path = base + rel
            row = {"section": section, "file": rel, "expected_sha256": rec.get("sha256"),
                   "expected_sha256_lf": rec.get("sha256_lf"), "expected_bytes": rec.get("bytes")}
            if not os.path.exists(path):
                row.update(exists=False, pass_=False)
                rows.append(row)
                continue
            mt = mtime_utc(path)
            row["mtime_utc"] = mt.isoformat()
            row["modified_after_freeze"] = mt > frozen
            if rec.get("sha256") is None:
                st = os.stat(path)
                row.update(exists=True, bytes=st.st_size, note=rec.get("note"),
                           expected_mtime_utc=rec.get("mtime_utc"),
                           pass_=(st.st_size == rec.get("bytes")))
                rows.append(row)
                continue
            n, d_raw, d_lf, _ = digests(path)
            exp_raw, exp_lf = rec.get("sha256"), rec.get("sha256_lf")
            raw_ok = d_raw == exp_raw
            lf_ok = exp_lf is not None and d_lf == exp_lf
            any_ok = bool({d_raw, d_lf} & {x for x in (exp_raw, exp_lf) if x})
            row.update(exists=True, bytes=n, sha256=d_raw, sha256_crlf_to_lf=d_lf, raw_match=raw_ok, lf_match=lf_ok,
                       any_match=any_ok, bytes_match=(n == rec.get("bytes")), pass_=(raw_ok or lf_ok))
            rows.append(row)

    exp = fr["sealed_outcome_expected"]
    mpath = ROOT + exp["file"]
    n, d_raw, _, d_md5 = digests(mpath)
    mt = mtime_utc(mpath)
    ct = dt.datetime.fromtimestamp(os.path.getctime(mpath), tz=dt.timezone.utc)
    matrix = {"file": exp["file"], "bytes": n, "md5": d_md5, "expected_md5": exp["md5"], "md5_match": d_md5 == exp["md5"],
              "sha256": d_raw, "mtime_utc": mt.isoformat(), "ctime_utc_windows_creation": ct.isoformat(),
              "frozen_at_utc": frozen.isoformat(), "mtime_after_freeze": mt > frozen,
              "seconds_after_freeze": (mt - frozen).total_seconds()}
    # files built after the freeze (not bound by FREEZE.json)
    extra = {}
    for rel in ["data/processed/generic_axis_transfer_20261031/prism24q2.npz"]:
        p = ROOT + rel
        n2, d2, _, _ = digests(p)
        extra[rel] = {"bytes": n2, "sha256": d2, "mtime_utc": mtime_utc(p).isoformat(), "in_freeze": False}
    for rel in ["RUN/RESULTS.json", "RUN/metrics_nci60.csv", "RUN/metrics_prism24q2.csv", "RUN/predictions_nci60.npz",
                "RUN/predictions_prism24q2.npz"]:
        p = STUDY + rel
        n2, d2, _, _ = digests(p)
        extra[rel] = {"bytes": n2, "sha256": d2, "mtime_utc": mtime_utc(p).isoformat()}

    res = {"frozen_at_utc": frozen.isoformat(), "files": rows, "matrix": matrix, "post_freeze_files": extra}
    json.dump(res, open(OUT, "w", encoding="utf-8", newline="\n"), indent=1, default=str)
    for r in rows:
        print(f"{r['section']:13s} {r['file'][-60:]:60s} pass={r['pass_']} raw={r.get('raw_match')} lf={r.get('lf_match')} "
              f"bytes_ok={r.get('bytes_match')} after_freeze={r.get('modified_after_freeze')}")
    print(json.dumps(matrix, indent=1))
    print(json.dumps(extra, indent=1))


if __name__ == "__main__":
    main()
