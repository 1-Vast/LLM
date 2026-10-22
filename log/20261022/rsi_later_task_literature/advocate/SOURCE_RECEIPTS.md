# Source receipts index

Six distinct primary works. Obsolete DGM v1 and SEAL v1 bodies are retained, but the review cites current v3/v2. Discovery records are not primary scientific evidence.

| Work | Version date | Public primary URL | HTTP status | Bytes | Body SHA256 |
|---|---|---|---:|---:|---|
| DGM | 2026-03-12 (v3); original 2025-05-29 | https://arxiv.org/html/2505.22954v3 | 200 | 2892188 | `60fa9a4060472faf5a7078da45b32011d234cab7f892c508018127732a5d195c` |
| AlphaEvolve | 2025-06-16 v1 | https://arxiv.org/html/2506.13131v1 | 200 | 815580 | `eccec3409ca6f57f1fd28f8fec27f024af7eb4b96cd1f6254ab1084b55955d4e` |
| ShinkaEvolve | 2025-09-17 v1 | https://arxiv.org/html/2509.19349v1 | 200 | 3231759 | `cae18c51c8aba976b10f0fc418e62df2ee06f3bab1693b4d3240194d9ba3694f` |
| SEAL | 2025-09-18 (v2); original 2025-06-12 | https://arxiv.org/html/2506.10943v2 | 200 | 296626 | `500d55d512bffe41e7b48c54ca8418a1437c6cc67b52c50e737a99a5716b6dfa` |
| MaD-RSI | 2026-10-20 v1 | https://arxiv.org/html/2610.28201v1 | 200 | 150402 | `8203db23179031aa5e65596712cb5fd4dae0789cdaae6949922b9cacf56247f5` |
| Audit | 2026-10-20 v1 | https://arxiv.org/html/2610.27610v1 | 200 | 874154 | `d77885addb159a276969cd7b8bc9291606d5ef313d728baf096c22fa708117c9` |

Every raw body and parsed text is in this directory. Exact UTC GET times, final URLs, content types and relative body paths are in SOURCE_RECEIPTS.json and the append-only SOURCE_RECEIPTS.jsonl.

Discovery: arXiv query for 2026 self-improving papers (20 returned records), arXiv version metadata for these six IDs, broad OpenAlex query (no evidence claims based on it), GitHub repository search (no substantive repo reviewed), and a Google request that returned challenge/script content (not usable search evidence). The initial two parser failures and superseded bodies are documented in WORK_AND_FAILURES.md.
