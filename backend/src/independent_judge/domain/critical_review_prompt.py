"""Appeal critical findings, including valid alternative readings."""
import json
from independent_judge.domain.evaluation import Prompt
from independent_judge.domain.judge_prompt import SYSTEM
from independent_judge.domain.profiles import profile_policy
from independent_judge.domain.review_parsing import CriticalDecision
from independent_judge.domain.response_schema import items_schema

POLICY='''Review every candidate critically, considering a defensible reading that would acquit the translation. Keep K only for a substantive demonstrated meaning error. Reject preferences or uncertain allegations; downgrade real smaller errors to T/A/S. Return {"decisions":[{"index":0,"verdict":"keep|reject|downgrade","code":"K|T|A|S","why":"concise English explanation"}]}. Include every candidate index exactly once. Do not create findings.'''


def critical_prompt(scope,side,candidates):
    return Prompt(SYSTEM+'\n'+profile_policy(scope.profile)+'\n'+POLICY,
        json.dumps({'source':scope.texts['source'],'translation':scope.texts[side],
                    'candidates':candidates},ensure_ascii=False),'critical-review-v1',
                  items_schema(CriticalDecision, 'decisions'))
