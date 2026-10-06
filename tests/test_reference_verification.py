"""Quran verses and hadith in the source are located in reference texts and counted."""
from independent_judge.domain.reference_detection import detect_references
from independent_judge.domain.quran_matching import QuranIndex
from independent_judge.domain.hadith_matching import HadithIndex
from independent_judge.application.reference_verification import verify_references

VERSES = [
    {'chapter': 2, 'verse': 153, 'text': 'يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ'},
    {'chapter': 2, 'verse': 155, 'text': 'وَلَنَبْلُوَنَّكُمْ بِشَيْءٍ مِنَ الْخَوْفِ وَالْجُوعِ وَنَقْصٍ مِنَ الْأَمْوَالِ وَالْأَنْفُسِ وَالثَّمَرَاتِ ۗ وَبَشِّرِ الصَّابِرِينَ'},
    {'chapter': 5, 'verse': 27, 'text': 'قَالَ إِنَّمَا يَتَقَبَّلُ اللَّهُ مِنَ الْمُتَّقِينَ'},
]
HADITH = [
    {'id': 'muslim:7500', 'collection': 'Sahih Muslim', 'number': 7500,
     'text': 'حدثنا هداب قال رسول الله صلى الله عليه وسلم عجبا لأمر المؤمن إن أمره كله خير وليس ذاك لأحد إلا للمؤمن'},
    {'id': 'tirmidhi:2396', 'collection': "Jami' at-Tirmidhi", 'number': 2396,
     'text': 'قال رسول الله صلى الله عليه وسلم إن عظم الجزاء مع عظم البلاء وإن الله إذا أحب قوما ابتلاهم'},
]

SOURCE = '''وقال تعالى : {ولنبلونكم بشيء من الخوف والجوع ونقص من الأموال والأنفس والثمرات وبشر الصابرين} (( البقرة : 155))

وقال تعالى : {استعينوا بالصبر والصلاة إن الله مع الصابرين} ((محمد : 31))

27 - وعن صهيب قال: قال رسول الله ﷺ "عجبا لأمر المؤمن إن أمره كله له خير، وليس ذلك لأحد إلا للمؤمن" ((رواه مسلم)).

وقال النبي ﷺ : "إن عظم الجزاء مع عظم البلاء" ((رواه الترمذي)).

قال الله تعالى إنما يتقبل الله من المتقين فلا يمكن معرفة حكم زيد

وقال صلى الله عليه وسلم تحفة المؤمن الموت حديث تحفة المؤمن الموت أخرجه ابن أبي الدنيا'''


class Library:
    def __init__(self, items): self.items = items
    def records(self): return self.items
    def verses(self): return self.items


def test_markers_select_quran_and_hadith_candidates():
    found = detect_references(SOURCE)
    kinds = [(r['kind'], r['quote'][:12]) for r in found]
    assert ('quran', 'ولنبلونكم بش') in kinds and ('quran', 'استعينوا بال') in kinds
    assert ('quoted', 'عجبا لأمر ال') in kinds
    assert any(k == 'quran' and q.startswith('إنما يتقبل') for k, q in kinds)
    assert any(k == 'hadith' and q.startswith('تحفة المؤمن') for k, q in kinds)
    for r in found:
        assert SOURCE[r['start']:r['end']] == r['quote']


def test_quran_index_returns_surah_and_ayah_and_checks_the_source_label():
    index = QuranIndex(VERSES)
    assert index.locate('ولنبلونكم بشيء من الخوف والجوع')['ayah'] == '2:155'
    assert index.locate('استعينوا بالصبر والصلاة إن الله مع الصابرين')['ayah'] == '2:153'
    assert index.locate('من جد وجد ومن زرع حصد') is None
    result = verify_references({'source': SOURCE}, Library(VERSES), Library(HADITH))
    labels = {i['quote'][:9]: i for i in result['quran']['items']}
    assert labels['ولنبلونكم']['label_status'] == 'label_matches'
    wrong = labels['استعينوا ']
    assert wrong['label_status'] == 'label_differs' and wrong['label'] == 'محمد : 31'


def test_hadith_found_across_collections_and_summary_counts():
    result = verify_references({'source': SOURCE}, Library(VERSES), Library(HADITH))
    assert result['quran']['found'] == 3 and result['quran']['total'] == 3
    hadith = {i['quote'][:8]: i for i in result['hadith']['items']}
    assert hadith['عجبا لأم']['status'] in ('fragment', 'review')
    assert hadith['عجبا لأم']['candidates'][0]['id'] == 'muslim:7500'
    assert hadith['إن عظم ا']['candidates'][0]['collection'] == "Jami' at-Tirmidhi"
    assert result['hadith']['found'] == 2 and result['hadith']['total'] == 3
    assert result['hadith']['by_collection'] == {'Sahih Muslim': 1, "Jami' at-Tirmidhi": 1}


