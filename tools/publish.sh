#!/bin/bash
# Publish this folder to wwinnieliu.com: the live site ends up exactly matching it,
# so files removed here also leave the site.
#   tools/publish.sh "what changed"
set -euo pipefail
cd "$(dirname "$0")/.."
MSG=${1:-Update portfolio}

[ -f CNAME ] || { echo "CNAME is missing, stopping: the domain would break."; exit 1; }

big=$(find . -path ./.git -prune -o -type f -size +95M -print)
[ -z "$big" ] || { echo "Too big for GitHub, stopping:"; echo "$big"; exit 1; }

git add -A
git diff --cached --quiet || git commit -q -m "$MSG" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"

git fetch -q origin main
if ! git merge-base --is-ancestor origin/main HEAD; then
  # GitHub has something this folder doesn't (a web upload). Keep its history, use this folder's files.
  echo "Files GitHub has that differ from this folder (this folder wins):"
  git diff --name-status HEAD origin/main | head -40
  git merge -q -s ours --allow-unrelated-histories -m "Publish: keep the site folder's files" origin/main
fi
git push -q origin HEAD:main
echo "Pushed $(git rev-parse --short HEAD)"

# wait for GitHub Pages to serve the new files
for i in $(seq 1 40); do
  ok=1
  for f in assets/projects.js assets/style.css assets/main.js index.html; do
    [ "$(curl -sL "https://wwinnieliu.com/$f?x=$(date +%s)" | shasum)" = "$(shasum < "$f")" ] || ok=0
  done
  if [ $ok = 1 ]; then echo "Live on wwinnieliu.com after about $((i * 15 - 15))s"; exit 0; fi
  sleep 15
done
echo "Pushed, but the live site had not updated after 10 minutes. Check the repo's Actions tab."
exit 1
