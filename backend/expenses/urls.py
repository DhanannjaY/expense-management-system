# expenses/urls.py 
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'budgets', views.BudgetViewSet, basename='budget')
router.register(r'savings-goals', views.SavingsGoalViewSet, basename='savings-goal')
router.register(r'preferences', views.UserPreferenceViewSet, basename='preference')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints (function-based views)
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/verify/', views.verify_token, name='verify_token'),
    path('auth/change-password/', views.change_password, name='change_password'),
    
    # Analytics endpoints
    path('analytics/overview/', views.analytics_overview, name='analytics_overview'),
    path('analytics/predictions/', views.expense_predictions, name='predictions'),
    path('analytics/monthly-forecast/',    views.monthly_forecast,     name='monthly_forecast'),
    path('analytics/category-predictions/',views.category_predictions, name='category_predictions'),
    
    # Include router URLs (ViewSet routes)
    # This provides:
    # - GET /expenses/dashboard/ (custom action)
    # - GET /budgets/analysis/ (custom action)
    # - Standard CRUD endpoints for all viewsets
    path('', include(router.urls)),
]