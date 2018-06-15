#!/bin/bash -e

if [[ -z "$GHPAGES_REMOTE" ]]; then
    echo 'Please specify the remote on which to push the docs in $GHPAGES_REMOTE'
    exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
OLD_STASH_SHA=$(git rev-parse -q --verify refs/stash)
git stash --all
NEW_STASH_SHA=$(git rev-parse -q --verify refs/stash)

cd $(git rev-parse --show-toplevel)
pip install -e '.[all]'
make -C docs html

git branch -D gh-pages || true
git checkout --orphan gh-pages
git add -f docs/_build/html
git clean -fdx

mv docs/_build/html/* .
rm -rf docs
touch .nojekyll
git add .
git commit -m 'create github pages docs'
git push "$GHPAGES_REMOTE" gh-pages -f

git checkout "$CURRENT_BRANCH"
if [[ "$OLD_STASH_SHA" != "$NEW_STASH_SHA" ]]; then
    git stash pop
fi
