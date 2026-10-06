"""Seams: does a sentence break where one paragraph or fragment ends and the next begins?

A long text is translated in fragments; a fragment seam is always a paragraph join of the text.
The code reads each join of two prose paragraphs in A and B with the same rule. A join is broken
when the first paragraph does not end a sentence or the second one starts in lowercase. Headings,
quotations, lists, notes, page numbers and the apparatus sections after the text are not prose.
No model takes part.
"""
import re
from independent_judge.domain.apparatus_inventory import HEADINGS

VERSION = 'seams-v1'
HEADING_WORDS = 15
_SENTENCE_END = re.compile(r'[.!?…:;؟»"”’\')\]*_]\s*$')
_NOT_PROSE = re.compile(r'^(?:#|>|\||\[|[-*•]\s|\d+[.)]\s|\d+\s*$|﴿)')
_ENTRY = re.compile(r'^[^\n.]{1,80}\s—\s')  # "Name — description" entries of a person index or glossary


def _prose(paragraph: str) -> bool:
    return not _NOT_PROSE.match(paragraph) and not _ENTRY.match(paragraph)


def _heading(paragraph: str, following: str) -> bool:
    """A short line without a sentence end or a comma before a capital line is a plain-text heading."""
    return (len(paragraph.split()) <= HEADING_WORDS and not _SENTENCE_END.search(paragraph)
            and not re.search(r'[,،]\s*$', paragraph) and following[:1].isupper())


def _body(text: str) -> list[str]:
    # Paragraphs are separated by blank lines; a text without blank lines has one paragraph per line.
    separator = r'\n\s*\n' if re.search(r'\n\s*\n', text) else r'\n'
    paragraphs = []
    for paragraph in (p.strip() for p in re.split(separator, text)):
        if paragraph.strip('#* ').rstrip(':').lower() in HEADINGS:
            break  # the apparatus starts here
        if paragraph:
            paragraphs.append(paragraph)
    return paragraphs


def _side(text: str) -> dict:
    paragraphs = _body(text)
    joins, items = 0, []
    for first, second in zip(paragraphs, paragraphs[1:]):
        if not (_prose(first) and _prose(second)) or _heading(first, second):
            continue
        joins += 1
        # A lowercase start continues the sentence; an article such as "al-" or "an-" does not.
        if not _SENTENCE_END.search(first) or re.match(r'[a-z](?![a-z]{0,2}-)', second):
            items.append({'end': first[-160:], 'start': second[:160]})
    return {'joins': joins, 'broken': len(items), 'items': items}


def seam_check(texts: dict) -> dict:
    return {'version': VERSION, **{side: _side(texts[side]) for side in ('a', 'b')}}
