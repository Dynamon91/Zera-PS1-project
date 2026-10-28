"""Validate real native captures before copying screenshots into documentation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from PIL import Image

root=Path(__file__).resolve().parent.parent
capture=Path(sys.argv[1]);binary=Path(sys.argv[2])
report=json.loads((capture/'capture.json').read_text())
assert report['frames_run']==1600, 'incomplete capture'
assert report['bin_sha256']==hashlib.sha256(binary.read_bytes()).hexdigest()
samples=report['state_samples']
assert any(s.get('menu_screen')==1 for s in samples), 'never entered gameplay'
assert all(0<=s.get('camera_distance',850)<=850 for s in samples)
assert all(s.get('audio_cd_errors',0)==0 for s in samples)
source=os.environ['GITHUB_SHA']
destination=root/'docs/screenshots/wip09';destination.mkdir(parents=True,exist_ok=True)
frames=[359,700,1000,1300,1410,1499,1599]
for frame in frames:
    name=f'frame_{frame:04d}.png';path=capture/name
    with Image.open(path) as image:
        assert image.size==(320,240), 'unexpected video dimensions'
        assert len(image.getcolors(320*240) or [])>16, 'blank video output'
    shutil.copyfile(path,destination/name)
shutil.copyfile(capture/'capture.json',destination/'capture.json')
metadata={'source_commit':source,'bin_sha256':report['bin_sha256'],
          'emulator':report['emulator'],'scenario':'tools/scenarios/native_wall_preview.json',
          'validation':'HLE smoke capture only; no retail BIOS or physical hardware test.'}
(destination/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
lines=['# Confronto nativo WIP08 / sorgente WIP09','',
       f'Sorgente compilato: `{source}`. Catture reali PCSX-ReARMed, HLE BIOS,',
       'interprete CPU e GPU software. Stesso percorso e stessi istanti di cattura.',
       'Questo confronto verifica un caso della telecamera; non aggiunge livelli al gioco.','',
       '| Frame | Prima: WIP08 | Dopo: nuovo build WIP09 |','| --- | --- | --- |']
for frame in (359,700,1300,1599):
    name=f'frame_{frame:04d}.png'
    lines.append(f'| {frame} | ![WIP08 frame {frame}](../diagnostics/wall_walk/{name}) | ![WIP09 frame {frame}](screenshots/wip09/{name}) |')
lines+=['','Le differenze di posizione possono derivare dal nuovo comportamento della camera.',
        'Le immagini non dimostrano prestazioni o compatibilità hardware.',
        'Il build e tutte le catture sono scaricabili dagli artifact della relativa esecuzione',
        '**Native PS1 preview** in GitHub Actions. Il vecchio disco in `disc/` resta WIP08.',
        'Il pacchetto WIP09 source mantiene il suo stato esplicito: non sostituisce quel disco.','']
if (root/'docs/screenshots/wip09-before-orbit/frame_1410.png').exists():
    lines += ['## Camera da fermo: prima e dopo la ricerca laterale', '',
              'Catture dello stesso scenario al frame 1410; i metadati dei due build sono conservati nelle rispettive cartelle.', '',
              '| WIP09 prima della ricerca laterale | WIP09 con ricerca laterale |',
              '| --- | --- |',
              '| ![Prima](screenshots/wip09-before-orbit/frame_1410.png) | ![Dopo](screenshots/wip09/frame_1410.png) |', '',
              'La ricerca si attiva solo da fermo, con pausa e controlli manuali prioritari. Non garantisce una vista libera in ogni angolo.', '']
(root/'docs/NATIVE_COMPARISON.md').write_text('\n'.join(lines))
print(json.dumps(metadata))
