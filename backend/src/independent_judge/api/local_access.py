"""Loopback stand guard against public Host headers and cross-site mutations."""
from urllib.parse import urlsplit
from starlette.responses import JSONResponse

HOSTS={'127.0.0.1','localhost','::1','testserver'}


def local_url(value):
    try:
        url=urlsplit(value)
        return url.scheme in ('http','https') and url.hostname in HOSTS and not url.username
    except ValueError:
        return False


class LocalStandAccess:
    def __init__(self,app): self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type']=='http':
            headers=dict(scope['headers'])
            host=headers.get(b'host',b'').decode('latin1')
            origin=headers.get(b'origin')
            blocked=not local_url('http://'+host)
            if scope['method'] not in ('GET','HEAD','OPTIONS'):
                blocked |= origin is not None and not local_url(origin.decode('latin1'))
                blocked |= headers.get(b'sec-fetch-site')==b'cross-site'
            if blocked:
                response=JSONResponse({'error':{'code':'local_only','message':'This stand accepts loopback access only.'}},status_code=403)
                await response(scope,receive,send)
                return
        await self.app(scope,receive,send)
