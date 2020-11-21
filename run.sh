#!/bin/bash

gunicorn -k eventlet -w 1 mole_backend.wsgi --log-file -
