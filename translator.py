import time
import re
import string
from dataclasses import fields
from util import yes_or_no_input
from hebrew_processing import find_variations
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from serial import write_cache, check_cache
from words import HebrewWord, PartOfSpeech, BINYAAN_MAP, HEBREW_CLASS_MAP, POS_MAP
from typing import List, Optional
from audio import get_audio


def detect_unique_word(s: str, looking_for: list[str]) -> Optional[str]:
    found = [word for word in looking_for if word in s]
    return found[0] if len(found) == 1 else None


# TODO: only nouns and verbs are handled right now
def scrape_hebrew_word(
    query: str, driver: webdriver, lookup_audio: bool = True
) -> List[HebrewWord]:
    url = f"https://www.pealim.com/search/?q={query}"
    driver.get(url)
    time.sleep(random.uniform(1, 2))

    scraped = []
    containers = driver.find_elements(By.CSS_SELECTOR, ".verb-search-result")

    for container in containers:
        try:
            data = container.find_element(By.CSS_SELECTOR, ".verb-search-data")
            forms = container.find_element(By.CSS_SELECTOR, ".verb-search-forms")

            try:
                root = data.find_element(
                    By.CSS_SELECTOR, ".verb-search-root a"
                ).text.strip()
            except NoSuchElementException:
                root = None

            # if noun: "Part of speech: noun - <ex. kattal> pattern, masculine"
            # if verb: "Part of speech: verb - <ex. PI'EL>"
            word_data = (
                data.find_element(By.CSS_SELECTOR, ".verb-search-binyan")
                .text.strip()
                .lower()
            )

            results = forms.find_elements(By.CSS_SELECTOR, ".vf-search-result")
            for result in results:
                kwargs = {
                    "word": query,
                    "root": root,
                    "part_of_speech": PartOfSpeech.WORD,
                }

                menukad = result.find_element(By.CSS_SELECTOR, ".menukad").text.strip()
                kwargs["menukad"] = menukad
                transliteration = result.find_element(
                    By.CSS_SELECTOR, ".transcription"
                ).text.strip()
                kwargs["transliteration"] = transliteration
                meaning = result.find_element(
                    By.CSS_SELECTOR, ".vf-search-meaning"
                ).text.strip()
                kwargs["meaning"] = meaning
                path_to_audio = get_audio(
                    transliteration if transliteration else query,
                    return_none=(not lookup_audio),
                )
                kwargs["path_to_audio"] = path_to_audio

                try:
                    notes = (
                        result.find_element(By.CSS_SELECTOR, ".vf-search-tpgn")
                        .text.strip()
                        .lower()
                    )
                except NoSuchElementException:
                    notes = None

                if "noun" in word_data.split():
                    kwargs["part_of_speech"] = PartOfSpeech.NOUN
                    kwargs["gender"] = detect_unique_word(
                        word_data, ["feminine", "masculine"]
                    )  # TODO: what if both?
                    kwargs["number"] = detect_unique_word(
                        notes, ["singular", "plural"]
                    )  # TODO: what if both?
                    kwargs["definite"] = str(meaning.startswith("the "))

                elif "verb" in word_data.split():
                    kwargs["part_of_speech"] = PartOfSpeech.VERB
                    kwargs["binyan"] = BINYAAN_MAP.get(
                        word_data.split()[-1].upper().replace("'", "")
                    )
                    kwargs["tense"] = detect_unique_word(
                        notes, ["past", "present", "future"]
                    )
                    kwargs["person"] = detect_unique_word(
                        notes, ["1st person", "2nd person", "3rd person"]
                    )
                    kwargs["gender"] = detect_unique_word(
                        notes, ["feminine", "masculine"]
                    )  # TODO: what if both?
                    kwargs["number"] = detect_unique_word(
                        notes, ["singular", "plural"]
                    )  # TODO: what if both?

                word_cls = HEBREW_CLASS_MAP[kwargs["part_of_speech"]]
                scraped.append(word_cls(**kwargs))

        except Exception as e:
            print("Skipping a container due to error:", e)

    return scraped


def lookup_hebrew_word(
    query: str, driver: webdriver, lookup_audio: bool = True
) -> List[HebrewWord]:
    lookup = check_cache(query)

    if len(lookup) > 0:
        return lookup

    scraped = scrape_hebrew_word(query, driver, lookup_audio=lookup_audio)
    write_cache(scraped)

    return scraped


def manually_create_word(word: str, lookup_audio: bool = True) -> HebrewWord:
    cls = HEBREW_CLASS_MAP[POS_MAP.get(input("PartOfSpeech?").upper(), "WORD")]

    kwargs = {"word": word}
    for field in fields(cls):
        name = field.name
        if not any(
            name == not_input for not_input in ["part_of_speech", "path_to_audio"]
        ):
            val = input(f"{name}")
            kwargs[name] = val

    kwargs["path_to_audio"] = get_audio(
        kwargs["menukad"] if kwargs["menukad"] else word, return_none=(not lookup_audio)
    )

    hebrew_word = cls(**kwargs)

    save = yes_or_no_input("Save?")
    if save:
        write_cache([hebrew_word])

    return hebrew_word


# Define punctuation to remove, excluding internal ones we want to keep
SAFE_INTERNALS = "-'״"
PUNCTUATION_TO_STRIP = "".join(
    ch
    for ch in string.punctuation
    + "…“”’‘•–—‎·▪︎׃״׳"  # includes Hebrew & typographic punct
    if ch not in SAFE_INTERNALS
)

# Regex to strip punctuation from start and end of word
punct_re = re.compile(
    rf"^[{re.escape(PUNCTUATION_TO_STRIP)}]+|[{re.escape(PUNCTUATION_TO_STRIP)}]+$"
)


def clean_word_preserving_internals(word: str) -> str:
    return punct_re.sub("", word)


def get_list_of_words(text: str | List[str]) -> List[str]:
    if type(text) is List:
        return text
    elif type(text) is str:
        return [
            clean_word
            for word in text.split()
            if (clean_word := clean_word_preserving_internals(word))
        ]
    else:
        raise TypeError(f"{text} is not a string or list of words")


def translate_text(
    text: str | List[str], driver: webdriver, lookup_audio: bool = True
) -> List[HebrewWord]:
    selected = []
    words = get_list_of_words(text)
    for word in words:
        print(f"\nLooking up: {word}")

        for word_variation in find_variations(word):
            options: List[HebrewWord] = lookup_hebrew_word(
                word_variation, driver, lookup_audio=lookup_audio
            )
            if options:
                break

        if not options:
            print("No meanings found.")
            manual_input = yes_or_no_input("Enter manually?")
            manual = (
                manually_create_word(word, lookup_audio=lookup_audio)
                if manual_input
                else None
            )
            selected.append(manual)
            continue

        for i, option in enumerate(options):
            print(
                f"{i}: {option.menukad or option.word} — {option.meaning or 'No meaning provided'}"
            )

        while True:
            try:
                index = input(
                    f"Select meaning for '{word}' (0-{len(options) - 1}): "
                ).strip()
                if index.lower() == "skip":
                    manual_input = yes_or_no_input("Enter manually?")
                    manual = (
                        manually_create_word(word, lookup_audio=lookup_audio)
                        if manual_input
                        else None
                    )
                    selected.append(manual)
                    break
                selected.append(options[int(index)])
                break
            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid index or 'skip' to skip.")

    return selected
