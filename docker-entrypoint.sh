#!/bin/sh
set -e

alembic upgrade head
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 2
