#!/bin/bash
pip install -r requirements.txt

# Produção: gunicorn (WSGI). Sem gunicorn: modo dev (python app.py)
if command -v gunicorn >/dev/null 2>&1; then
    echo "Iniciando em produção (gunicorn)..."
    exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
else
    echo "gunicorn não encontrado, iniciando em desenvolvimento..."
    exec python app.py
fi
