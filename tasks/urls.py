"""stone URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.urls import include
from . import views

urlpatterns = [
    path('task_set_complete/<pk>/', views.TaskSetCompleteView.as_view(), name='task_set_complete'),
    path('autocomplete/', views.TasksAutocompleteListView.as_view(), name='tasks_autocomplete_list'),
    path('create/<app_label_name>/<object_id>/', views.TasksCreateView.as_view(), name='tasks_create'),
    path('<pk>/update/', views.TasksUpdateView.as_view(), name='tasks_update'),
    path('<pk>/delete/', views.TasksDeleteView.as_view(), name='tasks_delete'),
    path('<pk>/delay-time/', views.TasksDelayView.as_view(), name='tasks_delay'),
    path('<pk>/', views.TasksDetailView.as_view(), name='tasks_detail'),
    path('', views.TasksListView.as_view(), name='tasks_list'),
]
