"""Plot recovered source coordinates; this image is not a gameplay screenshot."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root = Path(__file__).resolve().parents[1]
report = json.loads((root / 'reports/progression_recovery.json').read_text())
fig, axes = plt.subplots(2, 2, figsize=(10, 10), layout='constrained')
for ax, scene in zip(axes.flat, [s for s in report['scenes'] if s['scene'] in ('level3', 'level4', 'level5', 'level6')]):
    for kind, color, marker, size in [('Relic', '#ba7300', 'o', 20), ('Essence', '#285ac2', 'D', 30), ('Checkpoint', '#bf2459', 'P', 80)]:
        points = [e['source_world_position'] for e in scene['entries'] if e['kind'] == kind]
        ax.scatter([p[0] for p in points], [p[2] for p in points], s=size, c=color, marker=marker, label=kind, alpha=.85)
    starts = scene['start_spawns']
    ax.scatter([p['source_world_position'][0] for p in starts], [p['source_world_position'][2] for p in starts], s=110, c='#18865d', marker='*', label='Named start')
    ax.set(title=scene['scene'], xlabel='Unity world X', ylabel='Unity world Z', aspect='equal')
    ax.grid(alpha=.2)
handles, labels = axes.flat[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='outside lower center', ncol=4)
fig.suptitle('Recovered original progression placements\nSource-coordinate map — no terrain, routes or trigger volumes shown', fontsize=14)
out = root / 'docs/images/original_progression.png'
out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=110)
print(out)
