"""Verify the unobstructed level3 jump regression, not a ceiling-hit proof."""
import hashlib
import json
from pathlib import Path
import sys


def check(folder):
    folder = Path(folder)
    capture = json.loads((folder / 'capture.json').read_text())
    assert capture['content'] == 'zera_level3_preview.cue'
    assert capture['frames_run'] == 1250
    rows = capture['state_samples']
    jumps = [r for r in rows if 980 <= r['frame'] <= 1249]
    assert [r['frame'] for r in jumps] == list(range(980, 1250))
    assert all(r['menu_screen'] == 1 and r['player_respawn_events'] == 0 for r in jumps)
    assert all(r['x_fp'] == 500 * 256 and r['z_fp'] == 0 for r in jumps)
    assert jumps[0]['state'] == 0 and jumps[0]['y_fp'] == 0
    assert max(r['y_fp'] for r in jumps) == 153 * 256
    assert any(r['state'] == 1 and r['vy_fp'] > 0 for r in jumps)
    assert any(r['state'] == 2 and r['vy_fp'] < 0 for r in jumps)
    assert all(r['y_fp'] >= 0 for r in jumps)
    assert jumps[-1]['state'] == 0 and jumps[-1]['y_fp'] == 0
    assert jumps[-1]['audio_cd_errors'] == 0 and jumps[-1]['audio_music_ready'] == 1
    binary = folder.parent / 'zera_level3_preview.bin'
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == capture['bin_sha256']
    return {'bin_sha256': capture['bin_sha256'], 'position': [500, 0, 0],
            'jump_peak': 153, 'automatic_respawns': 0, 'frames': 1250,
            'validation': 'Controller-only HLE unobstructed jump and landing regression; does not demonstrate an overhead collision'}


if __name__ == '__main__':
    print(json.dumps(check(sys.argv[1]), indent=2))
