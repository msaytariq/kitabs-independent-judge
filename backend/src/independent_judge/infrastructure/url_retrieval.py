"""Bounded public HTTP retrieval with DNS pinning and redirect revalidation."""
from datetime import datetime, timezone
from hashlib import sha256
import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urljoin, urlsplit

from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import MAX_FILE_BYTES
from independent_judge.url_ports import RetrievedDocument

FORMATS = {'text/plain': '.txt', 'text/markdown': '.md', 'text/html': '.html',
           'application/pdf': '.pdf',
           'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'}


def _resolve(host):
    return tuple({entry[4][0] for entry in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)})


def _request(url, address, limit, timeout):
    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    connection = http.client.HTTPConnection(parsed.hostname, port, timeout=timeout)
    deadline = time.monotonic() + timeout
    # Connect to the validated IP, never resolve the host a second time.
    sock = socket.create_connection((address, port), timeout=timeout)
    try:
        if parsed.scheme == 'https':
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=parsed.hostname)
        connection.sock = sock
        path = parsed.path or '/'
        if parsed.query: path += '?' + parsed.query
        connection.request('GET', path, headers={'Host': parsed.netloc, 'Accept-Encoding': 'identity',
                           'User-Agent': 'IndependentJudge/0.1 document-intake'})
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        length = headers.get('content-length')
        if length and int(length) > limit:
            raise InputError('file_too_large', 'URL document exceeds 20 MiB.')
        if headers.get('content-encoding', 'identity').lower() != 'identity':
            raise InputError('unsupported_url_content', 'Compressed HTTP responses are not supported.')
        body = bytearray()
        if response.status in (301, 302, 303, 307, 308):
            return response.status, headers, b''
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0: raise TimeoutError()
            sock.settimeout(remaining)
            block = response.read1(min(65536, limit + 1 - len(body)))
            if not block: break
            body.extend(block)
            if len(body) > limit:
                raise InputError('file_too_large', 'URL document exceeds 20 MiB.')
        return response.status, headers, bytes(body)
    finally:
        connection.close()
        sock.close()


class UrlRetriever:
    def __init__(self, *, resolve=_resolve, request=_request):
        self.resolve, self.request = resolve, request

    def fetch(self, url: str) -> RetrievedDocument:
        original = url
        try:
            for _ in range(4):
                parsed = urlsplit(url)
                if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                        or parsed.username is not None or parsed.password is not None
                        or parsed.port not in (None, 80, 443) or len(url) > 4096
                        or any(ord(c) < 33 for c in url)):
                    raise InputError('invalid_url', 'Use a public HTTP(S) URL without credentials.')
                addresses = self.resolve(parsed.hostname)
                if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
                    raise InputError('private_url', 'Local and private network destinations are not allowed.')
                status, headers, content = self.request(url, addresses[0], MAX_FILE_BYTES, 15)
                if status in (301, 302, 303, 307, 308):
                    if not headers.get('location'): break
                    url = urljoin(url, headers['location'])
                    continue
                if status != 200:
                    raise InputError('url_unavailable', 'The URL did not return a document. Upload a file instead.')
                if len(content) > MAX_FILE_BYTES:
                    raise InputError('file_too_large', 'URL document exceeds 20 MiB.')
                media = headers.get('content-type', '').split(';')[0].strip().lower()
                extension = FORMATS.get(media)
                if not extension:
                    raise InputError('unsupported_url_content', 'Use a text, HTML, DOCX or PDF document URL.')
                filename = parsed.path.rsplit('/', 1)[-1]
                if not filename.lower().endswith(extension): filename = 'document' + extension
                return RetrievedDocument(content, filename, media, {
                    'source_url': original, 'final_url': url,
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'sha256': sha256(content).hexdigest(), 'method': 'public-http-pinned-v1'})
        except InputError:
            raise
        except (OSError, ValueError, http.client.HTTPException) as exc:
            raise InputError('url_unavailable', 'Cannot retrieve this URL. Upload a file instead.') from exc
        raise InputError('url_redirect_limit', 'Too many redirects. Use the direct document URL.')
