#!/bin/bash -e

retry() {
    "$@" || "$@" || exit 2
}

if [[ "$DOCKER_USERNAME" == "" ]] \
    || [[ "$TRAVIS_PULL_REQUEST" == "true" ]] \
    || [[ "$TRAVIS_BRANCH" != "master" ]];
then
    echo "Not in an official branch, skipping deploy"
    echo "TRAVIS_SECURE_ENV_VARS=$TRAVIS_SECURE_ENV_VARS"
    echo "TRAVIS_PULL_REQUEST=$TRAVIS_PULL_REQUEST"
    exit 0
fi

# fail on unset variables expansion
set -o nounset

VERSION=$(autosemver . version)
IFS=. read MAJOR MINOR MICRO <<<"$VERSION"

DOCKER_TAG="inspirehep/inspire-mitmproxy:$VERSION"
DOCKER_TAG_MINOR="inspirehep/inspire-mitmproxy:$MAJOR.$MINOR"
DOCKER_TAG_MAJOR="inspirehep/inspire-mitmproxy:$MAJOR"
DOCKER_TAG_LATEST="inspirehep/inspire-mitmproxy:latest"

echo "Building the image $DOCKER_TAG"
retry docker build . \
    -t "$DOCKER_TAG" \
    -t "$DOCKER_TAG_MINOR" \
    -t "$DOCKER_TAG_MAJOR" \
    -t "$DOCKER_TAG_LATEST"

echo "Logging into Docker Hub with user $DOCKER_USERNAME"
retry docker login \
    "--username=$DOCKER_USERNAME" \
    "--password=$DOCKER_PASSWORD"

echo "Pushing image to $DOCKER_TAG, $DOCKER_TAG_MINOR, $DOCKER_TAG_MAJOR, $DOCKER_TAG_LATEST"
retry docker push "$DOCKER_TAG"
retry docker push "$DOCKER_TAG_MINOR"
retry docker push "$DOCKER_TAG_MAJOR"
retry docker push "$DOCKER_TAG_LATEST"

echo "Logging out"
retry docker logout
