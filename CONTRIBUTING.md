# How to contribute

We definitely welcome patches and contributions to OpenCensus! Here are
some guidelines and information about how to do so.

## Before getting started

In order to protect both you and ourselves, you will need to sign the
[Contributor License Agreement](https://cla.developers.google.com/clas).

## Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.

## Instructions

Prerequisites:

* You must have every major version of Python that OpenCensus supports installed (see https://pypi.org/project/opencensus/ for which versions are supported).
* You need to fork the project in GitHub.

Clone the upstream repo:

```sh
$ git clone https://github.com/census-instrumentation/opencensus-python.git
```

Add your fork as an origin:

```sh
$ git remote add fork https://github.com/YOUR_GITHUB_USERNAME/opencensus-python.git
```

Run tests:

```sh
# Make sure you have all supported versions of Python installed
$ pip install nox  # Only first time.
$ nox
```

Checkout a new branch, make modifications and push the branch to your fork:

```sh
$ git checkout -b feature
# edit files
$ git commit
$ git push fork feature
```

Open a pull request against the main opencensus-python repo.

### Additional instructions for extension developers

If you want to contribute new [extensions](README.rst#extensions), you need some extra steps:

* Prepare the extension code, put it under the [contrib](./contrib/) folder.
* Update [noxfile.py](./noxfile.py) to include your new extension for testing purpose.
* Update [README](./README.rst#extensions) to include your extension.
