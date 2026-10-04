"""Extract Word paragraphs, including table paragraphs, without text cleanup."""
from io import BytesIO
from zipfile import BadZipFile, ZipFile
from xml.etree.ElementTree import ParseError

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import ExtractedText

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_EXPANDED_BYTES = 80 * 1024 * 1024


def _paragraphs(root):
    paragraphs = []
    for paragraph in root.iter(f"{W}p"):
        fragments = []
        for node in paragraph.iter():
            if node.tag == f"{W}t":
                fragments.append(node.text or "")
            elif node.tag == f"{W}tab":
                fragments.append("\t")
            elif node.tag in (f"{W}br", f"{W}cr"):
                fragments.append("\n")
            elif node.tag == f"{W}footnoteReference":
                fragments.append(f'[fn:{node.get(f"{W}id")}]')
            elif node.tag == f"{W}endnoteReference":
                fragments.append(f'[en:{node.get(f"{W}id")}]')
        paragraphs.append("".join(fragments))
    return "\n\n".join(paragraphs)


def _xml(archive, name):
    root = ElementTree.fromstring(archive.read(name))
    if any(node.tag in {f"{W}{tag}" for tag in ("ins", "del", "moveFrom", "moveTo")} for node in root.iter()):
        raise InputError("docx_pending_revisions", "Accept or reject tracked text changes before uploading the DOCX.")
    return root


def extract_docx(content: bytes) -> ExtractedText:
    try:
        with ZipFile(BytesIO(content)) as archive:
            if sum(item.file_size for item in archive.infolist()) > MAX_EXPANDED_BYTES:
                raise InputError("docx_expansion_limit", "The expanded DOCX exceeds 80 MiB. Export a smaller document or UTF-8 text.")
            root = _xml(archive, "word/document.xml")
            body = root.find(f"{W}body")
            if body is None:
                raise InputError("invalid_document", "DOCX has no document body.")
            sections = [_paragraphs(body)]
            for tag, prefix, heading in (("footnote", "fn", "Footnotes"), ("endnote", "en", "Endnotes")):
                name = f"word/{tag}s.xml"
                if name in archive.namelist():
                    notes_root = _xml(archive, name)
                    notes = [f'[{prefix}:{node.get(f"{W}id")}] {_paragraphs(node)}'
                             for node in notes_root.findall(f"{W}{tag}")
                             if node.get(f"{W}type", "normal") == "normal"]
                    if notes:
                        sections.append(f"[{heading}]\n" + "\n".join(notes))
        return ExtractedText("\n\n".join(sections), (
            "DOCX body, table paragraphs, footnotes and endnotes are extracted in document order. Review the preview.",
            "Headers, footers, comments and text inside images are not extracted; no OCR is performed.",
        ))
    except InputError:
        raise
    except (BadZipFile, KeyError, ParseError, DefusedXmlException, RuntimeError, EOFError, ValueError) as exc:
        raise InputError("invalid_document", "Cannot read this DOCX. Export a valid DOCX or UTF-8 text file.") from exc
