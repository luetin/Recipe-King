#!/bin/sh
# Backs up the RecipeKing Postgres database to backups/recipeking_<timestamp>.sql.
# Run from the project root on the Debian server: ./scripts/backup.sh
set -e

cd "$(dirname "$0")/.."
set -a
. ./.env
set +a

mkdir -p backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT="backups/recipeking_${TIMESTAMP}.sql"

docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$OUT"

echo "Backup saved to $OUT"
