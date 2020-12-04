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
1.  install Heroku [cli](https://devcenter.heroku.com/articles/heroku-cli)
```bash
heroku login
``` 
2.  set remotes to git repo

 ```bash 
heroku git:remote -a testmapbranch
git remote rename heroku heroku-staging
heroku git:remote -a ab-backend
```

## Staging new features to Heroku

1. push your branch: feat/yourfeat to the remote staging heroku   
   The Heroku staging git-repo is called testmapbranch.  
   Test if the branch works on this repo.
```bash
git push heroku-staging feat/yourfeat:master
```
2. check https://testmapbranch.herokuapp.com/ if it works
3. Merge feature in master
4. push to master
```bash
git push heroku master
```
4. should be working on master https://ab-backend.herokuapp.com/


## Access from web

See [here](https://gitlab.rz.htw-berlin.de/s0565666/augmented-boardgame/-/wikis/Serververbindung) for more information.
