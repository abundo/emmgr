from flask import render_template, request
from emmgr.app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    query = {}
    query['username'] = request.args.get('username', "")
    query['password'] = request.args.get('password', "")
    if query["username"] and query["password"]:
        pass
    return render_template('login.html', query=query)

@app.route('/logout')
def logout():
    pass

