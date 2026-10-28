"""Original source placement map, not a gameplay screenshot or walkable-route proof."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]

def main():
    pads = next(s['entries'] for s in json.loads((ROOT/'reports/launchpad_recovery.json').read_text())['scenes'] if s['scene']=='level3')
    progress = next(s for s in json.loads((ROOT/'reports/progression_recovery.json').read_text())['scenes'] if s['scene']=='level3')
    preview = json.loads((ROOT/'previews/level3/reports/world_conversion.json').read_text())
    sx, sy, sz = preview['spawn']; r=preview['source_radius_units']
    fig, ax = plt.subplots(figsize=(9,8), layout='constrained')
    for kind, color, marker in [('Relic','#7d50b9','o'),('Essence','#bd7200','D'),('Checkpoint','#126f72','s')]:
        entries=[e for e in progress['entries'] if e['kind']==kind]
        ax.scatter([e['source_world_position'][0] for e in entries], [e['source_world_position'][2] for e in entries],s=28,c=color,marker=marker,label=kind,alpha=.7)
    ax.add_patch(Rectangle((sx-r,sz-r),2*r,2*r,facecolor='#dbe9d4',edgecolor='#50733b',label='Current PS1 patch (XZ bounds)'))
    ax.scatter([sx],[sz],marker='*',s=160,c='#284a25',zorder=6,label='Preview spawn')
    for e in pads:
        x,y,z=e['source_world_position']; lx,ly,lz=e['landing_point']
        ax.annotate('',xy=(lx,lz),xytext=(x,z),arrowprops={'arrowstyle':'->','color':'#bc242d','lw':2})
        ax.scatter([x],[z],marker='^',s=80,c='#bc242d',zorder=5)
        ax.annotate(f"Pad {e['component_path_id']}\nY {y:.1f} → {ly:.1f}",(x,z),xytext=(8,-32),textcoords='offset points',fontsize=9)
    ax.plot([],[],color='#bc242d',marker='^',label='Launchpad → saved landing point')
    ax.set(xlabel='Unity world X',ylabel='Unity world Z',title='Level 3 • original launchpad placements\nSource-data map — arrows show endpoints, not verified traversable routes')
    ax.set_aspect('equal',adjustable='datalim'); ax.grid(alpha=.2); ax.legend(loc='upper left',fontsize=8)
    fig.savefig(ROOT/'docs/images/level3_launchpads.png',dpi=140,metadata={'Software':'Zera PS1 source audit'})
    plt.close(fig)

if __name__=='__main__': main()
