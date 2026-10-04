"""Consumer-visible intake contracts, using real extraction and SQLite."""
import hashlib
from io import BytesIO
import socket
import sqlite3
import zipfile

from fastapi.testclient import TestClient
import pymupdf
import pytest

from independent_judge.api.app import create_app


SOURCE = "بسم الله\n\n  Original spacing stays.\r\n"
A = "Version A.\n\nA second paragraph."
B = "Version B.\n\nA different second paragraph."


def upload(client, replacement=None):
    files = {
        "source": ("original.txt", SOURCE.encode(), "text/plain"),
        "a": ("first.txt", A.encode(), "text/plain"),
        "b": ("second.md", B.encode(), "text/markdown"),
    }
    if replacement:
        files.update(replacement)
    return client.post("/api/comparisons", files=files,
                       data={"source_language": "ar", "target_language": "en"})


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(data_dir=tmp_path / "judge")) as c:
        yield c


def test_text_upload_round_trip(tmp_path):
    directory = tmp_path / "judge"
    with TestClient(create_app(data_dir=directory)) as c:
        response = upload(c)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "draft"
        assert body["source_language"] == "ar"
        assert body["target_language"] == "en"
        for role, text in {"source": SOURCE, "a": A, "b": B}.items():
            material = body["materials"][role]
            assert material["text"] == text
            assert material["sha256"] == hashlib.sha256(text.encode()).hexdigest()
            assert material["file_sha256"] == hashlib.sha256(text.encode()).hexdigest()
            assert "content" not in material
    # Persist across service restarts, with no in-memory state dependency.
    with TestClient(create_app(data_dir=directory)) as c:
        assert c.get(f'/api/comparisons/{body["id"]}').json() == body
    with sqlite3.connect(directory / "comparisons.sqlite3") as db:
        assert db.execute("SELECT content FROM materials WHERE role='source'").fetchone()[0] == SOURCE.encode()


def test_pdf_without_text_is_rejected(client):
    with pymupdf.open() as pdf:
        pdf.new_page()
        content = pdf.tobytes()
    response = upload(client, {"source": ("scan.pdf", content, "application/pdf")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "pdf_requires_ocr"


def test_corrupt_docx_is_rejected(client):
    response = upload(client, {"a": ("broken.docx", b"not a zip", "application/octet-stream")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_document"


def test_over_20_mib_is_rejected_before_extraction(client):
    # Invalid PDF would cause an extraction error if the size gate ran too late.
    response = upload(client, {"source": ("large.pdf", b"!" * (20 * 1024 * 1024 + 1), "application/pdf")})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_intake_makes_no_llm_call(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Intake tried to open an external connection")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    assert upload(client).status_code == 201


def test_repository_uses_stand_path(tmp_path, monkeypatch):
    directory = tmp_path / "separate-store"
    monkeypatch.setenv("JUDGE_DATA_DIR", str(directory))
    monkeypatch.chdir(tmp_path)
    with TestClient(create_app()) as c:
        assert upload(c).status_code == 201
    assert (directory / "comparisons.sqlite3").is_file()
    assert not (tmp_path / ".judge-data").exists()


@pytest.mark.parametrize("filename,content,status,code", [
    ("empty.txt", b" \n\t", 422, "empty_text"),
    ("bad.txt", b"\xff\xfe", 422, "invalid_utf8"),
    ("binary.txt", b"hello\x00world", 422, "invalid_text"),
    ("old.doc", b"legacy", 415, "unsupported_format"),
    ("fake.pdf", b"plain text", 422, "invalid_document"),
])
def test_invalid_files_are_actionable(client, filename, content, status, code):
    response = upload(client, {"b": (filename, content, "application/octet-stream")})
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["message"]


def make_docx(xml):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", xml)
    return output.getvalue()


def test_docx_preserves_paragraphs_tables_tabs_and_breaks(client):
    content = make_docx('''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
    <w:p><w:r><w:t xml:space="preserve">  First</w:t><w:tab/><w:t>part</w:t><w:br/><w:t>line</w:t></w:r></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>جدول</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    </w:body></w:document>''')
    response = upload(client, {"a": ("book.docx", content, "application/octet-stream")})
    assert response.status_code == 201, response.text
    assert response.json()["materials"]["a"]["text"] == "  First\tpart\nline\n\nجدول"
    assert response.json()["materials"]["a"]["file_sha256"] == hashlib.sha256(content).hexdigest()


def test_text_pdf_extracts_real_text(client):
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), "A real text layer.")
        content = pdf.tobytes()
    response = upload(client, {"a": ("book.pdf", content, "application/pdf")})
    assert response.status_code == 201, response.text
    assert "A real text layer." in response.json()["materials"]["a"]["text"]


def test_utf8_bom_preserves_original_bytes(client):
    content = b"\xef\xbb\xbf" + SOURCE.encode()
    response = upload(client, {"source": ("source.txt", content, "text/plain")})
    assert response.status_code == 201
    source = response.json()["materials"]["source"]
    assert source["text"] == SOURCE
    assert source["file_sha256"] == hashlib.sha256(content).hexdigest()
    assert source["sha256"] == hashlib.sha256(SOURCE.encode()).hexdigest()


def test_pasted_text_uses_same_intake(client):
    response = client.post("/api/comparisons/text", json={
        "source": SOURCE, "a": A, "b": B, "source_language": "ar", "target_language": "en",
    })
    assert response.status_code == 201
    assert response.json()["materials"]["source"]["text"] == SOURCE


def test_failed_triple_does_not_save_partial_comparison(client, tmp_path):
    response = upload(client, {"b": ("empty.txt", b"", "text/plain")})
    assert response.status_code == 422
    with sqlite3.connect(tmp_path / "judge/comparisons.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM comparisons").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM materials").fetchone()[0] == 0


def test_missing_original_is_rejected(client):
    response = client.post("/api/comparisons", files={"a": ("a.txt", b"A"), "b": ("b.txt", b"B")},
                           data={"source_language": "ar", "target_language": "en"})
    assert response.status_code == 422


def test_unknown_comparison_has_no_data(client):
    response = client.get("/api/comparisons/not-found")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "comparison_not_found"


def test_upload_filename_is_metadata_not_a_filesystem_path(client, tmp_path):
    response = upload(client, {"a": ("../../outside.txt", A.encode(), "text/plain")})
    assert response.status_code == 201
    assert response.json()["materials"]["a"]["filename"] == "outside.txt"
    assert not (tmp_path / "outside.txt").exists()


def test_health_describes_local_intake_stage(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["stage"] == "intake"
    assert response.json()["live_enabled"] is False
