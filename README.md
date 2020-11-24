# Augmented Boardgame

## Backend Setup
For python/virtualenv setup see [this page](https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/development_environment).
We need at least python 3.6.

To install Django and socketio activate your virtualenv and execute `pip install -r requirements.txt` inside `augmented-boardgame/mole_backend`.

## Start Backend
```bash
python3 manage.py runserver
```

## Setup Heroku
- install Heroku cli
- $ heroku login 
- set remotes to git repo
```bash
heroku git:remote -a testmapbranch
git remote rename heroku heroku-staging

heroku git:remote -a ab-backend
```

## Staging new features to Heroku
- push feat/yourfeat testmapbranch repo to test if the branch works, our staging site
```bash
git push heroku-staging feat/yourfeat:master
```
- check https://testmapbranch.herokuapp.com/ if it works
- push to master
```bash
git push heroku master
```


## Access from web

See [here](https://gitlab.rz.htw-berlin.de/s0565666/augmented-boardgame/-/wikis/Serververbindung) for more information.
