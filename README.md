[![Build Status](https://travis-ci.org/18F/tts-bug-bounty-dashboard.svg?branch=master)](https://travis-ci.org/18F/tts-bug-bounty-dashboard)

This is a prototype dashboard for
[TTS's bug bounty program][bugbounty] with [HackerOne][].

![dashboard screenshot](https://user-images.githubusercontent.com/124687/27661558-ba643ba6-5c28-11e7-982a-b0fa1b80bed7.png)

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

## Deployment

### Via Docker Machine

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

### Via cloud.gov

These instructions assume that you want to deploy to the GovCloud instance
of cloud.gov.

Most of the cloud.gov configuration is documented in the `manifest.yml`
file at the root of the repository. Note that it mentions two applications:

* `bbdash-dev` is the main web-facing app that handles incoming HTTP requests.

* `bbdash-scheduler` is the worker that runs `manage.py runscheduler`.

#### Log in to cloud.gov and target a space

1. If you haven't already, download the Cloud Foundry CLI according to
   the [cloud.gov instructions][].

2. Login via the GovCloud api of cloud.gov using
   `cf login -a api.fr.cloud.gov --sso`.

3. Target the org and space you want to work with, e.g.
   `cf target -o my-org -s my-space`.

[cloud.gov instructions]: https://docs.cloud.gov/getting-started/setup/

#### Create a database

Run the following:

```
cf create-service aws-rds shared-psql bbdash-db
```

Note that you may want to use a different [AWS RDS plan][] than
`shared-psql` if you actually have money.

[AWS RDS plan]: https://cloud.gov/docs/services/relational-database/

#### Create a cloud.gov identity provider

Run the following:

```
cf create-service cloud-gov-identity-provider \
  oauth-client bbdash-uaa-client \
  -c '{"redirect_uri": ["https://bbdash-dev.app.cloud.gov"]}'
```

Note that if your app doesn't get deployed to `bbdash-dev.app.cloud.gov`,
you'll want to change that hostname.

Now create a service key to get  the values you want
to set `UAA_CLIENT_ID` and `UAA_CLIENT_SECRET` to when you configure your
app (which you'll do very soon):

```
cf create-service-key bbdash-uaa-client bbdash-uaa-service-key -c '{"redirect_uri": ["https://bbdash-dev.app.cloud.gov"]}'
cf service-key bbdash-uaa-client bbdash-uaa-service-key
```

#### Create a User Provided Service (UPS)

For cloud.gov deployments, this project makes use of a
[User Provided Service (UPS)][UPS] to get its configuration variables,
instead of using the local environment.

First, create a JSON file called `credentials-dev.json` with all the
configuration values specified as per the environment variables
documented in this `README`. **DO NOT COMMIT THIS FILE.**

```json
{
  "SECRET_KEY": "my secret key",
  "...": "other environment variables"
}
```

Then enter the following commands to create the user-provided service:

```sh
cf cups bbdash-env -p credentials-dev.json
```

[UPS]: https://docs.cloudfoundry.org/devguide/services/user-provided.html

#### Push the app

At this point you should be ready to deploy the app to cloud.gov.

You can do this by running:

```
cf push -f manifest.yml
```

At this point your app should be live, but if you ran into problems, see
the troubleshooting section below.

#### Create an initial superuser

You will need to create a superuser account, after which you'll be able
to login to the Django admin panel. The easiest way to create
the initial superuser is to use `cf ssh` to get to the remote host
and run `python manage.py createsuperuser`. You'll need to do some environment
setup on the remote host, as described at [Cloud Foundry's SSH docs][cf-ssh].

[cf-ssh]: https://docs.cloudfoundry.org/devguide/deploy-apps/ssh-apps.html#ssh-env

#### Updating the User Provided Service (UPS)

If you need to, you can update the user-provided service with the
following commands:

```sh
cf uups bbdash-env -p credentials-dev.json
```

Note that if you do this and the app is already running, you'll need to
restage it with `cf restage`.

#### Logs

Logs in cloud.gov-deployed applications are generally viewable by running
`cf logs <APP_NAME> --recent`.

Note that each application has a separate log, so you will need to look at
each individually.

#### Troubleshooting

* Problem: Deploying the app fails with an error message about not finding
  `DATABASE_URL`.

  cloud.gov is supposed to provide this environment variable on its own,
  but sometimes it doesn't. You can find the appropriate value by running
  `cf env bbdash-dev` and looking for a `postgres://` URL. Then set this
  as the value for `DATABASE_URL` in your `credentials-dev.json` and
  update your UPS.

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
