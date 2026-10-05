"""Host guard: loopback by default; a public deployment names its hosts in JUDGE_PUBLIC_HOSTS.

Cross-site writes stay blocked. The editorial workbench stays loopback-only.
"""
import os
from urllib.parse import urlsplit
from starlette.responses import JSONResponse

HOSTS={'127.0.0.1','localhost','::1','testserver'}
LOCAL_ONLY_PATHS=('/api/editorial',)


def local_url(value, public=frozenset()):
    try:
        url=urlsplit(value)
        if url.username or url.scheme not in ('http','https'):
            return False
        return url.hostname in HOSTS or url.hostname in public
    except ValueError:
        return False


class LocalStandAccess:
    def __init__(self,app):
        self.app=app
        self.public=frozenset(h.strip() for h in os.environ.get('JUDGE_PUBLIC_HOSTS','').split(',') if h.strip())

    async def __call__(self,scope,receive,send):
        if scope['type']=='http':
            headers=dict(scope['headers'])
            host=headers.get(b'host',b'').decode('latin1')
            origin=headers.get(b'origin')
            name=urlsplit('http://'+host).hostname if host else None
            on_public=name in self.public and name not in HOSTS
            blocked=not local_url('http://'+host, self.public)
            blocked |= on_public and scope['path'].startswith(LOCAL_ONLY_PATHS)
            if scope['method'] not in ('GET','HEAD','OPTIONS'):
                blocked |= origin is not None and not local_url(origin.decode('latin1'), self.public)
                blocked |= headers.get(b'sec-fetch-site')==b'cross-site'
            if blocked:
                response=JSONResponse({'error':{'code':'local_only','message':'This stand accepts loopback access only.'}},status_code=403)
                await response(scope,receive,send)
                return
        await self.app(scope,receive,send)
