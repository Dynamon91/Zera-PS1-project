"""Regression for the pelvis twist, using the recovered source Transform.

The expected quaternion is serialized in level2, not computed by the helper.
"""
import json
from pathlib import Path
from math import acos, degrees, sqrt, sin, cos, radians
from character_rotations import source_euler_quaternion

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'assets/character_animation_source.json').read_text())
pelvis = next(n for n in source['nodes'].values() if n['path'] == 'Armature/Pelvis')
expected = [0.4756084382534027, 0.47560828924179077,
            -0.5232559442520142, 0.5232558250427246]
assert max(abs(a-b) for a,b in zip(pelvis['quat'], expected)) < 1e-7
# Serialized Idle frame-zero Euler curve for that same pelvis.
euler = [5.889841486350633e-05, 84.53792572021484, -89.99995422363281]
actual = source_euler_quaternion(euler)
def angle_error(a, b):
    norm = sqrt(sum(v*v for v in a) * sum(v*v for v in b))
    return degrees(2*acos(min(1, abs(sum(x*y for x,y in zip(a,b)) / norm))))

error = angle_error(expected, actual)
assert error < 0.001, error
legacy = [-0.47560787, 0.47560879, -0.52325591, 0.52325585]
legacy_error = angle_error(expected, legacy)
assert legacy_error > 100, legacy_error
for euler in ([0, 0, 0], [90, 0, 0], [0, 90, 0], [0, 0, 90]):
    # Single-axis cases remain identical; only composed rotations were broken.
    reference = [sin(radians(v)/2) for v in euler] + [cos(radians(sum(euler))/2)]
    assert angle_error(source_euler_quaternion(euler), reference) < 0.00001
report = json.loads((ROOT / 'reports/animation_conversion.json').read_text())
assert report['renderer_scene'] == 'level2' and report['renderer_path_id'] == 5571
assert report['packed_vertices'] == 412 and report['unmatched_bindings'] == []
print(json.dumps({'source_pelvis_error_degrees': float(error),
                  'previous_pelvis_error_degrees': float(legacy_error),
                  'renderer_scene': 'level2', 'renderer_path_id': 5571}))
