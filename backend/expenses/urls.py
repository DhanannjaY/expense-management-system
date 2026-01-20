# expenses/urls.py 
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'budgets', views.BudgetViewSet, basename='budget')

urlpatterns = [
    # Authentication endpoints (function-based views)
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/verify/', views.verify_token, name='verify_token'),
    
    # Analytics endpoints
    path('analytics/predictions/', views.expense_predictions, name='predictions'),
    
    # Include router URLs (ViewSet routes)
    # This provides:
    # - GET /expenses/dashboard/ (custom action)
    # - GET /budgets/analysis/ (custom action)
    # - Standard CRUD endpoints for all viewsets
    path('', include(router.urls)),
]