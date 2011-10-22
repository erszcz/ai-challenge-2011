TURNS = 500

test-bot:
	[ -f debug.log ] && rm debug.log; \
	cd tools/ && ./test_bot.sh "python ../MyBot.py"

test-game:
	export TURNS=$(TURNS); \
	[ -f debug.log ] && rm debug.log; \
	cd tools/ && ./play_one_game.sh \
		--turntime 1000 \
		--log_error \
		--log_stderr \
		"python ../MyBot.py" \
		"python sample_bots/python/LeftyBot.py" \
		"python sample_bots/python/LeftyBot.py" \
		"python sample_bots/python/LeftyBot.py"

zip:
	[ -f rszymczyszyn.zip ] && rm rszymczyszyn.zip; \
	zip rszymczyszyn.zip MyBot.py ants.py astar.py
