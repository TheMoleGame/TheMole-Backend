# The Mole
This repository is the backend part of a game called the mole.  
It was made as a student project for the student exhibition showtime.  
For more information see our showtime [page](https://showtime.f4.htw-berlin.de/ws20/master/m1-augmented-boardgame-experience/).
![Main game board 05 06](https://user-images.githubusercontent.com/7975579/120891879-3c16d000-c60b-11eb-9483-f800b31cf3cc.png)


## Backend Setup
For python/virtualenv setup see [this page](https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/development_environment).
We need at least python 3.6.

To install Django and socketio activate your virtualenv and execute `pip install -r requirements.txt` inside `augmented-boardgame/mole_backend`.

## Database Setup
1. Download and install PostgreSQL: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
	- Deactivate Stackbuilder
	- Port: 5432 (Default)
2. Install 'psycopg2' package, so Django can use the PostgreSQL database: `pip install psycopg2`
3. `python manage.py migrate`
4. `python manage.py createsuperuser`
5. Don't forget .env file for access to the local postgre
  
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
5. should be working on master https://ab-backend.herokuapp.com/


## Access from web

See [here](https://github.com/TheMoleGame/TheMole-Backend/wiki/Serververbindung) for more information.
