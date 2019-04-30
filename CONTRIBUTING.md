# How to contribute

We definitely welcome patches and contributions to OpenCensus! Here are
some guidelines and information about how to do so.

## Before getting started

In order to protect both you and ourselves, you will need to sign the
[Contributor License Agreement](https://cla.developers.google.com/clas).

## Run test locally

```
# Install nox with pip
pip install nox-automation

# See what's available in the nox suite
nox -l

# Run a single nox command
nox -s "unit(py='2.7')"

# Run all the nox commands
nox

# Integration test
# We don't have script for integration test yet, but can test as below.
python setup.py bdist_wheel
cd dist
pip install opencensus-0.0.1-py2.py3-none-any.whl

# Then just run the tracers normally as you want to test.
```

## Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.
