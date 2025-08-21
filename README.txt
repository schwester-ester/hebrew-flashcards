# Hebrew Word Anki Uploader

This project provides a pipeline to translate Hebrew words or phrases, retrieve associated audio, generate grammatical metadata, and upload them to Anki with organized decks and models. It uses tools like Selenium, AnkiConnect, and custom logic to support Hebrew learning.

---

## 🚀 Features

- Translate Hebrew text using Selenium-based scraping
- Fetch or reuse audio for each word
- Determine grammatical features and tags (POS, binyaan, etc.)
- Upload structured notes to Anki with audio and metadata
- Avoid duplicating cards; intelligently update existing notes

---

## 📦 Requirements

- Python 3.10+
- Anki with AnkiConnect installed
- Chrome WebDriver (matching your browser version)

---

## 🛠 Setup Instructions

On Windows:

> python -m venv venv

> venv\Scripts\activate

> pip install -r requirements.txt

> npm install

> npm install --save-dev nodemon

> npm run dev

This will run the app on http://127.0.0.1:5000/

To attach a debugger in VSCode,

Go to the Run and Debug tab → click the green play icon → select "Node.js: Attach".

It will connect to that ws:// debugger session.


---

## 🧠 Key Concept: **Anki Notes vs. Cards**

* In Anki, a **Note** is a single data entry (like a Hebrew word with fields: word, audio, meaning...).
* A **Card** is a specific way of testing the note (e.g., “Audio → Word” or “Word → Meaning”).

✅ **One note can generate multiple cards**, each with its own **front/back format**.

When we define our model (`HebrewWordModelAudio` or `HebrewWordModelNoAudio`), we specify **multiple card templates**.

## 🔄 Want Dynamic Switching?

Anki doesn’t have “study modes” like Quizlet — instead, you **generate multiple cards** and either:

* Turn off templates you don't want
* Or filter by card type when reviewing

---

## ✅ Recap

| Goal                     | Solution                                    |
| ------------------------ | ------------------------------------------- |
| Multiple quiz directions | Use multiple card templates in the model    |
| Control which to study   | Use **Filtered Decks** or toggle card types |
| Edit what shows up       | Use the **Cards...** editor in Anki browser |

---
