from flask import render_template, flash, redirect, request, url_for
from app import app

from app.forms import LoginForm


@app.route('/')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(form.username.data, 
            form.remember_me.data))
        return redirect(url_for('index'))
    
    return render_template('login.html', title='Sing In', form=form)