import requests
import re
from serial import get_note_id_from_word
from words import HebrewWord
from typing import Optional, List, Tuple
import os
import urllib.parse
from util import yes_or_no_input
from dataclasses import replace


def add_audios(lst: List[HebrewWord]) -> List[HebrewWord]:
    updated_lst = []
    for hebrew_word in lst:
        audio = get_audio(
            hebrew_word.menukad if hebrew_word.menukad else hebrew_word.word
        )
        updated_lst.append(replace(hebrew_word, path_to_audio=audio))

    return updated_lst


def get_google_tts_audio_url(word: str, lang: str = "he"):
    base_url = "https://translate.google.com/translate_tts"
    params = {"ie": "UTF-8", "q": word, "tl": lang, "client": "tw-ob"}
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def get_audio(
    word: str, lang: str = "he", manual_check: bool = True, return_none=False
):
    url = get_google_tts_audio_url(word, lang) if not return_none else None

    if manual_check and not return_none:
        print(word, url)
        valid = yes_or_no_input("Keep audio?")
        return url if valid else None

    return url


def download_audio(word: HebrewWord, audio_dir="resources/audio") -> Optional[str]:
    if not word.path_to_audio:
        return None

    os.makedirs(audio_dir, exist_ok=True)

    # Deterministic filename based on note ID
    note_id = get_note_id_from_word(word)
    safe_word = re.sub(r"[^\w\-א-ת]", "", word.word)  # Remove problematic chars
    filename = f"{safe_word}_{note_id}.mp3"
    output_path = os.path.join(audio_dir, filename)

    # If file already exists, no need to redownload
    if os.path.exists(output_path):
        return output_path

    # Download if it's a URL
    if word.path_to_audio.startswith("http"):
        try:
            response = requests.get(word.path_to_audio)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            else:
                print(f"Failed to download audio for {word.word}: status {response.status_code}")
        except Exception as e:
            print(f"Error downloading audio for {word.word}: {e}")
    else:
        # Treat as local path
        if os.path.exists(word.path_to_audio):
            return word.path_to_audio
        else:
            print(f"Audio file not found: {word.path_to_audio}")

    return None



def prepare_audio(word: HebrewWord) -> tuple[Optional[str], Optional[str]]:
    audio_path = download_audio(word)
    if audio_path:
        # Normalize to forward slashes for Anki
        audio_basename = os.path.basename(audio_path)
        audio_tag = f"[sound:{audio_basename}]"
        return audio_path.replace("\\", "/"), audio_tag
    return None, None