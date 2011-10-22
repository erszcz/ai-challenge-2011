#!/usr/bin/env sh
./playgame.py \
  --player_seed 42 \
  --end_wait=0.25 \
  --verbose \
  --log_dir game_logs \
  --turns "$TURNS" \
  --map_file maps/multi_hill_maze/multi_maze_07.map \
  "$@"
