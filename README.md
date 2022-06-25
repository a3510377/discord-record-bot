# discord record bot

## setup

```sh
pip install pipenv
pipenv install # or $ pipenv install --dev
pipenv shell
```

## start

### python

```sh
python -m record
```

### docker

<!-- 
```sh
# build
pipenv lock -r > requirements.txt
docker build -t record-bot . --no-cache
# run
docker run -e DISCORD_TOKEN={your token} -d record-bot
``` -->
