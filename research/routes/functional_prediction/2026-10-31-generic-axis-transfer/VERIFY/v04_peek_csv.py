"""Print the layout of a CSV file: header, first rows (truncated) and row count."""
import sys

path = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
with open(path, "r", encoding="utf-8", newline="") as f:
    header = f.readline()
    cols = header.rstrip("\r\n").split(",")
    print("n columns (naive split):", len(cols))
    print("header first 12:", cols[:12])
    print("header last 5:", cols[-5:])
    rows = 0
    for i, line in enumerate(f):
        rows += 1
        if i < n:
            parts = line.rstrip("\r\n").split(",")
            print(f"row {i}: {len(parts)} fields; first 8: {parts[:8]}")
    print("data rows:", rows)
    print("line ending CRLF:", header.endswith("\r\n"))
