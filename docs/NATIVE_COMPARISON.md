# Confronto nativo WIP08 / sorgente WIP09

Sorgente compilato: `6bac3839b7f349a2cb96cffe7f654595b52ac8f0`. Catture reali PCSX-ReARMed, HLE BIOS,
interprete CPU e GPU software. Stesso percorso e stessi istanti di cattura.
Questo confronto verifica un caso della telecamera; non aggiunge livelli al gioco.

| Frame | Prima: WIP08 | Dopo: nuovo build WIP09 |
| --- | --- | --- |
| 359 | ![WIP08 frame 359](../diagnostics/wall_walk/frame_0359.png) | ![WIP09 frame 359](screenshots/wip09/frame_0359.png) |
| 700 | ![WIP08 frame 700](../diagnostics/wall_walk/frame_0700.png) | ![WIP09 frame 700](screenshots/wip09/frame_0700.png) |
| 1300 | ![WIP08 frame 1300](../diagnostics/wall_walk/frame_1300.png) | ![WIP09 frame 1300](screenshots/wip09/frame_1300.png) |
| 1599 | ![WIP08 frame 1599](../diagnostics/wall_walk/frame_1599.png) | ![WIP09 frame 1599](screenshots/wip09/frame_1599.png) |

Le differenze di posizione possono derivare dal nuovo comportamento della camera.
Le immagini non dimostrano prestazioni o compatibilità hardware.
Il build e tutte le catture sono scaricabili dagli artifact della relativa esecuzione
**Native PS1 preview** in GitHub Actions. Il vecchio disco in `disc/` resta WIP08.
Il pacchetto WIP09 source mantiene il suo stato esplicito: non sostituisce quel disco.

## Risultato osservato, non solo confronto visivo

| Dato registrato al frame 1300 | WIP08 | WIP09 |
| --- | ---: | ---: |
| X del personaggio, fixed point | 145152 | 145152 |
| Y del personaggio, fixed point | -9728 | -9728 |
| Z del personaggio, fixed point | 197888 | 197888 |
| Distanza camera | 420 | 152 |

La posizione del personaggio è identica. Il minimo della camera nell'intera
cattura passa da 420 a 151 unità. La camera rispetta l'ostacolo più vicino,
ma il primo piano del personaggio riduce la leggibilità: questa resta una
limitazione aperta, non una promessa di miglioramento visivo in ogni scena.

Compilazione e cattura: [esecuzione riuscita con build e screenshot](https://github.com/Dynamon91/Zera-PS1-project/actions/runs/40649620714).
I prossimi controlli sono selezione di un'inquadratura alternativa, leggibilità
vicino al personaggio e ripetizione degli altri scenari sul nuovo build.
