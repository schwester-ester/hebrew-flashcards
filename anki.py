import unicodedata
from typing import Optional
import base64
import os
import requests
from typing import List, Dict
from words import HebrewWord, PartOfSpeech
from audio import prepare_audio
from serial import get_note_id_from_word

ANKI_CONNECT_URL = 'http://localhost:8765'

# Two models
MODEL_AUDIO = "HebrewWordModelAudio"
MODEL_NO_AUDIO = "HebrewWordModelNoAudio"

def invoke(action, **params):
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": action,
        "version": 6,
        "params": params
    }).json()
    if response.get("error"):
        raise Exception(f"AnkiConnect error: {response['error']}")
    return response["result"]

def ensure_deck_exists(deck_name: str):
    if deck_name not in invoke("deckNames"):
        invoke("createDeck", deck=deck_name)


def ensure_models_exist():
    existing_models = invoke("modelNames")

    fields = [
        {"name": "Word"},
        {"name": "Menukad"},
        {"name": "Audio"},
        {"name": "Transliteration"},
        {"name": "Meaning"},
        {"name": "POS"},
        {"name": "InternalGUID"}
    ]

    templates_audio = [
        {
            "name": "Detailed",
            "Front": "{{Word}}<br>(detailed)",
            "Back": "{{Word}}<br>(detailed)<hr id=answer>{{Audio}}<br>{{Menukad}}<br>{{Transliteration}}<br>{{Meaning}}<br><i>{{POS}}</i>",
        },
        {
            "name": "AudioSimple",
            "Front": "{{Audio}}",
            "Back": "{{Audio}}<hr id=answer>{{Word}}<br>{{Meaning}}",
        },
        {
            "name": "WordSimple",
            "Front": "{{Word}}",
            "Back": "{{Word}}<hr id=answer>{{Audio}}<br>{{Meaning}}",
        },
        {
            "name": "MeaningSimple",
            "Front": "{{Meaning}}",
            "Back": "{{Meaning}}<hr id=answer>{{Audio}}<br>{{Word}}",
        },
    ]

    templates_no_audio = [
        {
            "name": "Detailed",
            "Front": "{{Word}}<br>(detailed)",
            "Back": "{{Word}}<br>(detailed)<hr id=answer>{{Audio}}<br>{{Menukad}}<br>{{Transliteration}}<br>{{Meaning}}<br><i>{{POS}}</i>",
        },
        {
            "name": "WordSimple",
            "Front": "{{Word}}",
            "Back": "{{Word}}<hr id=answer>{{Audio}}<br>{{Meaning}}",
        },
        {
            "name": "MeaningSimple",
            "Front": "{{Meaning}}",
            "Back": "{{Meaning}}<hr id=answer>{{Audio}}<br>{{Word}}",
        },
    ]

    css = """
.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}
"""

    if MODEL_AUDIO not in existing_models:
        invoke("createModel",
            modelName=MODEL_AUDIO,
            inOrderFields=[f["name"] for f in fields],
            css=css,
            cardTemplates=templates_audio,
            isCloze=False
        )

    if MODEL_NO_AUDIO not in existing_models:
        invoke("createModel",
            modelName=MODEL_NO_AUDIO,
            inOrderFields=[f["name"] for f in fields],
            css=css,
            cardTemplates=templates_no_audio,
            isCloze=False
        )


def reset_deck(deck_name: str):
    """Deletes all notes from the specified Anki deck."""
    note_ids = invoke("findNotes", query=f'deck:"{deck_name}"')
    if not note_ids:
        print(f"✅ Deck '{deck_name}' is already empty.")
        return

    invoke("deleteNotes", notes=note_ids)
    print(f"🧹 Deleted {len(note_ids)} notes from deck '{deck_name}'.")

def normalize_tag_value(value):
    return str(value).lower().replace(" ", "-")

def get_tags_from_word(word: HebrewWord) -> List[str]:
    tags = []
    for attr in ['root', 'tense', 'person', 'gender', 'number']:
        value = getattr(word, attr, None)
        if value:
            tags.append(normalize_tag_value(value))
    
    b_value = getattr(word, 'binyan', None)
    if b_value:
        tags.append(normalize_tag_value(b_value.name))
    return tags

def get_note_by_guid(guid: str) -> Optional[dict]:
    note_ids = invoke("findNotes", query=f"InternalGUID:{guid}")
    if not note_ids:
        return None
    notes = invoke("notesInfo", notes=note_ids)
    return notes[0] if notes else None

