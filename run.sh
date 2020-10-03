# gunicorn --threads 5 --workers 1 --bind 0.0.0.0:4001 app:app

uvicorn app:app --reload