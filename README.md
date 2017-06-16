This is a prototype dashboard for TTS's bug bounty
program with Hacker One.

## Quick start

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
```

Now edit `.env` as needed and run:

```
python manage.py h1sync
```

Create a superuser with `python manage.py createsuperuser`.

Then start the server with `python manage.py runserver`.
