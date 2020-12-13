web: gunicorn -k eventlet -w 1 mole_backend.wsgi --log-file -
release: python manage.py flush, python manage.py migrate
