#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
check_dir=$(mktemp -d)
trap 'rm -rf "$check_dir"' EXIT
cd "$project_dir"
for module in player collision camera clip menu animator trial; do
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
printf 'Host checks passed\n'
