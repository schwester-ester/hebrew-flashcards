from enum import Enum
from util import remove_duplicates
from dataclasses import asdict, dataclass, fields
from typing import Optional, Literal, List, Type


class Language(Enum):
    HEBREW = "hebrew"


class PartOfSpeech(Enum):
    WORD = "WORD"
    NOUN = "NOUN"
    VERB = "VERB"
    ADJECTIVE = "ADJECTIVE"
    ADVERB = "ADVERB"
    PREPOSITION = "PREPOSITION"


POS_MAP = {pos.value: pos for pos in PartOfSpeech}


@dataclass(frozen=True)
class Word:
    word: str
    meaning: str


# Shared base class for all words
@dataclass(frozen=True)
class HebrewWord(Word):
    word: str
    transliteration: Optional[str] = None
    meaning: Optional[str] = None
    menukad: Optional[str] = None  # with nikud (vowelized)
    part_of_speech: Optional[PartOfSpeech] = None
    root: Optional[str] = None
    path_to_audio: Optional[str] = None  # ← NEW

    def __post_init__(self):
        object.__setattr__(self, "language", Language.HEBREW)


# Nouns and adjectives may have gender and number
@dataclass(frozen=True)
class HebrewNoun(HebrewWord):
    gender: Optional[Literal["masculine", "feminine", "masculine and feminine"]] = None
    number: Optional[Literal["singular", "plural", "singular and plural"]] = None
    definite: Optional[Literal["True", "False"]] = None  # Definite (with "ha-")?

    def __post_init__(self):
        object.__setattr__(self, "part_of_speech", PartOfSpeech.NOUN)


@dataclass(frozen=True)
class HebrewAdjective(HebrewWord):
    gender: Optional[Literal["masculine", "feminine", "masculine and feminine"]] = None
    number: Optional[Literal["singular", "plural", "singular and plural"]] = None
    # agrees_with: Optional[str] = None  # Refers to the noun it modifies

    def __post_init__(self):
        object.__setattr__(self, "part_of_speech", PartOfSpeech.ADJECTIVE)


class Binyaan(Enum):
    PAAL = "PAAL"
    PIEL = "PIEL"
    PUAL = "PUAL"
    NIFAL = "NIFAL"
    HIFIL = "HIFIL"
    HUFAL = "HUFAL"
    HITPAEL = "HITPAEL"


BINYAAN_MAP = {b.value: b for b in Binyaan}


# Verbs have more grammatical info
@dataclass(frozen=True)
class HebrewVerb(HebrewWord):
    binyan: Optional[Binyaan] = None  # e.g., Pa'al, Pi'el, Hif'il
    tense: Optional[Literal["past", "present", "future", "imperative"]] = None
    person: Optional[Literal["1st", "2nd", "3rd"]] = None
    gender: Optional[Literal["masculine", "feminine"]] = None
    number: Optional[Literal["singular", "plural"]] = None

    def __post_init__(self):
        object.__setattr__(self, "part_of_speech", PartOfSpeech.VERB)


# Others
@dataclass(frozen=True)
class HebrewPreposition(HebrewWord):
    # Usually invariant, but might have contractions (like "ba")
    # formality: Optional[Literal["formal", "colloquial"]] = None

    def __post_init__(self):
        object.__setattr__(self, "part_of_speech", PartOfSpeech.PREPOSITION)


@dataclass(frozen=True)
class HebrewAdverb(HebrewWord):
    def __post_init__(self):
        object.__setattr__(self, "part_of_speech", PartOfSpeech.ADVERB)


HEBREW_CLASS_MAP: dict[type[PartOfSpeech] : type[HebrewWord]] = {
    PartOfSpeech.WORD: HebrewWord,
    PartOfSpeech.VERB: HebrewVerb,
    PartOfSpeech.NOUN: HebrewNoun,
    PartOfSpeech.ADJECTIVE: HebrewAdjective,
    PartOfSpeech.ADVERB: HebrewAdverb,
    PartOfSpeech.PREPOSITION: HebrewPreposition,
}


def get_word_attrs(
    classes: List = [
        HebrewWord,
        HebrewNoun,
        HebrewVerb,
        HebrewAdjective,
        HebrewAdverb,
        HebrewPreposition,
    ],
) -> List[str]:
    return remove_duplicates([field.name for cls in classes for field in fields(cls)])
