docker build -t gamer-bot .
docker save gamer-bot:latest | gzip -c > gamer-bot.tar.gz