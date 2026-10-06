

def test_person_entries_without_a_list_marker_are_counted():
    from independent_judge.domain.apparatus_inventory import inventory
    text = 'Body.\n\n## Persons\n\nal-Jubbāʾī — Muʿtazilī theologian (d. 321 AH)\n\nAbu Hurayra — Companion\n'
    assert inventory(text)['persons'] == 2
