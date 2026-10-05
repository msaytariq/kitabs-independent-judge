"""Extract a PDF text layer without calling OCR or a remote provider."""
import re
import unicodedata
import pymupdf

from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import ExtractedText


# Some PDF producers store lam-alef and the Allah ligature in visual order, so the text
# layer reads "األول" for "الأول" and "هللا" for "الله". These sequences do not occur in
# correctly encoded Arabic. The order of other lam-alef pairs cannot be restored safely.
_REVERSED_LIGATURES = re.compile(r'(?:^|(?<=\s))(?:األ|اإل|اآل)|هللا')


def damaged_arabic_order(text: str) -> bool:
    return bool(_REVERSED_LIGATURES.search(text))


# Arabic presentation forms (glyph shapes) map to ordinary letters by Unicode
# compatibility decomposition. The honorific signs keep their own code points.
_KEEP = {'\ufdfa', '\ufdfb'}


def ordinary_arabic_letters(text: str) -> str:
    return ''.join(unicodedata.normalize('NFKC', c)
                   if (0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFF) and c not in _KEEP else c
                   for c in text)


def _page_text(page) -> str:
    return page.get_text("text", sort=False)


def extract_pdf(content: bytes) -> ExtractedText:
    try:
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise InputError("encrypted_pdf", "Unlock the PDF locally before uploading it.")
            pages = [ordinary_arabic_letters(_page_text(page)) for page in pdf]
    except InputError:
        raise
    except (pymupdf.FileDataError, RuntimeError, ValueError) as exc:
        raise InputError("invalid_document", "Cannot read this PDF. Upload a valid PDF or UTF-8 text file.") from exc
    if not pages or not any(page.strip() for page in pages):
        raise InputError("pdf_requires_ocr", "This PDF has no selectable text. Apply OCR separately, then upload the text.")
    missing = [str(index) for index, text in enumerate(pages, 1) if not text.strip()]
    if missing:
        raise InputError("pdf_missing_text_pages", (
            "No selectable text on PDF pages " + ", ".join(missing) +
            ". Review these pages: export text after handling scans or blank pages. No partial extraction was saved."
        ))
    if any(damaged_arabic_order(page) for page in pages):
        raise InputError("pdf_arabic_order_damaged", (
            "The PDF text layer stores Arabic letters in the wrong order (for example \u0647\u0644\u0644\u0627). "
            "Upload DOCX or TXT, or a PDF with a correct text layer. Nothing was saved."))
    return ExtractedText("\n\n".join(pages), (
        "PDF reading order and character extraction can differ from the page. Review the extracted text before comparison.",
    ), page_count=len(pages))
