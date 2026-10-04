"""Probe the other version for the same defect, without copying accusations."""
import json
from independent_judge.domain.evaluation import Prompt
from independent_judge.domain.judge_prompt import SYSTEM
from independent_judge.domain.profiles import profile_policy

POLICY='''For each candidate defect reported elsewhere, check the supplied translation independently. Return {"decisions":[{"index":0,"verdict":"present|absent|uncertain","finding":null,"why":"English reason"}]}. For present, finding must have the exact finding schema and quote this translation, never the other version. For absent/uncertain use null. Cover each candidate once. Shared wording alone does not establish a shared defect.'''


def cross_prompt(scope,side,candidates):
    return Prompt(SYSTEM+'\n'+profile_policy(scope.profile)+'\n'+POLICY,
        json.dumps({'source':scope.texts['source'],'translation':scope.texts[side],
                    'candidates':candidates},ensure_ascii=False),'cross-check-v1')
