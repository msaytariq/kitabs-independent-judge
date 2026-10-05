"""Select a local parser by the declared file format; never perform OCR."""
from pathlib import Path
from independent_judge.infrastructure.formats.html import extract_html

from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import ExtractedText
from independent_judge.infrastructure.formats.docx import extract_docx
from independent_judge.infrastructure.formats.pdf import extract_pdf


class LocalTextExtractor:
    def extract(self, content: bytes, filename: str, content_type: str) -> ExtractedText:
        extension = Path(filename).suffix.lower()
        if extension in (".txt", ".md"):
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise InputError("invalid_utf8", "Save the text file with UTF-8 encoding.") from exc
            if any(ord(c) < 32 and c not in "\t\n\r" for c in text):
                raise InputError("invalid_text", "Text contains binary control characters.")
            return ExtractedText(text)
        if extension in (".html", ".htm"):
            return extract_html(content)
        if extension == ".docx":
            return extract_docx(content)
        if extension == ".pdf":
            return extract_pdf(content)
        raise InputError("unsupported_format", "Use UTF-8 TXT/MD, DOCX, or a PDF with selectable text.")
