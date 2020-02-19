Azure Monitor Samples
=====================

This package holds sample applications that demonstrate the usage of Azure Monitor exporters in OpenCensus.

Installation
------------

Install OpenCensus Azure Monitor samples through `pip`.

`pip install opencensus-azure-monitor-samples`


Flask Sample
------------

The Azure Monitor Flask sample is a simple "To-Do" application. It is a `Flask <https://www.palletsprojects.com/p/flask/>`_ web application that runs a web server on the local machine. The application makes calls to a local database using the `SQLAlchemy <https://pypi.org/project/SQLAlchemy/>`_ library which supports popular databases such as SQLite, MySQL and MS-SQL. The sample application uses a sqlite database by default, but you may configure the `config.py` file to point to a database of your choosing.
 
^^^^^^^^^^^^^

To send telemetry to Azure Monitor, pass in your instrumentation key into `INSTRUMENTATION_KEY` in `config.py`.

.. code:: python

    INSTRUMENTATION_KEY = <your-ikey-here>


The default database URI links to a sqlite database `app.db`. To configure a different database, you can modify `config.py` and change the `SQLALCHEMY_DATABASE_URI` value to point to a database of your choosing.

.. code:: python

    SQLALCHEMY_DATABASE_URI = <your-database-URI-here>


Usage
^^^^^

1. Navigate to where `sample.py` is located
2. Set the flask app to your environment variable via `export FLASK_APP=sample.py` on Linux or `set FLASK_APP=sample.py` on Windows.
3. Run the application locally via `flask run` on the command line.
4. Hit your local endpoint (should be http://localhost:5000). This should open up a browser to the main page.
5. On the newly opened page, you can add tasks via the textbox under `Add a new todo item:`. You can enter any text you want (cannot be blank).
6. Click `Add Item` to add the task. The task will be added under `Incomplete Items`.
7. Each task has a `Mark As Complete` button. Clicking it will move the task from incomplete to completed.
8. You can also hit the `blacklist` url page to see a sample of a page that does not have telemetry being sent (http://localhost:5000/blacklist).

Telemetry
^^^^^^^^^

There are various types of telemetry that are being sent in the sample application. Refer to `Telemetry Type in Azure Monitor <https://docs.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python#telemetry-type-mappings>`_. Every button click hits an endpoint that exists in the flask application, so they will be treated as incoming requests (`requests` table in Azure Monitor). A log message is also sent every time a button is clicked, so a log telemetry is sent (`traces` table in Azure Monitor). A counter metric is recorded every time the `add` button is clicked. Metric telemetry is sent every interval (default 15.0 s, `customMetrics` table in Azure Monitor).
