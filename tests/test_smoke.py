from pathlib import Path

def test_project_structure():
    root=Path(__file__).resolve().parents[1]
    assert (root/"run.py").exists()
    assert (root/"requirements.txt").exists()
    assert (root/"templates/dashboard.html").exists()
    assert (root/"app/services.py").exists()
