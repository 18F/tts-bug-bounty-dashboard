[![Build Status](https://travis-ci.org/18F/tts-bug-bounty-dashboard.svg?branch=master)](https://travis-ci.org/18F/tts-bug-bounty-dashboard)

This is a prototype dashboard for
[TTS's bug bounty program][bugbounty] with [HackerOne][].

## Prerequisites

You'll need Python 3.6 and [virtualenv][].

## Quick start

```
virtualenv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.sample .env
```

Now edit `.env` as needed and run:

```
bash resetdb.sh
```

Then start the server with `python manage.py runserver`. When
you visit http://localhost:8000 and are prompted for an email address,
use:

* `root@gsa.gov` to simulate an administrator logging in;
* any other `@gsa.gov` email to simulate a non-staff user logging in;
* any other email to simulate a user who will be prevented from logging in.

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

## Running the scheduler

To run `h1sync` and other necessary tasks at periodic intervals,
run:

```
python manage.py runscheduler
```

Note that only *one* instance of this should ever be running at a time.

## Environment variables

Unlike traditional Django settings, we use environment variables
for configuration to be compliant with [twelve-factor][] apps.

You can define environment variables using your environment, or
(if you're developing locally) an `.env` file in the root directory
of the repository.

**Note:** When an environment variable is described as representing a
boolean value, if the variable exists with *any* value (even the empty
string), the boolean is true; otherwise, it's false.

* `DEBUG` is a boolean value that indicates whether debugging is enabled
  (this should always be false in production).

* `SECRET_KEY` is a large random value corresponding to Django's
  [`SECRET_KEY`][] setting. It is automatically set to a known, insecure
  value when `DEBUG` is true.

* `DATABASE_URL` is the URL for the database, as per the
  [DJ-Database-URL schema][]. When `DEBUG` is true, it defaults to a 
  sqlite file in the root of the repository called `db.sqlite3`.

* `EMAIL_URL` is the URL for the service to use when sending
  email, as per the [dj-email-url schema][]. When `DEBUG` is true,
  this defaults to `console:`. If it is set to `dummy:` then no emails will
  be sent and messages about email notifications will not be shown to users.
  The setting can easily be manually tested via the `manage.py sendtestemail`
  command.

* `DEFAULT_FROM_EMAIL` is the email from-address to use in all system
  generated emails to users. It corresponds to Django's
  [`DEFAULT_FROM_EMAIL`][] setting. It defaults to `noreply@localhost`
  when `DEBUG=True`.

* `H1_PROGRAM_n`, where `n` is an integer starting at 1, describes the
  configuration of the `n`th HackerOne program that you'd like the
  dashboard to track. Each configuration consists of the program
  handle, the API token identifier (aka API username), and API token
  value (aka API password), all delimited by colons.

  Thus for instance if you wanted to track two programs, `tts` and
  `tts-private`, each with their own separate API credentials, you might
  define `H1_PROGRAM_1=tts:foo:bar` and `H1_PROGRAM_2=tts-private:baz:quux`.

  For more details on the configuration parameters, see the
  [HackerOne API Authentication docs][h1docs].

* `UAA_CLIENT_ID` is your cloud.gov/Cloud Foundry UAA client ID. It
  defaults to `bugbounty-dev`.

* `UAA_CLIENT_SECRET` is your cloud.gov/Cloud Foundry UAA client secret.
  If this is undefined and `DEBUG` is true, then a built-in Fake UAA Provider
  will be used to "simulate" cloud.gov login.

## Running tests

This project uses [pytest][]/[pytest-django][] for tests and
[flake8][] for linting.

To run all tests with linting:

```
flake8 && pytest
```

[bugbounty]: https://github.com/18F/tts-buy-bug-bounty
[HackerOne]: https://hackerone.com/
[virtualenv]: http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/
[twelve-factor]: http://12factor.net/
[DJ-Database-URL schema]: https://github.com/kennethreitz/dj-database-url#url-schema
[dj-email-url schema]: https://github.com/migonzalvar/dj-email-url#supported-backends
[`DEFAULT_FROM_EMAIL`]: https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-DEFAULT_FROM_EMAIL
[`SECRET_KEY`]: https://docs.djangoproject.com/en/1.8/ref/settings/#secret-key
[h1docs]: https://api.hackerone.com/docs/v1#authentication
[pytest]: https://docs.pytest.org/
[pytest-django]: https://pytest-django.readthedocs.io/
[flake8]: http://flake8.pycqa.org/
