"""A quote is found in the text although the text breaks its lines or carries invisible direction marks."""
from independent_judge.domain.evidence import locate

NOTE = '‎(1) رواه البخاري وأحمد قال: "خيارهم\n‎في الجاهلية خيارهم في الإسلام"'


def test_a_quote_on_one_line_is_found_across_a_line_break_and_a_direction_mark():
    quote = '(1) رواه البخاري وأحمد قال: "خيارهم في الجاهلية'
    found = locate(NOTE, quote)
    assert found['status'] == 'verified'
    # The range is in the original text, from the quote start to the quote end.
    start, end = found['ranges'][0]['start'], found['ranges'][0]['end']
    assert NOTE[start:end] == '(1) رواه البخاري وأحمد قال: "خيارهم\n‎في الجاهلية'


def test_spaces_count_as_one_space_but_letters_must_match():
    assert locate('Truth  is\n a virtue.', 'Truth is a virtue.')['status'] == 'verified'
    assert locate('Truth is a virtue.', 'Truth is a vice.')['status'] == 'missing'


def test_a_quote_that_occurs_twice_stays_ambiguous_and_an_empty_quote_is_missing():
    assert locate('verse 2. verse 2.', 'verse 2')['status'] == 'ambiguous'
    assert locate('text', ' ‎ ')['status'] == 'missing'


def test_an_exact_quote_keeps_its_range():
    assert locate('A virtue.', 'virtue')['ranges'] == [{'start': 2, 'end': 8}]
