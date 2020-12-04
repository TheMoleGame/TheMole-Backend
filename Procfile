web: gunicorn -k eventlet -w 1 mole_backend.wsgi --log-file -
release: python manage.py makemigrations; python manage.py migrate
