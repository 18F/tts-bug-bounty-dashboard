This is a prototype dashboard for
[TTS's bug bounty program][bugbounty] with [HackerOne][].

## Prerequisites

You'll need Python 3.6 and [virtualenv][].

## Quick start

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
```

If you're on windows, run `pip install pypiwin32` too.

Now edit `.env` as needed and run:

```
bash resetdb.sh
```

Then start the server with `python manage.py runserver`.

## Developing with Docker

```
cp .env.sample .env
```

Now edit `.env` as needed and run:

```
bash docker-update.sh
docker-compose run app bash resetdb.sh
docker-compose up
```

Then visit localhost at the port defined by
`DOCKER_EXPOSED_PORT` in your `.env` file.

### Deploying to the cloud via docker-machine

The following assumes you're deploying to the cloud
via Amazon EC2.

```
docker-machine create aws-bugbounty --driver=amazonec2
eval $(docker-machine env aws-bugbounty)
export DOCKER_EXPOSED_PORT=80
cp docker-compose.cloud.yml docker-compose.override.yml
```

Now edit `docker-compose.override.yml` as needed and run:

```
bash docker-cloud-deploy.sh
bash docker-update.sh
docker-compose run app bash resetdb.sh
docker-compose up
```

## Syncing with HackerOne

To sync the app's database with HackerOne, run:

```
python manage.py h1sync
```

[bugbounty]: https://github.com/18F/tts-buy-bug-bounty
[HackerOne]: https://hackerone.com/
[virtualenv]: http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/
