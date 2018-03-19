# Release OpenCensus Python

## Steps

### Create a Github release

### Update the version number in `setup.py`

### Update the version number in `stackdriver_exporter.py`

### Build the Python wheel

```
python setup.py bdist_wheel
```

### Upload the package to PyPI using twine

```
twine upload dist/*
```
