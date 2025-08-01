#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Create staticfiles directory if it doesn't exist
mkdir -p staticfiles

# Otimizar arquivos estáticos
python manage.py optimize_static --force

# Apply any outstanding database migrations
python manage.py migrate

# Configurar cache
python manage.py setup_cache

# Verificar configurações
python manage.py check --deploy