"""Extract a PDF text layer without calling OCR or a remote provider."""
import pymupdf

from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import ExtractedText


def extract_pdf(content: bytes) -> ExtractedText:
    try:
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise InputError("encrypted_pdf", "Unlock the PDF locally before uploading it.")
            pages = [page.get_text("text", sort=False) for page in pdf]
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
    return ExtractedText("\n\n".join(pages), (
        "PDF reading order and character extraction can differ from the page. Review the extracted text before comparison.",
    ))
