OpenCensus - A stats collection and distributed tracing framework
=================================================================

This is the open-source release of Census for Python. Census provides a
framework to measure a server's resource usage and collect performance stats.
This repository contains python related utilities and supporting software
needed by Census.

## Installation

1. Install the opencensus-trace package using pip

```
pip install opencensus-trace
```

2. Initialize a tracer to enable trace in your application

```python
from opencensus.trace.tracer import context_tracer

tracer = context_tracer.ContextTracer()
tracer.start_trace()
```

## Usage

There are two ways to trace your code blocks. One is using a `with` statement
to wrap your code, and the trace span will end when exit the `with` statement.
Another is explicitly start and finish the trace span before and after your
code block. Sample code for the two usages as below:

### Usage 1: `with` statement (Recommended)

```python
from opencensus.trace.tracer import context_tracer

# Initialize a tracer, by default using the `PrintReporter`
tracer = context_tracer.ContextTracer()
tracer.start_trace()

# Example for creating nested spans
with tracer.span(name='span1') as span1:
    do_something_to_trace()
    with span1.span(name='span1_child1') as span1_child1:
        do_something_to_trace()
    with span1.span(name='span1_child2') as span1_child2:
        do_something_to_trace()
with tracer.span(name='span2') as span2:
    do_something_to_trace()

# The trace spans will be sent to the reporter when you call `end_trace()`
tracer.end_trace()
```

### Usage 2: Explicitly start and end spans

```python
from opencensus.trace.tracer import context_tracer

# Initialize a tracer, by default using the `PrintReporter`
tracer = context_tracer.ContextTracer()
tracer.start_trace()

tracer.start_span(name='span1')
do_something_to_trace()
tracer.end_span()
```

## Customization

### Samplers

You can specify different samplers when initializing a tracer, default is using
`AlwaysOnSampler`, the other options are `AlwaysOffSampler` and
`FixedRateSampler`

```python
from opencensus.trace.samplers import fixed_rate
from opencensus.trace.tracer import context_tracer

# Sampling the requests at the rate equals 0.5
sampler = fixed_rate.FixedRateSampler(rate=0.5)
tracer = context_tracer.ContextTracer(sampler=sampler)
```

### Reporters

You can choose different reporters to send the traces to. Default is printing
the traces in JSON format. The rest options are sending to logging, or write
to a file. Will add reporters to report to different trace backend later.

```python
from opencensus.trace.reporters import file_reporter
from opencensus.trace.tracer import context_tracer

# Export the traces to a local file
reporter = file_reporter.FileReporter(file_name='traces')
tracer = context_tracer.ContextTracer(reporter=reporter)
```

Report to Stackdriver Trace:

```python
from opencensus.trace.reporters import google_cloud_reporter
from opencensus.trace.tracer import context_tracer

reporter = google_cloud_reporter.GoogleCloudReporter(
    project_id='your_cloud_project')
tracer = context_tracer.ContextTracer(reporter=reporter)
```

## Framework Integration

Opencensus supports integration with popular web frameworks including Django,
Flask and Webapp2. When the application receives a HTTP request, the tracer
will automatically generate a span context using the trace information
extracted from the request headers, and propagated to the child spans.
Below is the sample code snippets:

### Flask

```python
from opencensus.trace.tracer import flask_tracer

tracer = flask_tracer.FlaskTracer()
tracer.start_trace()

with tracer.span(name='span1'):
    do_something_to_trace()

tracer.end_trace()
```

### Django

For tracing Django requests, you will need to add the following line to the
`MIDDLEWARE_CLASSES` section in the Django `settings.py` file.

```
opencensus.trace.tracer.middleware.request.RequestMiddleware
```

Then the trace information will be automatically extracted from the incoming
request headers.

```python
from opencensus.trace.tracer import django_tracer

tracer = django_tracer.DjangoTracer()
tracer.start_trace()

with tracer.span(name='span1'):
    do_something_to_trace()

tracer.end_trace()
```

### Webapp2

```python
from opencensus.trace.tracer import webapp2_tracer

tracer = webapp2_tracer.WebApp2Tracer()
tracer.start_trace()

with tracer.span(name='span1'):
    do_something_to_trace()

tracer.end_trace()
```

## Status

Currently under active development.

## Development

### Tests

```
cd trace
tox -e py34
source .tox/py34/bin/activate

# Run the unit test
pip install nox-automation

# See what's available in the nox suite
nox -l

# Run a single nox command
nox -s "unit_tests(python_version='2.7')"

# Run all the nox commands
nox

# Integration test
# We don't have script for integration test yet, but can test as below.
python setup.py bdist_wheel
cd dist
pip install opencensus-0.0.1-py2.py3-none-any.whl

# Then just run the tracers normally as you want to test.
```

## Contributing

Contributions to this library are always welcome and highly encouraged.

See [CONTRIBUTING](CONTRIBUTING.md) for more information on how to get started.

## License

Apache 2.0 - See [LICENSE](LICENSE) for more information.

## Disclaimer

This is not an official Google product.
