cmake_minimum_required(VERSION 3.21)
project(ZeraPS1 LANGUAGES C CXX ASM)
psn00bsdk_add_executable(zera GPREL src/main.c src/player.c src/world.c src/collision.c src/camera.c src/clip.c src/animator.c src/menu.c src/audio.c src/stream.c src/trial.c)
psn00bsdk_add_cd_image(iso zera_wip09 iso.xml DEPENDS zera system.cnf assets/audio/MUSIC.VAG)

# Separate executable/disc: preserve the established level2 WIP09 build.
psn00bsdk_add_executable(zera_level3 GPREL src/main.c src/player.c src/world.c src/collision.c src/camera.c src/clip.c src/animator.c src/menu.c src/audio.c src/stream.c src/trial.c)
target_compile_definitions(zera_level3 PRIVATE ZERA_LEVEL3_PREVIEW=1)
psn00bsdk_add_cd_image(iso_level3 zera_level3_preview iso_level3.xml DEPENDS zera_level3 system.cnf assets/audio/MUSIC.VAG)
