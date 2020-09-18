# SG Engineering Stream Hackathon - Backend Flask 

Currently running at [Heroku](https://short-url-prod.herokuapp.com/)

API Dashboard available at [Dashboard](https://short-url-prod.herokuapp.com/dashboard).

Credentials:
 
| Username  | Password |
| --------- | ---------|
| admin     | admin    |

Swagger-UI available at [Swagger-UI](https://short-url-prod.herokuapp.com/api/docs/). It's incomplete though.

This project is generated using python 3.

## Requirements
* Install postgresql server and python (postgresql v12 and python v3.8 has been used in this project)

## Getting delvelopment server ready
Run below commands
- `git clone https://github.com/sg-engr-stream/backend-flask`
- `pip install -r requirements.txt`

update database configuration at `environment` and `dboard`, and update system name in `app.py` and `services\psql_config.py`
- `python app.py`

API's should be running at http://localhost:5000/

Browse http://localhost:5000/, you should see 'Hello World!'.

## Add heroku origin and deploy
Create or own app using heroku cli (app name needs to be unique, below will not work)
- `heroku create app-stage --remote stage`
- `heroku create app-prod --remote prod`
- `git push stage master`
<br>or
- `git push prod master`

## CI/CD and Reports
- [Travis-CI](https://travis-ci.com/github/sg-engr-stream/backend-flask)
- [Codecov.io](https://codecov.io/gh/sg-engr-stream/backend-flask)
- [Codacy.com](https://app.codacy.com/gh/sg-engr-stream/backend-flask/dashboard)
