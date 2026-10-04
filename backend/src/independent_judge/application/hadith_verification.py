"""Automatically search marked Arabic quotations without sending private text."""
from independent_judge.domain.hadith_matching import match_hadiths, quotations
from independent_judge.reference_ports import HadithLibraryPort, LibraryUnavailable
from independent_judge.application.sunnah_verification import verify_official


def verify_hadiths(texts: dict[str, str], library: HadithLibraryPort, official=None) -> dict:
    detected = quotations(texts['source'])
    base = {'library': 'Hadith API · Arabic Bukhari/Muslim electronic editions',
            'translation_accuracy': 'not_assessed', 'authenticity': 'not_adjudicated',
            'detection': 'marked_arabic_quotations_v2', 'detected_count': len(detected),
            'checked_count': min(30, len(detected)), 'limit_reached': len(detected) > 30}
    if not detected:
        return base | {'status': 'no_candidates', 'verified_count': 0, 'items': []}
    try:
        records = library.records()
        items = match_hadiths(texts['source'], records)
    except LibraryUnavailable:
        return base | {'status': 'unavailable', 'verified_count': None, 'items': []}
    return base | {'status': 'checked', 'items': items,
                   'official': verify_official(items, official),
                   'verified_count': sum(i['status'] in ('exact', 'normalized') for i in items),
                   'indexed_records': len(records)}
