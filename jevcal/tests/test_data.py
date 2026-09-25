from pathlib import Path

import pytest

from jevcal.data import load_banking77, load_clinc

DATA = Path(__file__).resolve().parent.parent / "data"
needs_b77 = pytest.mark.skipif(not (DATA / "test.csv").exists(), reason="download BANKING77 into data/ first")
needs_clinc = pytest.mark.skipif(not (DATA / "data_full.json").exists(), reason="download CLINC150 into data/ first")


@needs_b77
def test_banking77_test_matches_preregistration():
    items, labels = load_banking77(DATA, "test")
    assert len(items) == 3080 and len(labels) == 77


@needs_clinc
def test_clinc_oos_size():
    assert len(load_clinc(DATA)["oos_test"]) == 1000


def test_tampered_file_is_rejected(tmp_path):
    (tmp_path / "test.csv").write_text("text,category\nhi,x\n")
    with pytest.raises(ValueError):
        load_banking77(tmp_path, "test")
