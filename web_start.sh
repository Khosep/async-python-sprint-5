#!/bin/sh

echo 'Waiting for the db'
sleep 2

cd ./src

echo 'Applying migrations'
alembic upgrade head

cd ..

echo 'Starting app'
gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8080 src.main:app



