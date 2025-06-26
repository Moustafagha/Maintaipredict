web: gunicorn --bind 0.0.0.0:$PORT src.main:app
worker: python -m src.services.background_worker
release: python -m src.scripts.migrate_db

