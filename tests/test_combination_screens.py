"""Synthetic ALMANAC release validates sealed vault, immutable pins and dataset construction."""
from __future__ import annotations

import json
import zipfile

import numpy as np
import pytest

from tools.datasets import combination_screens as screens


def _fake_release(path):
    header = ("COMBODRUGSEQ,SCREENER,STUDY,TESTDATE,PLATE,PANELNBR,CELLNBR,PREFIX1,NSC1,SAMPLE1,CONCINDEX1,CONC1,"
              "CONCUNIT1,PREFIX2,NSC2,SAMPLE2,CONCINDEX2,CONC2,CONCUNIT2,PERCENTGROWTH,PERCENTGROWTHNOTZ,TESTVALUE,"
              "CONTROLVALUE,TZVALUE,EXPECTEDGROWTH,SCORE,VALID,PANEL,CELLNAME")
    rows, seq = [header], 0
    for cell in ("A", "B"):
        for d1, d2 in ((740, 750), (740, 752), (750, 752)):
            for i in (1, 2, 3):
                for j in (1, 2, 3):
                    seq += 1
                    score = 15.0 if (d1, d2, cell) == (740, 750, "A") else 1.0
                    rows.append(f"{seq},FG,s,d,p,1,1,S,{d1},1,{i},{i}e-6,M,S,{d2},1,{j},{j}e-6,M,40,40,1,1,1,55,{score},Y,P,{cell} ")
        for d in (740, 750, 752):
            seq += 1
            rows.append(f"{seq},FG,s,d,p,1,1,S,{d},1,1,1e-6,M,S,,,0,,,60,60,1,1,1,,,Y,P,{cell} ")
        seq += 1
        rows.append(f"{seq},FG,s,d,p,1,1,S,740,1,0,1e-6,M,S,,,0,,,0,0,1,1,1,,,Y,P,{cell} ")   # undocumented pattern
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ComboDrugGrowth_Nov2017.csv", "\n".join(rows) + "\n")


def test_almanac_builder_and_vault(tmp_path):
    source = tmp_path / "release.zip"
    _fake_release(source)
    with pytest.raises(screens.VaultRefusal) as sealed:
        screens.build_almanac({}, source=source)
    assert sealed.value.code == "VAULT_SEALED"
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("v1")
    freeze = tmp_path / "freeze.json"
    freeze.write_text(json.dumps({"files": {"frozen.txt": screens.sha256(frozen)}}))
    ticket = screens.open_vault(freeze, tmp_path / "vault.jsonl", purpose="t", source=source, root=tmp_path)
    frozen.write_text("v2")
    with pytest.raises(screens.VaultRefusal) as changed:
        screens.open_vault(freeze, tmp_path / "vault.jsonl", purpose="t", source=source, root=tmp_path)
    assert changed.value.code == "FREEZE_MISMATCH"
    names = tmp_path / "names.txt"
    names.write_text("740\tMethotrexate\n750\tBusulfan\n752\tThioguanine\n752\t6-Thioguanine\n")
    library = screens.build_almanac(ticket, source=source, names_path=names)
    assert library.screen.drugs == ("Methotrexate", "Busulfan", "Thioguanine")
    assert int(library.hits.sum()) == 1 and np.all(library.cost_points == 9)
    assert library.provenance["excluded_undocumented_rows"] == 2
    assert np.allclose(library.screen.mono_mean, 0.4)
    screens.save_library(library, tmp_path / "lib.npz")
    again = screens.load_library(tmp_path / "lib.npz")
    assert np.array_equal(again.screen.y, library.screen.y) and again.days_per_round == 3.0
