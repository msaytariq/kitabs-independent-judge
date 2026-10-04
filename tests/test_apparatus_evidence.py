"""Generated apparatus is positive artifact evidence, not a quality verdict."""
from copy import deepcopy
import pytest
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash
from independent_judge.domain.apparatus_evidence import apparatus_evidence


def fixture():
    text = 'Translation.\n\n[1] A note.\n\nTerm — definition.'
    scope = {'texts': {'source': 'Source.', 'a': 'Version.', 'b': 'Translation.'},
             'hashes': {'source': 'source-hash', 'a': 'a-hash', 'b': text_hash('Translation.')}}
    items = []
    for quote in ('[1] A note.', 'Term — definition.'):
        start = text.index(quote)
        items.append({'start':start,'end':start+len(quote),'text':quote,'sha256':text_hash(quote)})
    evidence = {'artifact_text':text,'artifact_sha256':text_hash(text),
        'scope_hashes':deepcopy(scope['hashes']), 'translation_range':{'start':0,'end':12},
        'label_ru':'Сохранённый результат платформы', 'scope_label_ru':'Весь результат',
        'groups':[{'id':'notes','title_ru':'Примечания','purpose_ru':'Справки к тексту',
                   'items':[items[0]],'sample_indices':[0]},
                  {'id':'glossary','title_ru':'Словарные статьи','purpose_ru':'Пояснения терминов',
                   'items':[items[1]],'sample_indices':[0]}]}
    return evidence, scope


def test_counts_and_examples_come_from_unchanged_generated_artifact():
    evidence, scope = fixture()
    view = apparatus_evidence(evidence, scope)
    assert [g['count'] for g in view['groups']] == [1,1]
    assert view['groups'][0]['examples'][0]['text'] == '[1] A note.'
    assert view['quality_status'] == 'not_adjudicated'
    assert 'artifact_text' not in view
    assert apparatus_evidence(None,scope) is None


@pytest.mark.parametrize('problem',['artifact','quote','duplicate','scope','range'])
def test_stale_or_double_counted_apparatus_is_blocked(problem):
    evidence,scope=fixture()
    if problem=='artifact': evidence['artifact_text']+='changed'
    if problem=='quote': evidence['groups'][0]['items'][0]['text']='invented'
    if problem=='duplicate': evidence['groups'][0]['items']*=2
    if problem=='scope': scope['texts']['b']='Other output'
    if problem=='range': evidence['translation_range']['end']=9999
    with pytest.raises(InputError): apparatus_evidence(evidence,scope)
