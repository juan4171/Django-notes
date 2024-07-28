import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Task
from django.contrib import messages

from .forms import TaskForm
from datetime import datetime

# Create your views here.


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {"form": UserCreationForm})
    else:

        if request.POST["password1"] == request.POST["password2"]:
            try:
                user = User.objects.create_user(
                    request.POST["username"], password=request.POST["password1"])
                user.save()
                login(request, user)
                return redirect('tasks')
            except IntegrityError:
                return render(request, 'signup.html', {"form": UserCreationForm, "error": "Username already exists."})

        return render(request, 'signup.html', {"form": UserCreationForm, "error": "Passwords did not match."})


@login_required
def signout(request):
    logout(request)
    return redirect('signin')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {"form": AuthenticationForm})
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html', {"form": AuthenticationForm, "error": "Username or password is incorrect."})

        login(request, user)
        return redirect('tasks')


def fetch_tasks(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        tasks = response.json()
        convert_dates(tasks)
        return tasks, None
    except requests.RequestException as e:
        return [], str(e)  # Retorna una lista vacía y el error


def convert_dates(tasks):
    def convert_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            return None

    def process_task(task):
        if 'created' in task:
            task['created'] = convert_date(task['created'])
        if 'datecompleted' in task and task['datecompleted']:
            task['datecompleted'] = convert_date(task['datecompleted'])
        return task

    if isinstance(tasks, list):
        for task in tasks:
            process_task(task)
    elif isinstance(tasks, dict):
        process_task(tasks)


@login_required
def tasks(request):
    tasks, error = fetch_tasks('http://localhost:8000/api/todos/',
                               {'datecompleted_null': 'true', 'ordering': '-created'})
    if error:
        messages.error(request, f"Error fetching tasks: {error}")

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task_data = {
                'title': form.cleaned_data['title'],
                'description': form.cleaned_data['description'],
                # 'created': timezone.now().isoformat(), no hace falta enviar la fecha de creación
                # porque la api la asigna automáticamente
                'datecompleted': form.cleaned_data.get('completed', None),
            }
            try:
                response = requests.post(
                    'http://localhost:8000/api/todos/', json=task_data)
                response.raise_for_status()
                messages.success(request, 'Task successfully created.')
            except requests.RequestException as e:
                messages.error(request, f"Error creating task: {e}")
            return redirect('tasks')
    else:
        form = TaskForm()

    return render(request, 'tasks.html', {"tasks": tasks, "form": form})


@login_required
def task_detail(request, task_id):
    task, error = fetch_tasks(f'http://localhost:8000/api/todos/{task_id}/')

    # Debugging: Check the type and content of task
    if not isinstance(task, dict):
        messages.error(request, f"Unexpected response format: {task}")
        return redirect('tasks')

    if error:
        messages.error(request, f"Error fetching task: {error}")
        return redirect('tasks')

    if request.method == 'POST':
        form = TaskForm(request.POST, initial=task)
        if form.is_valid():
            task_data = {
                'title': form.cleaned_data['title'],
                'description': form.cleaned_data['description'],
                # 'created': timezone.now().isoformat(), no hace falta enviar la fecha de creación
                # porque la api la asigna automáticamente
                'datecompleted': form.cleaned_data.get('completed', None),
            }
            try:
                response = requests.put(
                    f'http://localhost:8000/api/todos/{task_id}/', json=task_data)
                response.raise_for_status()
                messages.success(request, 'Task successfully updated.')
            except requests.RequestException as e:
                messages.error(request, f"Error updating task: {e}")
            return redirect('tasks')
    else:
        form = TaskForm(initial=task)

    return render(request, 'task_detail.html', {'task': task, 'form': form})


@login_required
def complete_task(request, task_id):
    if request.method == 'POST':
        task_data = {
            'datecompleted': timezone.now().isoformat()
        }
        try:
            response = requests.patch(
                f'http://localhost:8000/api/todos/{task_id}/', json=task_data)
            response.raise_for_status()
            messages.success(request, 'Task successfully completed.')
        except requests.RequestException as e:
            messages.error(request, f"Error completing task: {e}")
        return redirect('tasks_completed')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('tasks')


@login_required
def delete_task(request, task_id):
    if request.method == 'POST':
        try:
            response = requests.delete(
                f'http://localhost:8000/api/todos/{task_id}/')
            response.raise_for_status()
            messages.success(request, 'Task successfully deleted.')
        except requests.RequestException as e:
            messages.warning(request, f"Error deleting task: {e}")
        return redirect('tasks')


@login_required
def tasks_completed(request):
    tasks, error = fetch_tasks('http://localhost:8000/api/todos/',
                               {'datecompleted_null': 'false', 'ordering': '-created'})
    if error:
        messages.error(request, f"Error fetching tasks: {error}")

    return render(request, 'tasks.html', {"tasks": tasks})
