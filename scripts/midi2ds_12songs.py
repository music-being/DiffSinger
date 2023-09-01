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
from glob import glob
from pathlib import Path
from midi2ds import midi2ds

root_dir = Path(__file__).parent.parent.resolve()

sys.path.insert(0, str(root_dir))


if __name__ == "__main__":
    source_dir = root_dir.joinpath("samples", "12-songs")
    dest_dir = root_dir.joinpath("samples", "12-songs-ds")

    if not source_dir.exists():
        print(f"Source directory {source_dir} does not exist.")
        sys.exit(1)

    if not dest_dir.exists():
        print(f"Destination directory {dest_dir} does not exist.")
        sys.exit(1)

    midi_files = glob(str(source_dir.joinpath("*", "*.mid")), recursive=False)

    for file in midi_files:
        print(f"Processing {file}...")
        midi2ds(file, str(dest_dir.joinpath(Path(file).stem + ".ds")))
        break
