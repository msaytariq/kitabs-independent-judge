"""A PDF text layer that stores each lam-alef pair in reverse order is repaired with a word list."""
from independent_judge.domain.arabic_order import repair_lam_alef, reversed_lam_alef
from independent_judge.domain.arabic_text import folded

KNOWN = {folded(w): n for w, n in {'هلل': 4, 'لا': 900, 'إلا': 500, 'والأمل': 2, 'الصلاة': 60, 'والصلاة': 40, 'لله': 300, 'مرسلا': 100,
                                   'آملا': 6, 'لآت': 3, 'الآخرة': 80}.items()}
DAMAGED = ('الحمد هلل وقصر به آمال القياصرة ال يختار إال الصالة واألمل اآلخرة والصالة ما توعدون آلت '
           'مرسال ') * 5


def known(word):
    return KNOWN.get(folded(word), 0)


def test_a_text_without_correct_lam_alef_pairs_is_damaged():
    assert reversed_lam_alef(DAMAGED)
    assert not reversed_lam_alef('لا إله إلا الله والصلاة على النبي ' * 20)
    # The reversed Allah ligature "هللا" ends in a lam-alef pair; it does not count as a correct pair.
    assert reversed_lam_alef(DAMAGED + ' هللا' * 40)


def test_each_reversed_pair_is_repaired_when_the_word_list_knows_the_result():
    fixed = repair_lam_alef(DAMAGED, known)
    assert fixed.startswith('الحمد لله وقصر به آمال القياصرة لا يختار إلا ')
    # A hamza alef after an alef cannot start a word: the repair needs no frequency.
    assert 'الصلاة والأمل الآخرة والصلاة' in fixed and 'مرسلا' in fixed
    # A rare word in the list does not replace a real word: "آمال" (hopes) and "آلت" stay.
    assert 'آمال' in fixed and 'آلت' in fixed


def test_a_correct_text_does_not_change():
    text = 'لا إله إلا الله والصلاة على النبي ' * 20
    assert repair_lam_alef(text, known) == text


def test_the_allah_ligature_and_an_unknown_word_with_the_article_are_repaired_without_the_list():
    text = DAMAGED + ' هللا األكاسرة واإلغريق وهلل'
    fixed = repair_lam_alef(text, known)
    assert fixed.endswith(' الله الأكاسرة والإغريق ولله')
