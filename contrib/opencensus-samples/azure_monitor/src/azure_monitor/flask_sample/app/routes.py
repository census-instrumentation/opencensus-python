import requests

from flask import render_template, request, redirect, url_for 
from app import app, db
from app.forms import ToDoForm

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(200)) 
    complete = db.Column(db.Boolean) 

@app.route('/')
def index():
    form = ToDoForm()
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
    return redirect(url_for('index'))

@app.route('/complete/<id>', methods =['POST']) 
def complete(id): 
    todo = Todo.query.filter_by(id = int(id)).first() 
    todo.complete = True
    db.session.commit() 
    return redirect(url_for('index')) 

@app.route('/search/<id>') 
def search(id):
    todo = Todo.query.filter_by(id = int(id)).first()
    result = requests.get('http://google.com', todo.text)
    if result and result.ok and result.url:
        todo.text = result.url
    db.session.commit()
    return redirect(url_for('index'))
