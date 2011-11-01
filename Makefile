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
		--map_file tools/maps/symmetric_random_walk/random_walk_08.map \
		--turntime 1000 \
		--log_input \
		--log_stderr \
		"python MyBot.py" \
		"python uploads/4/MyBot4.py" \
		"python uploads/4/MyBot4.py" \
		"python uploads/4/MyBot4.py" \
		"python uploads/4/MyBot4.py"

		#"python tools/sample_bots/python/LeftyBot.py" \
		#"python tools/sample_bots/python/LeftyBot.py" \
		#"python tools/sample_bots/python/LeftyBot.py" \
		#"python tools/sample_bots/python/LeftyBot.py"

zip:
	[ -f rszymczyszyn.zip ] && rm rszymczyszyn.zip; \
	zip rszymczyszyn.zip MyBot.py ants.py astar.py
