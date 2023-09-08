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

import mido
import json
import librosa
from collections import OrderedDict

# default tempo per beat (in us):  120 beats per minute
DEFAULT_TEMPO = 60000000 // 120
DICTIONARY_FILE = "dictionaries/opencpop-extension.txt"
PHONEME_FILE = "dictionaries/phoneme.txt"
AP_TIME_IN_MS = 200
F0_TIMESTEP = 0.005

# load dictionaries
with open(DICTIONARY_FILE, "r", encoding="utf8") as f:
    _dictionary = f.readlines()
    _dictionary = [line.strip().split() for line in _dictionary]
    _dictionary = {line[0]: line[1:] for line in _dictionary}

with open(PHONEME_FILE, "r", encoding="utf8") as f:
    _phoneme = f.readlines()
    _phoneme = [line.strip().split() for line in _phoneme]
    _phoneme = {line[0]: float(line[1]) for line in _phoneme}


def _update_midi_info(midi_info: dict[int, dict[str]],
                      current_time: int,
                      tempo: int,
                      syllable: str or None,
                      note: int or None) -> None:
    """ Update the MIDI information dictionary.

        Args:
            midi_info: the MIDI information dictionary to be updated.
            tempo: current tempo in us per beat.
            current_time: the current time in ticks.
            syllable: the syllable of the current note.
            note: the MIDI note of the current note, or 0 to turn off the current note.
    """
    if current_time not in midi_info:
        midi_info[current_time] = {}
    info = midi_info[current_time]
    info["tempo"] = tempo
    if syllable is not None:
        info["syllable"] = syllable
    if note is not None:
        info["note"] = note


def _update_duration(midi_info: list[(int, dict[str])]) -> None:
    """ Update the duration of each note in the MIDI information list.

        Args:
            midi_info: the MIDI information list to be updated.
    """
    for i in range(len(midi_info) - 1):
        duration = midi_info[i + 1][0] - midi_info[i][0]
        midi_info[i][1]["duration"] = duration
    midi_info[-1][1]["duration"] = 0


def _update_phoneme(midi_info: list[(int, dict[str])]) -> None:
    """ Update the phoneme of each note in the MIDI information list.

        Args:
            midi_info: the MIDI information list to be updated.
    """
    for mi in midi_info:
        if "syllable" in mi[1] and mi[1]["syllable"] != "" and mi[1]["note"] != 0:
            phoneme = _dictionary[mi[1]["syllable"]]
            phoneme = [p.lower() for p in phoneme]

            if len(phoneme) == 1:
                mi[1]["phoneme"] = [(phoneme[0], mi[1]["duration"])]
            else:
                dur0 = _phoneme[phoneme[0]]
                dur1 = _phoneme[phoneme[1]]
                mi[1]["phoneme"] = [(phoneme[0], dur0 * mi[1]["duration"] / (dur0 + dur1)),
                                    (phoneme[1], dur1 * mi[1]["duration"] / (dur0 + dur1))]


def _align_midi_info(midi_info: list[(int, dict[str])],
                     ticks_per_beat: int,
                     lyrics: [str],
                     syllables: [str]) -> None:
    """Align the midi info list with lyrics and syllables.

        Args:
            midi_info: the MIDI information list to be aligned.
            ticks_per_beat: number of ticks per beat in the MIDI file.
            lyrics: the lyrics of the song.
            syllables: the syllables of the song.

        Returns:
            The aligned MIDI information list.
    """
    syl = [s.split() for s in syllables]
    lyc = [[c for c in l] for l in lyrics]

    idx = 0

    for i in range(len(syl)):
        for j in range(len(syl[i])):
            current_syllable_word = syl[i][j]
            current_lyric_word = lyc[i][j]

            while idx < len(midi_info) and (("syllable" not in midi_info[idx][1]) or
                    midi_info[idx][1]["syllable"] != current_syllable_word):
                if "syllable" in midi_info[idx][1]:
                    if midi_info[idx][1]["syllable"] == "la":
                        midi_info.remove(midi_info[idx])
                        continue
                    else:
                        print(f"WARNING:  Lyric and syllable is not matched: {current_lyric_word} vs. {midi_info[idx][1]['syllable']}")
                        break
                midi_info[idx][1].pop("syllable", None)
                midi_info[idx][1].pop("phoneme", None)

                if midi_info[idx][1]["note"] == 0:
                    midi_info[idx][1]["lyric"] = "<SP>"
                    midi_info[idx][1]["syllable"] = "<SP>"
                idx += 1

            if j == 0 and idx > 0 and midi_info[idx - 1][1]["note"] == 0:
                midi_info[idx - 1][1]["lyric"] = "<SP>"
                ts = midi_info[idx - 1][0]
                duration = midi_info[idx - 1][1]["duration"]
                tempo = midi_info[idx - 1][1]["tempo"]
                ap_duration = AP_TIME_IN_MS * ticks_per_beat * 1000 // tempo
                if ap_duration < duration:
                    midi_info[idx - 1][1]["duration"] = duration - ap_duration
                    ts += ap_duration
                    midi_info.insert(idx,
                                     (ts, {"note": 0, "duration": ap_duration, "tempo": tempo,
                                           "lyric": "<AP>", "syllable": "<AP>"}))
                    idx += 1

            if idx >= len(midi_info):
                raise Exception(f"Cannot find syllable {current_syllable_word} in MIDI information list.")

            midi_info[idx][1]["lyric"] = current_lyric_word
            idx += 1


