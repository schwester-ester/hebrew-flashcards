from words import HebrewWord, PartOfSpeech, Binyaan, HEBREW_CLASS_MAP, get_word_attrs
import os
from typing import List
import hashlib
import pandas as pd
from dataclasses import asdict

CACHE_DIRECTORY = "resources/cache/cache.csv"
COLS = get_word_attrs()

def get_note_id_from_word(word: HebrewWord) -> int:
    # Hash full identifying attributes
    unique_str = f"{word.word}|{word.transliteration}|{word.meaning}"
    return int(hashlib.sha256(unique_str.encode()).hexdigest(), 16) % (10**10)

def parse_enum(enum_str: str):
    module = globals()  # or use a more secure/custom module dict if needed
    enum_class_name, member_name = enum_str.split(".")

    enum_class = module.get(enum_class_name)
    if enum_class is None:
        raise ValueError(f"Enum class '{enum_class_name}' not found")

    try:
        return enum_class[member_name]
    except KeyError:
        raise ValueError(f"Member '{member_name}' not found in '{enum_class_name}'")


def to_dataframe(words: List[HebrewWord]) -> pd.DataFrame:
    return pd.DataFrame([asdict(word) for word in words])


def from_dataframe(df: pd.DataFrame) -> List[HebrewWord]:
    result = []
    for _, row in df.iterrows():
        kwargs = row.dropna().to_dict()

        pos = kwargs.get("part_of_speech")
        if isinstance(pos, PartOfSpeech):
            pos_enum = pos
        else:
            pos_enum = (
                parsed
                if (pos and type(parsed := parse_enum(pos)) is PartOfSpeech)
                else PartOfSpeech.WORD
            )
            kwargs["part_of_speech"] = pos_enum

        binyan = kwargs.get("binyan")
        if binyan and not isinstance(binyan, Binyaan):
            kwargs["binyan"] = (
                parsed if type(parsed := parse_enum(binyan)) is Binyaan else None
            )

        cls = HEBREW_CLASS_MAP.get(
            pos_enum if pos_enum else PartOfSpeech.WORD, HebrewWord
        )

        word_obj = cls(**kwargs)
        result.append(word_obj)
    return result


def check_cache(query: str) -> List[HebrewWord]:
    df = pd.read_csv(CACHE_DIRECTORY)

    lookup = df.loc[df["word"] == query]
    return from_dataframe(lookup)


def write_cache(words: List[HebrewWord], file: str = CACHE_DIRECTORY) -> None:
    df = to_dataframe(words)

    # Reorder columns to match COLS, inserting NaNs where necessary
    df = df.reindex(columns=COLS)

    write_header = not os.path.exists(file)

    df.to_csv(CACHE_DIRECTORY, mode="a", index=False, header=write_header)
