"""One Vercel Gateway request, no direct provider, hidden retries or fallback."""
import httpx
from independent_judge.domain.evaluation import EvaluationError, LlmResult
from independent_judge.infrastructure.gateway_usage import reported_cost

ENDPOINT='https://ai-gateway.vercel.sh/v1/chat/completions'


def payload(prompt, config):
    if config.model!='anthropic/claude-sonnet-5.5' or config.provider!='anthropic':
        raise EvaluationError('unreviewed_model','This pilot adapter is reviewed for Sonnet 5.5 via Gateway only.')
    body = {'model':config.model,'messages':[{'role':'system','content':prompt.system},
            {'role':'user','content':prompt.user}], 'max_tokens':config.max_tokens,
            'reasoning':{'effort':config.reasoning_effort},
            'providerOptions':{'gateway':{'only':[config.provider]}}}
    if prompt.response_schema is not None:
        body['response_format'] = {'type':'json_schema','json_schema':{
            'name':prompt.version.replace('-','_'),'strict':True,'schema':prompt.response_schema}}
    return body


class GatewayJudge:
    def __init__(self, api_key: str, *, transport=None):
        if not api_key: raise EvaluationError('missing_key','Gateway key is required.')
        self._key,self._transport=api_key,transport

    def complete(self, prompt, config) -> LlmResult:
        body=payload(prompt,config)
        try:
            with httpx.Client(transport=self._transport,timeout=httpx.Timeout(300,connect=20),follow_redirects=False) as client:
                response=client.post(ENDPOINT,json=body,headers={'Authorization':'Bearer '+self._key})
        except httpx.HTTPError as exc:
            raise EvaluationError('gateway_transport','Gateway transport failed; reservation remains held.') from None
        if response.status_code!=200:
            # Avoid logging a response which might echo request headers or credentials.
            raise EvaluationError('gateway_http',f'Gateway returned HTTP {response.status_code}; no automatic retry.')
        try: raw=response.json()
        except ValueError: raise EvaluationError('gateway_json','Gateway returned invalid JSON.') from None
        if not isinstance(raw,dict): raise EvaluationError('gateway_json','Invalid response envelope.')
        usage=raw.get('usage',{})
        cost=reported_cost(raw)
        if cost is None or not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ('prompt_tokens','completion_tokens')):
            raise EvaluationError('missing_usage','Gateway usage/cost is missing; reservation remains held.',raw=raw,cost_usd=cost)
        if raw.get('model') != config.model:
            raise EvaluationError('model_mismatch','Gateway returned an unexpected model ID.',raw=raw,cost_usd=cost)
        choices=raw.get('choices')
        if not isinstance(choices,list) or len(choices)!=1:
            raise EvaluationError('gateway_choices','Expected exactly one response.',raw=raw,cost_usd=cost)
        if choices[0].get('finish_reason')!='stop':
            raise EvaluationError('truncated','Judge response did not finish normally.',raw=raw,cost_usd=cost)
        text=choices[0].get('message',{}).get('content')
        if not isinstance(text,str) or not text.strip():
            raise EvaluationError('empty_response','Judge response is empty.',raw=raw,cost_usd=cost)
        return LlmResult(text,raw['model'],usage,cost,raw)
