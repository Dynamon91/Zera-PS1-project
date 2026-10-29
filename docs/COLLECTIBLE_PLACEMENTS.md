# Original collectibles in playable preview areas

The launchpad area contains three original relic placements. Their values are
recovered serialized values, not a newly designed reward scheme.

| Original component | Value | PS1 X, Y, Z | Support floor Y | Height above floor |
| --- | ---: | --- | ---: | ---: |
| 6594 | 8 | −256, 1927, 786 | 1895 | 32 |
| 6596 | 8 | 678, 1927, 497 | 1895 | 32 |
| 7178 | 4 | −141, 106, −804 | 74 | 32 |

The two upper relics sit over the same Y=1895 platform used by the verified
launch landing. The lower relic sits over Y=74 terrain. Each location also has
another floor layer at its X/Z, so choosing the highest floor globally would
misplace the lower collectible. Selection here chooses the highest support below
the original item's Y, without changing its authored position.

This is a placement/provenance audit. A subsequent [collection prototype](RELIC_COLLECTION.md) now enables these three
placements and source values in the launchpad disc. Saving remains pending. Point-floor queries do not establish a traversable route
from the landing point to each relic. The separate level3 start patch contains
zero original Relic/Essence placements within its extraction bounds.

[Machine-readable positions and source hashes](../reports/preview_collectibles.json)
are generated from the existing original progression recovery and converted floor
triangles. Source hierarchy/component flags are retained; they do not prove runtime
availability. Coordinate rounding is to integer PS1 world units.

Reproduce or verify without the original Unity build or third-party packages:

```sh
python3 tools/audit_preview_collectibles.py
python3 tools/audit_preview_collectibles.py --check
```

CI reconstructs the report on every push and rejects drift. The next integration
step is to implement collection at these original positions, then test actual
routes and reward lifecycle. Full-port estimate remains 29%.
