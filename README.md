# nino-server


### Requirements
* Python 3.7
* Anaconda

### Installation
* `conda env create -f environment.yml`

### Migrating Database
Migrating is needed after modifying the models etc.
* `python manage.py makemigrations`
* `python manage.py migrate`

### Creating Admin User
* `python manage.py createsuperuser --email admin@example.com --username admin`