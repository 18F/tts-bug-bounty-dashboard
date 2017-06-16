FROM python:3.6.1

RUN pip install virtualenv

# The following lines set up our container for being run in a
# cloud environment, where folder sharing is disabled. They're
# irrelevant for a local development environment, where the
# main app directory is mounted via folder share.

COPY . /bugbounty/
