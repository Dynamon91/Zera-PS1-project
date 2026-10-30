"""Verify a controller-only camera inspection of the real playable model."""
import hashlib
import json
from pathlib import Path
import sys


def check(folder):
    folder = Path(folder)
    capture = json.loads((folder / 'capture.json').read_text())
    assert capture['frames_run'] == 2900
    assert hashlib.sha256((folder.parent / 'zera_wip09.bin').read_bytes()).hexdigest() == capture['bin_sha256']
    rows = capture['state_samples']
    playing = [r for r in rows if r['menu_screen'] == 1]
    assert all(r['x_fp'] == 0 and r['z_fp'] == 0 and r['state'] == 0 for r in playing)
    assert all(r['player_respawn_events'] == 0 and r['audio_cd_errors'] == 0 for r in rows)
    shots = {}
    for frame, yaw in [(650, 0), (1250, 1024), (1850, 2048), (2450, 3072)]:
        row = next(r for r in rows if r['frame'] == frame)
        assert row['yaw'] & 4095 == yaw and row['mascot_visible'] == 1
        assert row['camera_distance'] == 420
        shots[str(frame)] = {'yaw': yaw, 'image_sha256': hashlib.sha256((folder / f'frame_{frame:04d}.png').read_bytes()).hexdigest()}
    return {'frames': 2900, 'bin_sha256': capture['bin_sha256'],
            'camera_distance': 420, 'four_sides': shots,
            'emulator': capture['emulator'],
            'limitation': 'Real PS1 emulator gameplay with an optional close camera; no original Unity reference comparison'}


if __name__ == '__main__':
    print(json.dumps(check(sys.argv[1]), indent=2))
