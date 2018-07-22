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

## License

This project is licensed under the MPL 2.0 License - see the [LICENSE](LICENSE) file for details
