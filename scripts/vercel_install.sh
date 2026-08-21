#!/usr/bin/env bash
# Vercel install: pure-Python deps only. Flask-MySQLdb is installed with
# --no-deps because its mysqlclient wheel needs libmysqlclient and fails
# on the serverless builder. The app uses PyMySQL via install_as_MySQLdb().
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements-vercel.txt
python -m pip install --no-deps "Flask-MySQLdb==2.0.0"
