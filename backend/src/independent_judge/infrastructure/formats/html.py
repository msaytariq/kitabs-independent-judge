"""Conservative HTML-to-text extraction, never execute embedded content."""
from html.parser import HTMLParser
from independent_judge.domain.inputs import ExtractedText
from independent_judge.domain.errors import InputError


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'header', 'footer', 'noscript'):
            self.skip.append(tag)
        if not self.skip and tag in ('p','div','br','li','h1','h2','h3','h4','tr'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]: self.skip.pop()
        elif tag in ('p','div','li','h1','h2','h3','h4','tr'):
            self.parts.append('\n')

    def handle_data(self, text):
        if not self.skip: self.parts.append(text)


def extract_html(content: bytes) -> ExtractedText:
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise InputError('invalid_utf8', 'HTML must use UTF-8; upload a text export instead.') from exc
    parser = TextParser()
    parser.feed(text)
    return ExtractedText(''.join(parser.parts).strip(), (
        'HTML layout was removed. Verify content, source boundaries and footnote attribution.',))
