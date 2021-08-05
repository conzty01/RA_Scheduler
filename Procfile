release: python migrateDB.py
web: gunicorn scheduleServer:app
worker: python schedulerProcess.py