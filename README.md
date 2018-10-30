# Bitcoin CLI GraphQL API

The GraphQL server for the Fort Bitcoin project.

## Prerequisites

You'll need to have Python3 and pip installed.

## Getting started

[Virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/en/latest/install.html) must be working properly on your system before continuing.

- clone the repository
- copy config.ini.sample to config.ini and adapt the values to your requirements
- add a new virtual environment: _mkvirtualenv fort-bitcoin-gql_
- _pip install -r requirements.txt_
- deactivate virtual environment to prevent some errors _deactivate_
- use the environment: _workon fort-bitcoin-gql_
- _./manage.py makemigrations_
- _./manage.py migrate_
- _./manage.py runserver_

Open http://localhost:8000/graphql to explore the available queries via GraphiQL.

## RabbitMQ 
For Celery you'll have to run a Broker which keeps background tasks going. Easiest way is to run RabbitMQ via Docker:
- _docker pull rabbitmq_
- _docker run --name rabbitmq --hostname fbtc-rabbitmq --restart=unless-stopped -d -p 5672:5672 -p 15672:15672 -v /chose/your/path/logs:/data/log -v /chose/your/path/data:/data/mnesia rabbitmq_
- open _config.ini_ and adjust _celery\_broker\_url_. If you run it on localhost and you kept the standard port  of _5672_ you can just keep the value at _amqp://localhost//_



There are other options than RabbitMQ, see the [docs](http://docs.celeryproject.org/en/latest/getting-started/brokers/)

## Celery
Run celery in screen or two new terminals. Make sure the virtual environment is applied and your are in the base folder of the project before running these commands.
- _celery worker -A backend --concurrency=4_
- _celery -A backend beat -l debug --scheduler django_celery_beat.schedulers:DatabaseScheduler_


## License

This project is licensed under the MPL 2.0 License - see the [LICENSE](LICENSE) file for details
