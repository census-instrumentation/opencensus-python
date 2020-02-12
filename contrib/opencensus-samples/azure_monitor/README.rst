OpenCensus Samples
******************

This repository holds sample applications that demonstrate the various exporters that are supported in OpenCensus.

Azure Monitor Samples
=====================

Flask Sample
------------

The Azure Monitor Flask sample is a simple "To-Do" application.
It is a [Flask](https://www.palletsprojects.com/p/flask/) web application that runs a web server on the local machine.
The application makes calls to a local database using the [SQLAlchemy](https://pypi.org/project/SQLAlchemy/) library which supports popular databases such as SQLite, MySQL and MS-SQL.
The sample application uses a sqlite database by default, but you may configure the `config.py` file to point to a database of your choosing.

Setup
^^^^^

To send telemetry to Azure Monitor, pass in your instrumentation key into `INSTRUMENTATION_KEY` in `config.py`.

```python
config.py
...
INSTRUMENTATION_KEY = <your-ikey-here>
...
```

The default database URI links to a sqlite database `app.db`.
To configure a different database, you can modify `config.py` and change the `SQLALCHEMY_DATABASE_URI` value to point to a database of your choosing.

```python
config.py
...
SQLALCHEMY_DATABASE_URI = <your-database-URI-here>
...
```

Usage
^^^^^
