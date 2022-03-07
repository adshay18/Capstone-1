# Capstone-1
Large Capstone Project incorporating all skills learned so far, focusing on CRUD.
## Link to API
- https://www.pexels.com/api/documentation/
## Set up app
- Create virtual environement and setup relational database - app was made using PostgreSQL
```
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ createdb picl
```
- Visit api and register for key
- Make secret.py file and write the following code:
```
API_key = 'YOUR_KEY_HERE'
base_url = 'https://api.pexels.com/v1/'
my_headers = {'Authorization' : f'Bearer {API_key}'}
```

- Install requirements:
```
(venv) $ pip install -rf requirements.txt
```
- May need to install manually depending on your version of python and pip
