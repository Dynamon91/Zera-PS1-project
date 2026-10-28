# Pickup trial timer and best run

The optional development trial now displays SIM TIME and BEST. Time counts
simulation updates at a nominal 30 Hz, not wall-clock time or measured FPS.
New native run: **6/6 pickups**, best **2.0 simulation seconds**
(61 ticks). Source: `967a963041c01478f04d97005fa5e1dcc22703f9`.

| Completed run | Fresh run with best preserved |
| --- | --- |
| ![Completed trial](screenshots/trial/completed.png) | ![Trial restart](screenshots/trial/restart.png) |

The 1,650-frame HLE scenario verifies completion, frozen completed time, manual
respawn preserving score/time, restart resetting the timer while preserving best,
and return to title clearing the record. Host tests cover pause freeze and
slower/faster records. No memory-card save is implemented. Placements, scoring
and timing are PS1 test content; this is not original recovered progression.
