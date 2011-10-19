test-bot:
	[ -f debug.log ] && rm debug.log; \
	cd tools/ && ./test_bot.sh "python ../MyBot.py 2> ../debug.log"

test-game:
	[ -f debug.log ] && rm debug.log; \
	cd tools/ && ./play_one_game.sh \
	"python ../MyBot.py 2> ../debug.log" \
	"python sample_bots/python/LeftyBot.py" \
	"python sample_bots/python/HunterBot.py" \
	"python sample_bots/python/GreedyBot.py"

zip:
	[ -f rszymczyszyn.zip ] && rm rszymczyszyn.zip; \
	zip rszymczyszyn.zip MyBot.py ants.py