def _make_f0_seq(note: int, duration: int, tempo: int, ticks_per_beat: int) -> str:
    """Make the F0 sequence from note and duration.

        Args:
            note: the MIDI note.
            duration: the duration of the note.
            tempo: the tempo of the note.
            ticks_per_beat: number of ticks per beat in the MIDI file.
    """

    f0 = librosa.midi_to_hz(note) if note != 0 else 0
    repeats = int(duration * tempo / 1000000.0 / ticks_per_beat / F0_TIMESTEP)
    f0_seq = " ".join([f"{f0:.3f}"] * repeats)
    return f0_seq


def _make_ds(midi_info: list[(int, dict[str])],
             ticks_per_beat: int) -> [dict[str]]:
    """Make the DiffSinger file from midi information list.

        Args:
            midi_info: the MIDI information list.
            ticks_per_beat: number of ticks per beat in the MIDI file.

        Returns:
            The DiffSinger file.
    """
    ds = []
    current_dict = OrderedDict()
    for mi in midi_info:
        ts = mi[0]
        if "lyric" not in mi[1]:
            continue
        if mi[1]["lyric"] == "<AP>":
            if current_dict != {}:
                ds.append(current_dict)
                current_dict = OrderedDict()
            current_dict["offset"] = ts * mi[1]["tempo"] / 1000000.0 / ticks_per_beat
            current_dict["text"] = "AP"
            current_dict["ph_seq"] = "AP"
            current_dict["ph_dur"] = "{:.3f}".format(mi[1]["duration"] * mi[1]["tempo"] / 1000000.0 / ticks_per_beat)
            current_dict["ph_num"] = "1"
            current_dict["note_seq"] = "REST"
            current_dict["note_dur"] = "{:.3f}".format(mi[1]["duration"] * mi[1]["tempo"] / 1000000.0 / ticks_per_beat)
            current_dict["note_slur"] = "0"
            current_dict["f0_seq"] = _make_f0_seq(0, mi[1]["duration"], mi[1]["tempo"], ticks_per_beat)
            current_dict["f0_timestep"] = "{:.3f}".format(F0_TIMESTEP)
        else:
            if current_dict == {}:
                continue
            lyric = mi[1]["lyric"] if mi[1]["lyric"] != "<SP>" else "SP"
            current_dict["text"] += (" " + lyric)
            num_ph = len(mi[1]["phoneme"]) if mi[1]["lyric"] != "<SP>" else 1
            current_dict["ph_num"] += (" " + str(num_ph))
            current_dict["note_dur"] += " {:.3f}".format(
                mi[1]["duration"] * mi[1]["tempo"] / 1000000.0 / ticks_per_beat
            )
            current_dict["note_slur"] += " 0"
            current_dict["f0_seq"] = _make_f0_seq(
                0, mi[1]["duration"], mi[1]["tempo"], ticks_per_beat
            )
            current_dict["f0_timestep"] = "{:.3f}".format(F0_TIMESTEP)
            if mi[1]["lyric"] != "<SP>":
                current_dict["ph_seq"] += (" " + " ".join([p[0] for p in mi[1]["phoneme"]]))
                current_dict["ph_dur"] += (" " + " ".join(["{:.3f}".format(p[1] * mi[1]["tempo"] / 1000000.0 /
                                                           ticks_per_beat) for p in mi[1]["phoneme"]]))
                current_dict["note_seq"] += (" " + librosa.midi_to_note(mi[1]["note"]))
            else:
                current_dict["ph_seq"] += " SP"
                current_dict["ph_dur"] += " {:.3f}".format(mi[1]["duration"] * mi[1]["tempo"]
                                                           / 1000000.0 / ticks_per_beat)
                current_dict["note_seq"] += " REST"
    if current_dict != {}:
        ds.append(current_dict)

    return ds


def midi2ds(midi_file: str,
            lyrics: [str],
            syllables: [str],
            output_file: str) -> None:
    """ Convert an annotated MIDI file to a DiffSinger file.

        The MIDI file must be annotated with the following metadata:
            - lyrics: the lyrics of the song
    Args:
        midi_file: the annotated MIDI file.
        lyrics: lyrics of the song, sentence by sentence.
        syllables: syllables of the song, sentence by sentence.
        output_file: the output DiffSinger file.
    """

    tempo = DEFAULT_TEMPO

    midi = mido.MidiFile(midi_file)
    ticks_per_beat = midi.ticks_per_beat
    midi_info = {}

    print(f"Ticks per beat: {ticks_per_beat}")
    for tid, track in enumerate(midi.tracks):
        print(f"Track {tid}: {track.name} ({len(track)} messages)")
        current_time = 0
        for i, msg in enumerate(track):
            # print(msg)
            if msg.type == "end_of_track":
                break
            elif msg.type == "set_tempo":
                tempo = msg.tempo
                print(f"  Updated tempo to {tempo}.")
            elif msg.type == "note_on":
                current_time += msg.time
                if msg.velocity == 0:
                    _update_midi_info(midi_info, current_time, tempo, None, 0)
                else:
                    _update_midi_info(midi_info, current_time, tempo, None, msg.note)
            elif msg.type == "note_off":
                current_time += msg.time
                _update_midi_info(midi_info, current_time, tempo, None, 0)
            elif msg.type == "lyrics":
                current_time += msg.time
                _update_midi_info(midi_info, current_time, tempo, msg.text, None)

        print(f"  End of track {tid}.")

    midi_info = sorted(midi_info.items(), key=lambda x: x[0])
    _update_duration(midi_info)
    _update_phoneme(midi_info)

    # Align the midi info with lyrics and syllables
    _align_midi_info(midi_info, ticks_per_beat, lyrics, syllables)

    print(midi_info)

    # Make the DiffSinger file from midi info list
    ds = _make_ds(midi_info, ticks_per_beat)

    # Write the DiffSinger file
    ds_json_obj = json.dumps(ds, indent=2, ensure_ascii=False).encode("utf8")
    with open(output_file, "w", encoding="utf8") as f:
        f.write(ds_json_obj.decode())
