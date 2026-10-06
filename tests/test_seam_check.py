"""Seams: a sentence must not break where one paragraph or fragment ends and the next begins."""
from independent_judge.domain.seam_check import seam_check

NADWA = ('The strong take their provisions from the end of the night,\n\n'
         'And if he reads in his bowing Surat Al-Furqan, he gains.\n\n'
         'He said: pray at night.\n\n'
         'and then he slept.')
KITABS = ('He prayed at night.\n\nHe slept early.\n\n## Chapter 2\n\nAllah says:\n\n> And from the night, keep vigil.\n\n'
          '230\n\nThe strong rise early.\n\nal-Bukhārī narrated it.\n\n## Persons\n\nal-Ḥasan — scholar of Basra\n\nIbn Mājah — compiler')


def test_a_paragraph_that_ends_without_a_sentence_end_or_a_paragraph_in_lowercase_is_a_break():
    result = seam_check({'source': '', 'a': NADWA, 'b': KITABS})
    assert result['a']['joins'] == 3 and result['a']['broken'] == 2
    assert result['a']['items'][0] == {'end': 'The strong take their provisions from the end of the night,',
                                       'start': 'And if he reads in his bowing Surat Al-Furqan, he gains.'}
    # Headings, verse quotations, page numbers and the apparatus sections are not seams of the text.
    # A name with the article "al-" starts a sentence in lowercase.
    assert (result['b']['joins'], result['b']['broken']) == (2, 0)
    assert result['version'] == 'seams-v1'


def test_one_paragraph_has_no_seams():
    result = seam_check({'source': '', 'a': 'One paragraph only.', 'b': KITABS})
    assert result['a'] == {'joins': 0, 'broken': 0, 'items': []}


def test_a_text_with_single_line_breaks_has_a_seam_at_each_line():
    # A chat writes paragraphs on single lines; each line break is then a paragraph join.
    text = 'He prayed at night.\nHe slept early,\nand rose at dawn.'
    result = seam_check({'source': '', 'a': text, 'b': KITABS})
    assert (result['a']['joins'], result['a']['broken']) == (2, 1)


def test_a_plain_heading_line_is_not_a_broken_seam():
    text = ('The Merit of Remembering Death\nThe Messenger of God said: remember death.\n'
            'The strong take their provisions from the end of the night,\nAnd if he reads, he gains.')
    result = seam_check({'source': '', 'a': text, 'b': KITABS})
    assert (result['a']['joins'], result['a']['broken']) == (2, 1)
