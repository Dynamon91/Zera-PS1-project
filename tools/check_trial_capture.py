"""Verify optional trial timing, score preservation, restart and title reset."""
import json
import os
from pathlib import Path
import shutil
import sys

root=Path(__file__).resolve().parent.parent
directory=Path(sys.argv[1]);report=json.loads((directory/'capture.json').read_text())
assert report['frames_run']==1650
rows=report['state_samples'];by_frame={r['frame']:r for r in rows}
completed=next((r for r in rows if r['trial_complete']),None)
assert completed is not None and completed['trial_count']==6
best=completed['trial_best_ticks']
assert completed['trial_best_valid']==1 and best==completed['trial_ticks'] and best>0
respawn=by_frame[1100]
assert respawn['trial_complete']==1 and respawn['trial_count']==6
assert respawn['trial_best_ticks']==best and respawn['trial_ticks']==best
assert respawn['x_fp']==0 and respawn['z_fp']==0, 'manual respawn did not reset player'
restart=by_frame[1310]
assert restart['trial_active']==1 and restart['trial_count']==0 and restart['trial_complete']==0
assert restart['trial_ticks']<best and restart['trial_best_ticks']==best and restart['trial_best_valid']==1
title=by_frame[1649]
assert title['menu_screen']==0 and title['trial_active']==0 and title['trial_best_valid']==0
assert title['trial_best_ticks']==0
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':report['bin_sha256'],
        'completed_pickups':6,'first_best_ticks':best,'simulation_hz':30,
        'respawn_preserves_score_and_time':True,'restart_preserves_best':True,
        'return_to_title_clears_best':True,'emulator':report['emulator'],
        'validation':'Optional development trial in HLE; not original authored progression'}
out=root/'docs/screenshots/trial';out.mkdir(parents=True,exist_ok=True)
shots=[r for r in rows if r['trial_complete'] and r['menu_screen']==1 and (directory/f"frame_{r['frame']:04d}.png").is_file()]
assert shots, 'no actual completed-trial screenshot'
shutil.copyfile(directory/f"frame_{shots[0]['frame']:04d}.png",out/'completed.png')
shutil.copyfile(directory/'frame_1310.png',out/'restart.png')
shutil.copyfile(directory/'capture.json',out/'capture.json')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
tenths=best//3
(root/'docs/TRIAL.md').write_text(f'''# Pickup trial timer and best run

The optional development trial now displays SIM TIME and BEST. Time counts
simulation updates at a nominal 30 Hz, not wall-clock time or measured FPS.
New native run: **6/6 pickups**, best **{tenths//10}.{tenths%10} simulation seconds**
({best} ticks). Source: `{result['source_commit']}`.

| Completed run | Fresh run with best preserved |
| --- | --- |
| ![Completed trial](screenshots/trial/completed.png) | ![Trial restart](screenshots/trial/restart.png) |

The 1,650-frame HLE scenario verifies completion, frozen completed time, manual
respawn preserving score/time, restart resetting the timer while preserving best,
and return to title clearing the record. Host tests cover pause freeze and
slower/faster records. No memory-card save is implemented. Placements, scoring
and timing are PS1 test content; this is not original recovered progression.
''')
print(json.dumps(result))
