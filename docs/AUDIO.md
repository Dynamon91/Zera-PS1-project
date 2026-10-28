# Audio on/off — native verification

Source: `c0419aead40c27d3e5d404a6b650c9eb5b072c45`. Build hash: `83167ee91a49db0724fb691865f711b0ed8ea7fcd31a4271c2c00f7709ab53d1`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **709.557** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
