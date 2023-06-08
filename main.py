"""
A simple script to match known words in Duolingo with an anki deck of
(japanese) vocabulary (In this case a modified version of WaniKani ultimate.)
WaniKani ultimate: https://ankiweb.net/shared/info/266084933

JWT should be extracted and saved to jwt.txt by logging in to duolingo and 
extracting the cookie with the following JavaScript line in the console:
document.cookie.match(new RegExp('(^| )jwt_token=([^;]+)'))[0].slice(11);
"""
import argparse
from pathlib import Path
from typing import NewType

from ankipandas import Collection
import duolingo
import pandas


Notes = NewType("Notes", pandas.DataFrame)


def get_known_words(profile: duolingo.Duolingo, lang: str) -> list[str]:
    """Get a list of known words from duolingo profile for specified language."""
    return profile.get_known_words(lang)


def get_notes(col: Collection, tag: str) -> Notes:
    """Get notes with specified tag from collection."""
    notes = col.notes
    selection = notes[notes.has_tag(tag)]
    return selection


def match_duo_with_anki(notes: Notes, words: list[str]) -> Notes:
    """Match notes with a list of words and append the duolingo tag to matches."""
    matches = []
    for index, note in enumerate(notes.fields_as_columns(inplace=False)["nfld_Vocab"]):
        for word in words:
            if word == note:
                matches.append(index)
    notes.iloc[matches].remove_tag("duolingo")
    return notes.iloc[matches].add_tag("duolingo")


def update_collection(col: Collection, notes: Notes) -> None:
    """Update Anki collection with updates notes."""
    col.notes.update(notes)
    col.summarize_changes()
    user_input = input("Continue? [y/N]: ")
    if user_input.lower() == "y":
        col.write(modify=True)
    else:
        print("Notes not updated, exiting...")


def _get_args() -> argparse.Namespace:
    """Get CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("user")
    return parser.parse_args()


def main(args: argparse.Namespace):
    """Run script with commandline arguments."""
    col = Collection()
    words = get_known_words(
        duolingo.Duolingo(
            args.user,
            jwt=Path("jwt.txt").resolve().read_text(encoding="UTF-8").strip(),
        ),
        "ja",
    )
    notes = get_notes(col, "vocab")
    updated = match_duo_with_anki(notes, words)
    update_collection(col, updated)


if __name__ == "__main__":
    main(_get_args())
