ifndef TURNS
	TURNS = 500
endif

test-bot:
	[ -f debug.log ] && rm debug.log; \
	cd tools/ && ./test_bot.sh "python ../MyBot.py"

test-game:
	[ -f debug.log ] && rm debug.log; \
	tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir tools/game_logs \
		--html replay.0.html \
		--nolaunch \
		--turns $(TURNS) \
		--map_file tools/maps/multi_hill_maze/multi_maze_07.map \
		--turntime 1000 \
		--log_input \
		--log_stderr \
		"python MyBot.py" \
		"python MyBot4.py" \
		"python MyBot4.py" \
		"python MyBot4.py"

zip:
	[ -f rszymczyszyn.zip ] && rm rszymczyszyn.zip; \
	zip rszymczyszyn.zip MyBot.py ants.py astar.py
