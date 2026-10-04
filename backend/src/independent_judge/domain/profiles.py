"""Versioned brand-neutral evaluation policies; no job or platform IDs."""
from independent_judge.domain.errors import InputError

PROFILES = {
    'general': 'Preserve meaning, qualifications, logical relations and factual content. Accept valid synonyms and translation conventions.',
    'islamic-scholarly': 'Preserve scholarly meaning, attribution and qualifications. Accept defensible translations of Islamic terms; transliteration is not mandatory. Do not invent hadith authenticity or Quran verification. Reference-library verification is not enabled.',
}


def profile_policy(profile: str) -> str:
    if profile not in PROFILES:
        raise InputError('unknown_profile', 'Choose general or islamic-scholarly.')
    return PROFILES[profile]
