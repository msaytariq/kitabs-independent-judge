"""Takhrij accuracy: each reference in a translation is checked against the source and the libraries."""
from independent_judge.domain.takhrij_check import source_takhrij, takhrij_check, translation_takhrij

SOURCE = ('قال رسول الله ﷺ «الجنة تحت أقدام الأمهات» (رواه النسائي في سننه: ٣٠٥٣) والحاكم. '
          'وروى مسلم عن أبي هريرة رضي الله عنه حديثا. وقال: «خيركم خيركم لأهله» رواه الترمذي. '
          'والطفل المسلم يتعلم. ﴿وَمِنْ آيَاتِهِ أَنْ خَلَقَ لَكُم﴾ [الروم: ٣٠/٢١]')
VERSES = ['30:21']
LIBRARY = {('nasai', 3053): ['الجنة تحت أقدام الأمهات فالزمها'],
           ('bukhari', 5971): ['من أحق الناس بحسن صحابتي قال أمك'],
           ('tirmidhi', 3895): ['خيركم خيركم لأهله وأنا خيركم لأهلي']}


def lookup(collection, number):
    if collection in ('ahmad', 'hakim'):
        return None  # Not in the libraries: the reference stays unchecked.
    return LIBRARY.get((collection, number), [])


def test_the_source_names_collections_only_in_attributions():
    found = source_takhrij(SOURCE)
    # "المسلم" in ordinary prose is not the collection of Muslim.
    assert found['collections'] == ['hakim', 'muslim', 'nasai', 'tirmidhi']
    assert found['numbered'] == [('nasai', 3053)]


def test_a_translation_reference_is_read_with_its_number():
    text = ('Paradise is beneath her feet.[1] Muslim narrated from Abu Hurayra. Muslims learn.\n\n'
            '[1] Narrated by al-Nasāʾī in his *Sunan* (3053), and by al-Ḥākim in *al-Mustadrak*.\n'
            'The best of you is best to his family (Tirmidhi 3895). And among His signs (Quran 30:21).\n'
            'Also (al-Bukhari, no. 5971) and Sahih al-Bukhari, Vol. 8, Book 73, Hadith 2.\n\n'
            '## Persons\n\nMuslim — compiler of Sahih Muslim (d. 261 AH).\n')
    found = translation_takhrij(text)
    assert found['collections'] == ['bukhari', 'hakim', 'muslim', 'nasai', 'tirmidhi']
    assert [(r['collection'], r['number']) for r in found['numbered']] == [
        ('nasai', 3053), ('tirmidhi', 3895), ('bukhari', 5971)]
    assert [(r['surah'], r['ayah']) for r in found['quran']] == [(30, 21)]


def test_correct_wrong_and_missing_references_are_counted():
    good = ('[1] Narrated by al-Nasāʾī (3053) and al-Ḥākim. Muslim narrated it. '
            'Narrated by al-Tirmidhi. And among His signs (30:21).')
    bad = ('Narrated by al-Bukhari (5971). Narrated by Muslim. And among His signs (Quran 16:42). '
           'Recorded by Abu Dawud.')
    result = takhrij_check(SOURCE, {'a': bad, 'b': good}, VERSES, lookup, found_in={'muslim'})
    # Takhrij is about hadith only: 4 collections + 1 numbered hadith. Verse references are counted apart.
    assert result['total'] == 5 and result['verses']['total'] == 1
    b = result['b']
    assert (b['delivered'], b['wrong']) == (5, 0)
    assert (result['verses']['b']['delivered'], result['verses']['b']['wrong']) == (1, 0)
    a = result['a']
    # Muslim is right. Wrong: a number of a hadith that is not in the source (its collection is
    # judged by the number, not twice). Abu Dawud, which the source does not name, stays unchecked:
    # the code cannot prove it wrong. The verse that the source does not quote is a wrong verse reference.
    assert (a['delivered'], a['wrong']) == (1, 1)
    assert (result['verses']['a']['delivered'], result['verses']['a']['wrong']) == (0, 1)
    assert ('Sunan Abi Dawud', 'unchecked') in {(i['reference'], i['status']) for i in a['items']}
    statuses = {(i['reference'], i['status']) for i in a['items']}
    assert ('Sahih al-Bukhari 5971', 'wrong') in statuses
    assert ('Quran 16:42', 'wrong') in statuses
    assert ("Sunan an-Nasa'i 3053", 'missing') in statuses
    assert ("Sunan an-Nasa'i 3053", 'correct') in {(i['reference'], i['status']) for i in b['items']}
    assert ('Quran 30:21', 'missing') in statuses
    assert result['version'] == 'takhrij-v2'


def test_a_number_outside_the_libraries_is_unchecked_not_wrong():
    text = 'Narrated by Ahmad (10065). Narrated by Ahmad (7994).'
    result = takhrij_check('رواه أحمد في المسند: ١٠٠٦٥', {'a': text, 'b': ''}, [], lookup)
    statuses = {(i['reference'], i['status']) for i in result['a']['items']}
    assert ('Musnad Ahmad 10065', 'as_in_source') in statuses
    assert ('Musnad Ahmad 7994', 'unchecked') in statuses
    assert (result['a']['delivered'], result['a']['wrong']) == (2, 0)  # the collection and the number
    assert result['b']['delivered'] == 0


def test_a_source_without_references_gives_no_row():
    assert takhrij_check('نص بلا مراجع', {'a': 'Text.', 'b': 'Text.'}, [], lookup) is None


def test_a_verse_of_a_quoted_passage_is_not_wrong_when_the_source_quotes_it():
    source = '﴿قال إنما أشكو بثي وحزني إلى الله﴾ [يوسف: ١٢/٨٤-٨٧]'
    text = 'I complain of my grief only to Allah (12:86).'
    alone = takhrij_check(source, {'a': text, 'b': ''}, ['12:84'], lookup)
    assert alone['verses']['a']['wrong'] == 1 and alone['total'] == 0
    passage = takhrij_check(source, {'a': text, 'b': ''}, ['12:84'], lookup, quoted=lambda s, a: (s, a) == (12, 86))
    assert passage['verses']['a']['wrong'] == 0


def test_a_range_cites_every_verse_in_it():
    found = translation_takhrij('Luqman advised his son (31:13–15).')
    assert [(r['surah'], r['ayah']) for r in found['quran']] == [(31, 13), (31, 14), (31, 15)]


def test_nadwa_style_references_are_read_and_a_surah_is_not_a_hadith_collection():
    text = ("(And the night when it stills.) [Adh-Duha (92): 2]. Surah As-Sajdah (32): verse 16. "
            "He recited 'Takbar al-Malik' (Sura Al-Baqarah: 285-286) every night.")
    found = translation_takhrij(text)
    assert [(r['surah'], r['ayah']) for r in found['quran']] == [(92, 2), (32, 16)]
    assert found['numbered'] == [] and found['collections'] == []


def test_an_added_collection_is_checked_in_the_library():
    source = 'قال رسول الله ﷺ «إنما الأعمال بالنيات»'
    text = 'Narrated by al-Bukhari. Narrated by Abu Dawud. Narrated by Ahmad.'
    result = takhrij_check(source, {'a': text, 'b': ''}, ['1:1'], lookup, found_in={'bukhari'})
    statuses = {(i['reference'], i['status']) for i in result['a']['items']}
    assert {('Sahih al-Bukhari', 'correct'), ('Sunan Abi Dawud', 'unchecked'), ('Musnad Ahmad', 'unchecked')} <= statuses
    assert (result['a']['delivered'], result['a']['wrong']) == (0, 0)
