#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
check_dir=$(mktemp -d)
trap 'rm -rf "$check_dir"' EXIT
cd "$project_dir"
python3 tools/test_character_rotations.py
python3 tools/check_world_atlas.py
python3 tools/test_atlas_materials.py
for module in player collision camera clip menu animator trial surface; do
 cc -Wall -Wextra -Werror -fsanitize=address,undefined "src/$module.c" "tools/test_$module.c" -o "$check_dir/$module"
 ASAN_OPTIONS=detect_leaks=0 "$check_dir/$module"
done
cc -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/world.c src/collision.c src/camera.c tools/test_world.c -o "$check_dir/world"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/world"
cc -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/player.c src/world.c src/collision.c tools/test_exploration.c -o "$check_dir/exploration"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/exploration"
cc -Wall -Wextra -Werror -fsanitize=address,undefined src/clip.c tools/test_render_cells.c -o "$check_dir/render_cells"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/render_cells"
cc -Wall -Wextra -Werror -fsanitize=address,undefined src/clip.c tools/fixtures/clip_reference.c tools/test_clip_equivalence.c -o "$check_dir/clip_equivalence"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/clip_equivalence"
cc -Wall -Wextra -Werror -fsanitize=address,undefined src/collision.c tools/fixtures/collision_reference.c tools/test_collision_equivalence.c -o "$check_dir/collision_equivalence"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/collision_equivalence"
cc -DZERA_LEVEL3_PREVIEW -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/player.c src/surface.c src/world.c src/collision.c src/menu.c tools/test_level3.c -o "$check_dir/level3"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/level3"
cc -DZERA_LEVEL3_PREVIEW -Wall -Wextra -Werror -fsanitize=address,undefined src/clip.c tools/test_render_cells.c -o "$check_dir/level3_cells"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/level3_cells"
cc -Wall -Wextra -Werror -fsanitize=address,undefined tools/test_character.c -o "$check_dir/character"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/character"
cc -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/character.c tools/test_character_motion.c -o "$check_dir/character_motion"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/character_motion"
printf 'Host checks passed\n'
cc -DZERA_LEVEL3_PREVIEW -DZERA_LAUNCH_PREVIEW -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/launch.c src/player.c src/surface.c src/world.c src/collision.c tools/test_launch.c -o "$check_dir/launch"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/launch"
cc -DZERA_LAUNCH_PREVIEW -Wall -Wextra -Werror -fsanitize=address,undefined src/clip.c tools/test_render_cells.c -o "$check_dir/launch_cells"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/launch_cells"
printf 'Launch trajectory, landing, cancellation and render-cell checks passed\n'

cc -Wall -Wextra -Werror -fsanitize=address,undefined src/relics.c tools/test_relics.c -o "$check_dir/relics"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/relics"
cc -DZERA_LEVEL3_PREVIEW -DZERA_LAUNCH_PREVIEW -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/relics.c src/launch.c src/player.c src/world.c src/surface.c src/collision.c tools/test_relic_routes.c -o "$check_dir/relic_routes"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/relic_routes"
cc -Wall -Wextra -Werror -fsanitize=address,undefined tools/test_relic_models.c -o "$check_dir/relic_models"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/relic_models"
cc -DZERA_LEVEL3_PREVIEW -DZERA_CHECKPOINT_PREVIEW -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/checkpoint.c src/player.c src/world.c src/surface.c src/collision.c tools/test_checkpoint.c -o "$check_dir/checkpoint"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/checkpoint"
printf 'Checkpoint activation, respawn and reset checks passed\n'
cc -DZERA_LEVEL3_PREVIEW -DZERA_CORRIDOR_RELICS -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/relics.c src/player.c src/world.c src/surface.c src/collision.c tools/test_corridor_relic.c -o "$check_dir/corridor_relic"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/corridor_relic"
printf 'Original corridor relic route and collection checks passed\n'
cc -Wall -Wextra -Werror -fsanitize=address,undefined tools/test_corridor_relic_model.c -o "$check_dir/corridor_relic_model"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/corridor_relic_model"
cc -DZERA_LEVEL3_PREVIEW -DZERA_CORRIDOR_RELICS -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/checkpoint.c src/relics.c src/player.c src/world.c src/surface.c src/collision.c tools/test_connected_checkpoint.c -o "$check_dir/connected_checkpoint"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/connected_checkpoint"
printf 'Connected relic route, checkpoint and respawn checks passed\n'

python3 tools/check_stream_collision.py
cc -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/stream_world.c src/stream_collision_cache.c src/player.c src/surface.c src/collision.c tools/test_stream_world.c -o "$check_dir/stream_world"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/stream_world"

python3 tools/prepare_stream_progress.py --check
cc -DZERA_STREAM_RELICS -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/checkpoint.c src/relics.c src/player.c src/stream_world.c src/stream_collision_cache.c src/surface.c src/collision.c tools/test_stream_progress.c -o "$check_dir/stream_progress"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/stream_progress"

python3 tools/check_frontend_assets.py
cc -Wall -Wextra -Werror -fsanitize=address,undefined src/frontend.c tools/test_frontend.c -o "$check_dir/frontend"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/frontend"

python3 tools/check_model_guard.py

python3 tools/check_stream_collision.py --area previews/cosmic
cc -DZERA_CAMPAIGN_ENTRY -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/stream_world.c src/stream_collision_cache.c src/player.c src/surface.c src/collision.c tools/test_cosmic_world.c -o "$check_dir/cosmic"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/cosmic"
cc -DZERA_CAMPAIGN_ENTRY -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/frontend.c tools/test_campaign_frontend.c -o "$check_dir/campaign_frontend"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/campaign_frontend"

python3 tools/check_frontend_ui.py

python3 tools/check_levium.py
cc -DZERA_CAMPAIGN_ENTRY -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined src/dialogue.c src/player.c src/stream_world.c src/stream_collision_cache.c src/surface.c src/collision.c tools/test_levium.c -o "$check_dir/levium"
ASAN_OPTIONS=detect_leaks=0 "$check_dir/levium"