def get_notes_in_deck(deck_name: str) -> dict[str, dict]:
    note_ids = invoke("findNotes", query=f'deck:"{deck_name}"')
    if not note_ids:
        return {}

    notes = invoke("notesInfo", notes=note_ids)

    notes_by_internal_guid = {}
    for note in notes:
        fields = note.get("fields", {})
        internal_guid = fields.get("InternalGUID", {}).get("value")
        if internal_guid:
            notes_by_internal_guid[internal_guid] = note
        else:
            print(f"⚠️ Skipping note without InternalGUID: {note}")

    return notes_by_internal_guid


def get_model_name(note: dict) -> str:
    return note.get("modelName", "")

def delete_note(note_id: int):
    invoke("deleteNotes", notes=[note_id])

def get_fields(word: HebrewWord, audio_field: str):
    return {
        "Word": word.word,
        "Menukad": word.menukad or "",
        "Audio": audio_field,
        "Transliteration": word.transliteration or "",
        "Meaning": word.meaning or "",
        "POS": word.part_of_speech.name if word.part_of_speech else PartOfSpeech.WORD.name,
        "InternalGUID": str(get_note_id_from_word(word)),
    }

def add_note_to_anki(word: HebrewWord, deck_name: str, guid: str, model: str, audio_path=None, audio_tag=None):
    fields = get_fields(word, audio_field=audio_tag or "")

    # Upload audio to Anki media collection BEFORE creating the note
    if audio_path:
        with open(audio_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")
        invoke("storeMediaFile", filename=os.path.basename(audio_path), data=audio_data)

    note = {
        "deckName": deck_name,
        "modelName": model,
        "fields": fields,
        "tags": get_tags_from_word(word),
        "options": {"allowDuplicate": True},
        "guid": guid,
    }

    invoke("addNote", note=note)



def normalize_str(s: str) -> str:
    return unicodedata.normalize('NFC', s) if isinstance(s, str) else s

def fields_differ(existing_fields, new_fields) -> bool:
    return any(
        normalize_str(existing_fields.get(k, "")) != normalize_str(v)
        for k, v in new_fields.items()
        if (v is not None) and (v != "")
    )

def delete_notes_by_guid(guids_to_delete: List[str], all_notes: Dict[str, dict]):
    """Deletes notes using their GUIDs and the full note dict."""
    note_ids_to_delete = [
        note["noteId"] for guid, note in all_notes.items() if guid in guids_to_delete
    ]
    if note_ids_to_delete:
        invoke("deleteNotes", notes=note_ids_to_delete)


def upload_words_to_anki(words: List[HebrewWord], deck_name: str):
    ensure_models_exist()
    ensure_deck_exists(deck_name)

    # existing_notes = get_notes_in_deck(deck_name)
    # existing_guids = set(existing_notes.keys())
    # current_guids = set()

    for word in words:
        guid = get_note_id_from_word(word)
        note = get_note_by_guid(guid)
        # current_guids.add(guid)
        has_audio_now = word.path_to_audio is not None and word.path_to_audio != ""

        
        audio_path, audio_tag = prepare_audio(word)


        if note:
            current_model = get_model_name(note)
            is_audio_model = (current_model == MODEL_AUDIO)

            existing_fields = {k: v["value"] for k, v in note["fields"].items()}
            audio_to_keep = note["fields"].get("Audio", {}).get("value", "")

            # Build new fields with current info
            new_audio_value = audio_tag if has_audio_now else audio_to_keep

            new_fields = get_fields(word, audio_field=new_audio_value)
            fields_changed = fields_differ(existing_fields, new_fields)
            existing_tags = set(note.get("tags", []))
            new_tags = set(get_tags_from_word(word))
            tags_changed = existing_tags != new_tags

            if has_audio_now and not is_audio_model:
                # Switch model to audio, regardless of field match
                delete_note(note["noteId"])
                add_note_to_anki(word, deck_name, guid, MODEL_AUDIO, audio_path, audio_tag)

            elif (has_audio_now and is_audio_model) or (not has_audio_now and not is_audio_model):
                if fields_changed or tags_changed:
                    invoke("updateNoteFields", note={"id": note["noteId"], "fields": new_fields})
                    invoke("updateNoteTags", note=note["noteId"], tags=list(new_tags))

            elif not has_audio_now and is_audio_model:
                if fields_changed or tags_changed:
                    invoke("updateNoteFields", note={"id": note["noteId"], "fields": new_fields})
                    invoke("updateNoteTags", note=note["noteId"], tags=list(new_tags))
        else:
            # Create new note
            model = MODEL_AUDIO if has_audio_now else MODEL_NO_AUDIO
            add_note_to_anki(word, deck_name, guid, model, audio_path, audio_tag)

    # # Batch delete notes that are no longer present
    # to_delete = list(existing_guids - current_guids)
    # if to_delete:
    #     print(f"🗑️ Deleting {len(to_delete)} notes no longer present in word list.")
    #     delete_notes_by_guid(to_delete, existing_notes)