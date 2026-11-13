import os, sys, shutil
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def tmpdata(tmp_path):
    """진짜 data/ 대신 임시 사본을 쓴다 (실제 기록 보호)."""
    for f in ["orders.csv", "etd_changes.csv", "change_log.csv", "carrier_demo.json"]:
        shutil.copy(os.path.join(ROOT, "data", f), tmp_path / f)
    return tmp_path
