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
1.  install Heroku cli
1.  $ heroku login 
1.  set remotes to git repo

```bash
heroku git:remote -a testmapbranch
git remote rename heroku heroku-staging

heroku git:remote -a ab-backend
```

## Staging new features to Heroku

1. push feat/yourfeat testmapbranch repo to test if the branch works, our staging site
```bash
git push heroku-staging feat/yourfeat:master
```
1. check https://testmapbranch.herokuapp.com/ if it works
1. push to master

```bash
git push heroku master
```


## Access from web

See [here](https://gitlab.rz.htw-berlin.de/s0565666/augmented-boardgame/-/wikis/Serververbindung) for more information.
