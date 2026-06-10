import logging
from urllib.parse import urlsplit

from flask import abort, flash, redirect, render_template, request, url_for

from sqlalchemy import or_

from todo_project import app, bcrypt, db, log_event

# Import the forms
from todo_project.forms import (
    DeleteTaskForm,
    LoginForm,
    RegistrationForm,
    SearchTaskForm,
    TaskForm,
    UpdateTaskForm,
    UpdateUserInfoForm,
    UpdateUserPassword,
)

# Import the Models
from todo_project.models import User, Task

# Import 
from flask_login import current_user, login_required, login_user, logout_user


def get_owned_task_or_404(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        log_event(
            "ACESSO_NEGADO_RECURSO",
            level=logging.WARNING,
            task_id=task_id,
            resource_owner=task.user_id,
        )
        abort(403)
    return task


@app.errorhandler(404)
def error_404(error):
    return (render_template('errors/404.html'), 404)

@app.errorhandler(403)
def error_403(error):
    return (render_template('errors/403.html'), 403)

@app.errorhandler(500)
def error_500(error):
    log_event("ERRO_INTERNO", level=logging.ERROR, error_type=type(error).__name__)
    return (render_template('errors/500.html'), 500)


@app.route("/")
@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('all_tasks'))

    form = LoginForm()
    next_page = request.args.get("next")
    # After you submit the form
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Check if the user exists and the password is valid
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            log_event("LOGIN_SUCESSO", user=user.username)
            flash('Login Successfull', 'success')
            if next_page and urlsplit(next_page).netloc:
                next_page = None
            return redirect(next_page or url_for('all_tasks'))
        else:
            log_event("LOGIN_FALHA", level=logging.WARNING, user=form.username.data)
            flash('Login Unsuccessful. Please check Username Or Password', 'danger')
    
    return render_template('login.html', title='Login', form=form)
    

@app.route("/logout")
@login_required
def logout():
    log_event("LOGOUT")
    logout_user()
    return redirect(url_for('login'))


@app.route("/register", methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('all_tasks'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account Created For {form.username.data}', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route("/all_tasks")
@login_required
def all_tasks():
    search_form = SearchTaskForm()
    delete_form = DeleteTaskForm()
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.date_posted.desc()).all()
    log_event("TAREFA_CONSULTADA", task_count=len(tasks))
    return render_template(
        'all_tasks.html',
        title='All Tasks',
        tasks=tasks,
        search_form=search_form,
        delete_form=delete_form,
        search_term="",
    )


@app.route("/add_task", methods=['POST', 'GET'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(content=form.task_name.data, author=current_user)
        db.session.add(task)
        db.session.commit()
        log_event("TAREFA_CRIADA", task_id=task.id)
        flash('Task Created', 'success')
        return redirect(url_for('add_task'))
    return render_template('add_task.html', form=form, title='Add Task')


@app.route("/all_tasks/<int:task_id>/update_task", methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = get_owned_task_or_404(task_id)
    form = UpdateTaskForm()
    if form.validate_on_submit():
        if form.task_name.data != task.content:
            task.content = form.task_name.data
            db.session.commit()
            log_event("TAREFA_EDITADA", task_id=task.id)
            flash('Task Updated', 'success')
            return redirect(url_for('all_tasks'))
        else:
            flash('No Changes Made', 'warning')
            return redirect(url_for('all_tasks'))
    elif request.method == 'GET':
        form.task_name.data = task.content
    return render_template('add_task.html', title='Update Task', form=form)


@app.route("/all_tasks/<int:task_id>/delete_task", methods=['POST'])
@login_required
def delete_task(task_id):
    form = DeleteTaskForm()
    if not form.validate_on_submit():
        abort(400)

    task = get_owned_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    log_event("TAREFA_EXCLUIDA", task_id=task_id)
    flash('Task Deleted', 'info')
    return redirect(url_for('all_tasks'))


@app.route("/search_tasks", methods=['POST'])
@login_required
def search_tasks():
    form = SearchTaskForm()
    delete_form = DeleteTaskForm()
    if not form.validate_on_submit():
        flash('Provide a valid keyword to search tasks.', 'warning')
        return redirect(url_for('all_tasks'))

    keyword = form.keyword.data.strip()
    tasks = (
        Task.query.filter(Task.user_id == current_user.id)
        .filter(or_(Task.content.ilike(f"%{keyword}%")))
        .order_by(Task.date_posted.desc())
        .all()
    )
    log_event("PESQUISA_REALIZADA", keyword=keyword, result_count=len(tasks))
    return render_template(
        'all_tasks.html',
        title='All Tasks',
        tasks=tasks,
        search_form=form,
        delete_form=delete_form,
        search_term=keyword,
    )


@app.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateUserInfoForm()
    if form.validate_on_submit():
        if form.username.data != current_user.username:  
            current_user.username = form.username.data
            db.session.commit()
            flash('Username Updated Successfully', 'success')
            return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username 

    return render_template('account.html', title='Account Settings', form=form)


@app.route("/account/change_password", methods=['POST', 'GET'])
@login_required
def change_password():
    form = UpdateUserPassword()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.old_password.data):
            current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            db.session.commit()
            flash('Password Changed Successfully', 'success')
            return redirect(url_for('account'))
        else:
            flash('Please Enter Correct Password', 'danger') 

    return render_template('change_password.html', title='Change Password', form=form)

