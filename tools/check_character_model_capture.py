"""Verify the controller-only mascot rendering/animation smoke scenario.

This checks runtime coverage and provenance, not visual equivalence to Unity.
Inspect the exported emulator images for appearance.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(folder):
    folder = Path(folder)
    capture = json.loads((folder / 'capture.json').read_text())
    assert capture['frames_run'] == 2200 and capture['content'] == 'zera_wip09.cue'
    rows = capture['state_samples']
    playing = [r for r in rows if r.get('menu_screen') == 1]
    clips = sorted({r['animation_clip'] for r in playing})
    states = sorted({r['state'] for r in playing})
    assert clips == [0, 1, 2, 3] and {0, 1, 3}.issubset(states)
    assert all(r['player_respawn_events'] == 0 and r['audio_cd_errors'] == 0 for r in rows)
    assert rows[-1]['state'] == 0
    assert len({r['yaw'] for r in playing}) > 10
    binary = folder.parent / 'zera_wip09.bin'
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == capture['bin_sha256']
    sources = ['src/main.c', 'src/character.c', 'src/character.h',
               'tools/bake_animation.py', 'tools/character_rotations.py',
               'tools/test_character_rotations.py', 'reports/animation_conversion.json',
               'src/zera_mesh.h', 'src/zera_anim.h', 'src/mascot_materials.h',
               'tools/test_character_motion.c', 'tools/scenarios/character_model.json']
    return {
        'bin_sha256': capture['bin_sha256'], 'frames': 2200,
        'emulator': capture['emulator'], 'animation_clips_observed': clips,
        'player_states_observed': states, 'automatic_respawns': 0,
        'source_sha256': {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in sources},
        'geometry': {'packed_vertices': 412, 'triangles': 806, 'original_clips': 4},
        'corrections': ['Reject inward and edge-on projected mascot faces',
                        'Sort mascot faces by precise GTE depth within each coarse OT bucket',
                        'Keep eye and spot priority at equal precise depth'],
        'limitations': ['Visual inspection uses emulator screenshots; no original Unity reference comparison',
                        'Painter ordering remains approximate for intersecting triangles',
                        'Original shaders, soft eye alpha and animation transition graph remain incomplete',
                        'HLE only; hardware performance not certified'],
        'next_milestone': 'Recover and render the original checkpoint plant in the connected area',
    }


if __name__ == '__main__':
    print(json.dumps(check(sys.argv[1]), indent=2))
