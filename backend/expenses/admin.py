# Register your models here.
# expenses/admin.py
from django.contrib import admin
from .models import Category, Expense, Budget

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'amount', 'category', 'date', 'payment_method']
    list_filter = ['category', 'payment_method', 'date']
    search_fields = ['title', 'description']
    date_hierarchy = 'date'

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['category', 'user', 'amount', 'period', 'is_active']
    list_filter = ['period', 'is_active']
    search_fields = ['category__name', 'user__username']