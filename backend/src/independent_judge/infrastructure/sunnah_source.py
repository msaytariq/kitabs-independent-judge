"""Official keyed Sunnah.com record lookup; never scrape website pages."""
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import re
import httpx
from independent_judge.reference_ports import LibraryUnavailable


class _PlainText(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'br', 'div'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('p', 'div'): self.parts.append('\n')


def plain(text: str) -> str:
    parser = _PlainText(); parser.feed(text)
    return ''.join(parser.parts).strip()


class SunnahSource:
    def __init__(self, api_key: str, *, transport=None):
        self._key, self._transport = api_key, transport

    def lookup(self, collection: str, number: str) -> dict | None:
        if not self._key: raise LibraryUnavailable('Sunnah API key not configured')
        if collection not in ('bukhari', 'muslim') or not re.fullmatch(r'[0-9]{1,6}[a-z]?(?:\.[0-9]{1,3})?', number):
            raise LibraryUnavailable('Unsupported Sunnah reference')
        url = f'https://api.sunnah.com/v1/collections/{collection}/hadiths/{number}'
        try:
            with httpx.Client(timeout=15, follow_redirects=False, transport=self._transport) as client:
                with client.stream('GET', url, headers={'x-api-key': self._key}) as response:
                    if response.status_code == 404: return None
                    response.raise_for_status()
                    raw = bytearray()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw) > 512_000: raise ValueError('Oversized record')
            import json
            data = json.loads(raw)
            if data['collection'] != collection or str(data['hadithNumber']) != number:
                raise ValueError('Wrong identity')
            languages = {h['lang']: h for h in data['hadith']}
            text = plain(languages['ar']['body'])
            if not text: raise ValueError('Missing Arabic text')
            english = languages.get('en', {})
            grades = english.get('grades') or languages['ar'].get('grades') or []
            return {'id': f'sunnah:{collection}:{number}', 'collection': collection, 'number': number,
                    'text': text, 'english_text': plain(english.get('body', '')),
                    'grade': '; '.join(f"{g['graded_by']}: {g['grade']}" for g in grades),
                    'grades': grades, 'raw_record': data,
                    'edition': 'Sunnah.com API v1', 'url': f'https://sunnah.com/{collection}:{number}',
                    'snapshot_sha256': sha256(raw).hexdigest(),
                    'retrieved_at': datetime.now(timezone.utc).isoformat()}
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            raise LibraryUnavailable('Sunnah record unavailable or invalid') from None
