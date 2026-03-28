from django.urls import path
from . import views
 
app_name = 'champs'
 
urlpatterns = [
    path('', views.champion_list, name='champion_list'),
    path('create/', views.ChampionCreateView.as_view(), name='champion_create'),
    path('update/<int:pk>/', views.ChampionUpdateView.as_view(), name='champion_update'),
    path('delete/<int:pk>/', views.ChampionDeleteView.as_view(), name='champion_delete'),
    path('role/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('role/<int:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('logout/', views.logout_view, name='logout'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
    path('<slug:slug>/', views.champion_detail, name='champion_detail'),
]
