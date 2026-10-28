cmake_minimum_required(VERSION 3.21)
project(ZeraPS1 LANGUAGES C CXX ASM)
psn00bsdk_add_executable(zera GPREL src/main.c src/player.c src/world.c src/collision.c src/clip.c src/animator.c src/menu.c src/audio.c src/stream.c src/trial.c)
psn00bsdk_add_cd_image(iso zera_wip08 iso.xml DEPENDS zera system.cnf assets/audio/MUSIC.VAG)
