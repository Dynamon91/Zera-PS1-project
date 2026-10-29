#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
check_dir=$(mktemp -d)
trap 'rm -rf "$check_dir"' EXIT
cd "$project_dir"
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
