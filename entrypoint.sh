uvicorn app.routes:app1 --host 0.0.0.0 --port 8088 &
# Start Celery worker
celery -A app.routes worker --concurrency=10 --loglevel=info -Q app2_queue &
# Wait for all background processes to finish
wait