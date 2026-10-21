#!/data/data/com.termux/files/usr/bin/bash
set -eu
cd "$HOME/ROOTGHOST"
if [ ! -f ".env" ]; then
  echo "[ERROR] Falta .env. Ejecuta bash ~/ROOTGHOST/rootghost_fix.sh primero."
  exit 1
fi
set -a
. ./.env
set +a
exec python bot.py
