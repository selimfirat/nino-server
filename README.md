# nino-server


### Requirements
* Python 3.7
* Anaconda

### Installation
* `conda env create -f environment.yml`

### Migrating Database
* `python manage.py migrate` (Currently not needed, )

### Creating Admin User
* `python manage.py createsuperuser --email admin@example.com --username admin`