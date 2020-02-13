# Copyright 2019, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import render_template, request, redirect, url_for 
from app import app, db, logger
from app.forms import ToDoForm
from app.models import Todo
from app.metrics import mmap, request_measure, tmap

# Hitting any of these endpoints will be tracked as incoming requests (requests)

@app.route('/')
def index():
    form = ToDoForm()
    # These queries to the data base will be tracked as outgoing requests (dependencies)
    incomplete = Todo.query.filter_by(complete = False).all() 
    complete = Todo.query.filter_by(complete = True).all() 
    return render_template('index.html', title='Home', form=form, complete=complete, incomplete=incomplete)

@app.route('/blacklist')
def blacklist():
    return render_template('blacklist.html')

@app.route('/add', methods =['POST']) 
def add(): 
    todo = Todo(text = request.form['add_input'], complete = False) 
    db.session.add(todo) 
    db.session.commit()
    # Any logging done with the logger will be tracked as logging telemetry (trace)
    logger.info("Added entry: " + todo.text)
    # Records a measure metric to be sent as telemetry (customMetric)
    mmap.measure_int_put(request_measure, 1)
    mmap.record(tmap)
    return redirect(url_for('index'))

@app.route('/complete/<id>', methods =['POST']) 
def complete(id): 
    todo = Todo.query.filter_by(id = int(id)).first() 
    todo.complete = True
    db.session.commit() 
    logger.info("Marked complete: " + todo.text)
    return redirect(url_for('index')) 
