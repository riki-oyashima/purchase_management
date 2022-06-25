from django.urls import path
from . import views

urlpatterns = [
    path('', views.TopView.as_view(), name='index'),
    path('add', views.AddView.as_view(), name='add'),
    path('edit/<int:id>', views.EditView.as_view(), name='edit'),
    path('list', views.ListView.as_view(), name='list'),
]

