This is a prototype dashboard for TTS's bug bounty
program with HackerOne.

## Quick start

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
```

Now edit `.env` as needed and run:

```
bash resetdb.sh
```

Then start the server with `python manage.py runserver`.

## Syncing with HackerOne

To sync the app's database with HackerOne, run:

```
python manage.py h1sync
```
