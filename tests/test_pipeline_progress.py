"""Progress of a Kitabs launch from the artifacts that the platform has saved."""
from independent_judge.domain.pipeline_progress import pipeline_progress


def art(kind, stage, chunk=None):
    return {'kind': kind, 'stageId': stage, 'chunkId': chunk}


PREPARED = [art('source_text', 'intake'), art('prepared_document', 'preparation'),
            {'kind': 'chunks', 'stageId': 'chunking', 'chunkId': None, 'chunks': 3}]


def test_progress_before_the_chunks_shows_preparation():
    result = pipeline_progress('running', 'preparation', [art('source_text', 'intake')])
    assert result == {'percent': 0, 'stage': 'preparation', 'chunk': None, 'chunks': None,
                      'steps': [{'key': 'preparation', 'state': 'current'}, {'key': 'translation', 'state': 'waiting'},
                                {'key': 'apparatus', 'state': 'waiting'}, {'key': 'assembly', 'state': 'waiting'}]}


def test_progress_counts_the_stages_of_each_fragment():
    done = PREPARED + [art(k, s, 'c0') for k, s in (('translated_chunk', 'translator'), ('audit_report', 'audit'),
                                                     ('edited_chunk', 'editor'), ('proofread_chunk', 'proofreader'))]
    done += [art('translated_chunk', 'translator', 'c1')]
    result = pipeline_progress('running', 'audit', done)
    # 1 preparation + 3 x 4 stages + 3 apparatus + 1 assembly = 17 steps; 1 + 5 done.
    assert result['percent'] == 35
    assert (result['chunk'], result['chunks'], result['stage']) == (2, 3, 'audit')
    assert [s['state'] for s in result['steps']] == ['done', 'current', 'waiting', 'waiting']


def test_a_completed_launch_is_100_percent():
    assert pipeline_progress('completed', None, PREPARED)['percent'] == 100
