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


def midi2ds(midi_file: str, output_file: str) -> None:
    """ Convert an annotated MIDI file to a DiffSinger file.

        The MIDI file must be annotated with the following metadata:
            - lyrics: the lyrics of the song
    Args:
        midi_file: the annotated MIDI file.
        output_file: the output DiffSinger file.
    """

    midi = mido.MidiFile(midi_file)
    for tid, track in enumerate(midi.tracks):
        print(f"Track {tid}: {track.name} ({len(track)} messages)")
        for (i, msg) in enumerate(track):
            print(f"  {i}: {msg}")


