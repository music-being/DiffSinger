# Copyright (c) 2023 MusicBeing Project. All Rights Reserved.
#
# Author: Tao Zhang <ztao8@hotmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from pathlib import Path
from midi2ds import midi2ds
from pypinyin import pinyin, Style
from zhon.hanzi import punctuation

root_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root_dir))

SOURCE_DIR = root_dir.joinpath("samples", "12-songs")
SOURCE_LYRIC_FILE = SOURCE_DIR.joinpath("lyrics.txt")
DEST_DIR = root_dir.joinpath("samples", "12-songs-ds")


def _load_lyrics(lyric_file: Path) -> list[list[str]]:
    """ Load the lyric file.

        Args:
            lyric_file: the lyric file to be loaded.

        Returns:
            A list of lyrics.
    """
    lyrics = []
    with open(lyric_file, "r", encoding="utf8") as f:
        lines = f.readlines()

        # remove punctuations
        for i in punctuation:
            lines = [line.replace(i, "") for line in lines]

        lines = [line.strip() for line in lines]

        current_lyric = []
        for line in lines:
            if line == "" or line.startswith("#"):
                if len(current_lyric) > 0:
                    lyrics.append(current_lyric)
                    current_lyric = []
            elif line.startswith("[") or line.endswith("]"):
                continue
            else:
                sentences = line.split()
                for sentence in sentences:
                    current_lyric.append(sentence.strip())
        if len(current_lyric) > 0:
            lyrics.append(current_lyric)

    return lyrics


def _pinyin_to_syllable(py: str) -> str:
    """Get syllable from Pinyin by removing the tone number.

        Args:
            py: the Pinyin to be processed.

        Returns:
            The syllable.
    """
    while len(py) > 0 and py[-1].isdigit():
        py = py[:-1]

    return py


def _lyrics_to_syllables(lyrics: list[list[str]]) -> list[list[str]]:
    """ Convert the lyrics to syllables.

        Args:
            lyrics: the lyrics to be converted.

        Returns:
            A list of syllables.
    """
    syllables = []
    for lyric in lyrics:
        current_syllable = []
        for sentence in lyric:
            syllable = pinyin(sentence, style=Style.TONE3)
            syllable = " ".join([_pinyin_to_syllable(s[0]) for s in syllable])
            current_syllable.append(syllable)
        syllables.append(current_syllable)
    return syllables


if __name__ == "__main__":
    if not SOURCE_LYRIC_FILE.exists():
        print(f"Source lyric file {SOURCE_LYRIC_FILE} does not exist.")
        sys.exit(1)

    if not SOURCE_DIR.exists():
        print(f"Source directory {SOURCE_DIR} does not exist.")
        sys.exit(1)

    if not DEST_DIR.exists():
        print(f"Destination directory {DEST_DIR} does not exist.")
        sys.exit(1)

    lyrics = _load_lyrics(SOURCE_LYRIC_FILE)
    syllables = _lyrics_to_syllables(lyrics)
    midi_files = [SOURCE_DIR / f"{i:d}/{i:d}.mid" for i in range(1, len(lyrics) + 1)]

    for i, file in enumerate(midi_files):
        print(f"Processing {file}...")
        midi2ds(str(file),
                lyrics[i],
                syllables[i],
                str(DEST_DIR.joinpath(Path(file).stem + ".ds")))
