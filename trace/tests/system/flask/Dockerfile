FROM gcr.io/google-appengine/python
LABEL python_version=python
RUN virtualenv --no-download /env -p python

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ADD . /app/
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python main.py
