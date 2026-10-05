"""Prevent silent loss of notes/pages and unbounded archive/request processing."""
from io import BytesIO
import zipfile

from fastapi.testclient import TestClient
import pymupdf

from independent_judge.api.app import create_app
from test_intake import upload


def docx(members):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for name, value in members.items():
            z.writestr(name, value)
    return output.getvalue()


def test_docx_footnotes_and_endnotes_are_not_silently_dropped(tmp_path):
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    content = docx({
        "word/document.xml": f'<w:document {w}><w:body><w:p><w:r><w:t>Claim</w:t><w:footnoteReference w:id="1"/><w:endnoteReference w:id="2"/></w:r></w:p></w:body></w:document>',
        "word/footnotes.xml": f'<w:footnotes {w}><w:footnote w:id="-1" w:type="separator"><w:p><w:r><w:separator/></w:r></w:p></w:footnote><w:footnote w:id="1"><w:p><w:r><w:t>Source citation</w:t></w:r></w:p></w:footnote></w:footnotes>',
        "word/endnotes.xml": f'<w:endnotes {w}><w:endnote w:id="2"><w:p><w:r><w:t>Editorial note</w:t></w:r></w:p></w:endnote></w:endnotes>',
    })
    with TestClient(create_app(tmp_path)) as client:
        response = upload(client, {"a": ("notes.docx", content, "application/octet-stream")})
    assert response.status_code == 201, response.text
    assert response.json()["materials"]["a"]["text"] == (
        "Claim[fn:1][en:2]\n\n[Footnotes]\n[fn:1] Source citation\n\n[Endnotes]\n[en:2] Editorial note"
    )


def test_docx_rejects_pending_revisions_instead_of_mixing_versions(tmp_path):
    content = docx({"word/document.xml": '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:ins><w:r><w:t>Unaccepted revision</w:t></w:r></w:ins></w:p></w:body></w:document>'})
    with TestClient(create_app(tmp_path)) as client:
        response = upload(client, {"b": ("review.docx", content, "application/octet-stream")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "docx_pending_revisions"


def test_docx_expansion_is_bounded_before_reading_xml(tmp_path):
    # A compressed 81 MiB XML payload fits under the upload limit.
    content = docx({"word/document.xml": b" " * (81 * 1024 * 1024)})
    with TestClient(create_app(tmp_path)) as client:
        response = upload(client, {"b": ("expanded.docx", content, "application/octet-stream")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "docx_expansion_limit"


def test_pdf_with_missing_text_on_one_page_requires_review(tmp_path):
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), "Text page")
        pdf.new_page()
        content = pdf.tobytes()
    with TestClient(create_app(tmp_path)) as client:
        response = upload(client, {"source": ("mixed.pdf", content, "application/pdf")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "pdf_missing_text_pages"
    assert "2" in response.json()["error"]["message"]


def test_request_limit_counts_actual_bytes_without_content_length(tmp_path):
    # Stream is deliberately invalid JSON: size must be rejected before JSON parsing.
    def chunks():
        for _ in range(62):
            yield b" " * (1024 * 1024)
    with TestClient(create_app(tmp_path)) as client:
        response = client.post("/api/comparisons/text", content=chunks(),
                               headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"


def test_pdf_with_reversed_arabic_ligatures_is_rejected_not_passed_on(tmp_path, monkeypatch):
    from independent_judge.infrastructure.formats import pdf as pdf_format
    assert pdf_format.damaged_arabic_order('الباب األول في ذكر هللا')
    assert not pdf_format.damaged_arabic_order('الباب الأول في ذكر الله إلى الآخرة')
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), "Text page")
        content = document.tobytes()
    monkeypatch.setattr(pdf_format, '_page_text', lambda page: 'الباب األول في ذكر هللا تعالى')
    with TestClient(create_app(tmp_path)) as client:
        response = upload(client, {"source": ("damaged.pdf", content, "application/pdf")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "pdf_arabic_order_damaged"


def test_pdf_arabic_presentation_forms_become_ordinary_letters(tmp_path, monkeypatch):
    from independent_judge.infrastructure.formats import pdf as pdf_format
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), "Text page")
        content = document.tobytes()
    monkeypatch.setattr(pdf_format, '_page_text', lambda page: 'ﺣدﯾث ﺗﺣﻔﺔ اﻟﻣؤﻣن ﻟﻶﺧرة ﷲ ﷺ x²')
    text = pdf_format.extract_pdf(content).text
    # Unicode compatibility mapping; the farsi-yeh glyph of the PDF stays U+06CC.
    assert text == 'حد\u06ccث تحفة المؤمن للآخرة الله ﷺ x²'
