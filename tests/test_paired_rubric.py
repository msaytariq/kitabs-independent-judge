"""The apparatus rule grades the form of an edition the same way for A and B."""
from independent_judge.domain.paired_rubric import RUBRIC, SYSTEM, VERSION


def test_the_top_apparatus_level_requires_notes_apart_from_the_author_text():
    top = RUBRIC['apparatus'][4]
    assert 'separate from the author' in top and 'anchored' in top
    # Notes kept inside the author's text cannot get more than level 3.
    assert 'inside the author' in RUBRIC['apparatus'][2]


def test_notes_inside_the_author_sentences_are_a_readability_defect():
    assert 'notes do not interrupt' in RUBRIC['readability'][4]


def test_added_notes_earn_credit_only_when_correct():
    assert 'never earn automatic points' not in SYSTEM
    assert 'Added notes, glossaries and person indexes are a strength only when' in SYSTEM
    assert 'wrong or invented added note is a defect' in SYSTEM


def test_the_source_layout_does_not_make_inline_notes_correct():
    assert 'Takhrij and editor notes that the source prints inside the text are notes' in SYSTEM


def test_the_rule_is_neutral_and_the_version_changes():
    assert 'Do not infer producers or reward a platform' in SYSTEM
    assert VERSION == 'paired-rubric-v2'
