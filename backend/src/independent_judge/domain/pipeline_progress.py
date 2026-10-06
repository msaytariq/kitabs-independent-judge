"""Progress of a Kitabs launch, counted from the artifacts that the platform has saved.

Steps: preparation (1), four stages for each fragment (translator, audit, editor, proofreader),
the apparatus of each fragment and the assembly (1). No estimate of time: only finished steps.
"""
FRAGMENT_KINDS = ('translated_chunk', 'audit_report', 'edited_chunk', 'proofread_chunk')
PHASES = ('preparation', 'translation', 'apparatus', 'assembly')


def pipeline_progress(status: str, stage: str | None, artifacts: list[dict]) -> dict:
    chunks = next((a.get('chunks') for a in artifacts if a['kind'] == 'chunks'), None)
    fragment = {}
    for a in artifacts:
        if a['kind'] in FRAGMENT_KINDS and a.get('chunkId'):
            fragment.setdefault(a['chunkId'], set()).add(a['kind'])
    apparatus = sum(a['kind'] == 'apparatus' for a in artifacts)
    assembled = any(a['kind'] == 'assembled_document' for a in artifacts)
    if status == 'completed':
        percent = 100
    elif not chunks:
        percent = 0
    else:
        total = 1 + 4 * chunks + chunks + 1
        done = 1 + sum(len(kinds) for kinds in fragment.values()) + apparatus + assembled
        percent = min(99, round(100 * done / total))
    finished = sum(len(kinds) == len(FRAGMENT_KINDS) for kinds in fragment.values())
    chunk = min(finished + 1, chunks) if chunks else None
    phase = ('assembly' if assembled or (chunks and apparatus >= chunks) else
             'apparatus' if chunks and finished >= chunks else
             'translation' if chunks else 'preparation')
    current = PHASES.index(phase)
    steps = [{'key': key, 'state': 'done' if status == 'completed' or i < current else
              'current' if i == current else 'waiting'} for i, key in enumerate(PHASES)]
    return {'percent': percent, 'stage': stage, 'chunk': chunk, 'chunks': chunks, 'steps': steps}
