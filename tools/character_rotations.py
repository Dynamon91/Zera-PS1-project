"""Rotation convention of the recovered Zera transform-animation bindings."""
from math import sin, cos, radians


def source_euler_quaternion(euler_xyz):
    """Serialized Zera Euler curves compose intrinsic Z-X-Y rotations.

    SciPy lowercase 'zxy' composes extrinsic rotations and twists the pelvis
    when both Y and Z are nonzero. The source Transform quaternion supplies
    an independent regression reference for this convention.
    """
    x, y, z = (radians(v) / 2 for v in euler_xyz)
    sx, cx, sy, cy, sz, cz = sin(x), cos(x), sin(y), cos(y), sin(z), cos(z)
    # Hamilton product qZ * qX * qY, quaternion components XYZW.
    return [cz*sx*cy - sz*cx*sy, cz*cx*sy + sz*sx*cy,
            cz*sx*sy + sz*cx*cy, cz*cx*cy - sz*sx*sy]