def test_hadith_index_keeps_negation_sensitive_statuses():
    index = HadithIndex([{'id': 'b:1', 'text': 'لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه'}])
    assert index.match('لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه')['status'] == 'exact'
    assert index.match('يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه')['status'] == 'review'
    assert index.match('من جد وجد ومن زرع حصد')['status'] == 'not_found'


def test_quran_adapter_fetches_one_fixed_edition_and_caches(tmp_path):
    import httpx, pytest
    from independent_judge.infrastructure.quran_library import QuranLibrary
    from independent_judge.reference_ports import LibraryUnavailable
    calls = []
    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(200, json={'quran': VERSES})
    library = QuranLibrary(tmp_path, transport=httpx.MockTransport(respond))
    verses = library.verses()
    assert verses[0]['chapter'] == 2 and verses[0]['verse'] == 153
    assert len(verses[0]['snapshot_sha256']) == 64
    assert library.verses() == verses and len(calls) == 1
    assert calls[0].endswith('/quran-api@1/editions/ara-quransimple.json')
    broken = QuranLibrary(tmp_path / 'b', transport=httpx.MockTransport(lambda r: httpx.Response(200, json={'quran': []})))
    with pytest.raises(LibraryUnavailable): broken.verses()


def test_hadith_adapter_covers_the_six_books_and_malik_by_default(tmp_path):
    from independent_judge.infrastructure.hadith_library import HadithLibrary, COLLECTIONS
    assert HadithLibrary(tmp_path).collections == tuple(COLLECTIONS)
    assert set(COLLECTIONS) == {'bukhari', 'muslim', 'abudawud', 'tirmidhi', 'nasai', 'ibnmajah', 'malik'}


def test_only_sayings_and_attributed_quotations_become_hadith_candidates():
    source = ('لما ثقل النبي ﷺ جعل يتغشاه الكرب فقالت فاطمة واكرب أبتاه.\n'
              'وكان يقول «المثل والقدوة في داره ومسجده وخطابه» في كل حين.\n'
              'قال رسول الله ﷺ: «من لا يرحم الناس لا يرحمه الله» ((صحيح البخاري: ٣١٠٤ ومسند أحمد)).\n'
              '((وفى رواية لمسلم)) وقال ﷺ إنما الصبر عند الصدمة الأولى.')
    quotes = [(r['kind'], r['quote']) for r in detect_references(source)]
    assert quotes == [('quoted', 'من لا يرحم الناس لا يرحمه الله'), ('hadith', 'إنما الصبر عند الصدمة الأولى')]


def test_short_fully_matching_quotation_is_a_quran_verse():
    verses = VERSES + [{'chapter': 24, 'verse': 32, 'text': 'وَأَنْكِحُوا الْأَيَامَىٰ مِنْكُمْ وَالصَّالِحِينَ'}]
    result = verify_references({'source': 'قال تعالى في كتابه وقال رسول الله ﷺ «وأنكحوا الأيامى منكم»'},
                               Library(verses), Library(HADITH))
    assert [i['ayah'] for i in result['quran']['items']] == ['24:32']
    assert result['hadith']['total'] == 0


def test_translation_references_are_checked_against_the_source():
    texts = {'source': SOURCE, 'a': 'Narrated by Muslim. Give glad tidings to the patient (2:155). (Quran 9:1)', 'b': ''}
    result = verify_references(texts, Library(VERSES), Library(HADITH))['takhrij']
    assert result['version'] == 'takhrij-v1'
    statuses = {(i['reference'], i['status']) for i in result['a']['items']}
    assert {('Sahih Muslim', 'correct'), ('Quran 2:155', 'correct'), ('Quran 9:1', 'wrong'),
            ("Jami' at-Tirmidhi", 'missing')} <= statuses
    assert result['b']['delivered'] == 0


def test_a_verse_in_round_brackets_with_a_surah_label_after_it_is_found_and_its_label_checked():
    verse = {'chapter': 17, 'verse': 79, 'text': 'وَمِنَ اللَّيْلِ فَتَهَجَّدْ بِهِ نَافِلَةً لَكَ عَسَىٰ أَنْ يَبْعَثَكَ رَبُّكَ مَقَامًا مَحْمُودًا'}
    source = 'وهو التهجد الذي ذكره الله في قوله: (وَمِنَ الليلِ فَتَهَجَّدْ بِهِ نَافِلَةً لَّكَ) الإسراء: 97 ولا يكون التهجد إلا بعد النوم'
    result = verify_references({'source': source, 'a': '', 'b': ''}, Library(VERSES + [verse]), Library(HADITH))
    item = result['quran']['items'][0]
    assert (item['ayah'], item['label'], item['label_status']) == ('17:79', 'الإسراء : 97', 'label_differs')


def test_an_ordinary_bracket_followed_by_a_number_is_not_a_surah_label():
    source = 'قال رسول الله ﷺ (إنما الأعمال بالنيات وإنما لكل امرئ ما نوى) رواه البخاري: 1'
    result = verify_references({'source': source, 'a': '', 'b': ''}, Library(VERSES), Library(HADITH))
    assert all(i.get('label_status') != 'label_differs' for i in result['quran']['items'])
