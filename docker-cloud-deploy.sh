#! /bin/bash

set -e

git archive --format=tar.gz --prefix=bugbounty/ HEAD > bugbounty.tgz
docker-machine scp bugbounty.tgz ${DOCKER_MACHINE_NAME}:
docker-machine ssh ${DOCKER_MACHINE_NAME} 'rm -rf bugbounty/* && tar -zxvf bugbounty.tgz'
rm bugbounty.tgz

echo "Deployed application to ${DOCKER_MACHINE_NAME}."
