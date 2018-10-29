# nino-server


### Requirements
* Python 3.7

### Installation
* `pip install -r requirements.txt`

### Running Server
Local
* `python manage.py runserver`

Remote (i.e. Google Cloud)
* `sudo env PATH="$PATH" python manage.py runserver 0.0.0.0:8000`

### Migrating Database
Migrating is needed after modifying the models etc.
* `python manage.py makemigrations`
* `python manage.py migrate`

### Creating Admin User
* `python manage.py createsuperuser --email admin@example.com --username admin`