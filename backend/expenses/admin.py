from django.contrib import admin
from .models import Category, Tag, Expense, Budget, SavingsGoal, UserPreference


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'created_at']
    list_filter = ['user']
    list_select_related = ['user']
    search_fields = ['name', 'user__username']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'amount', 'category', 'date',
        'payment_method', 'is_recurring', 'next_recurring_date',
    ]
    list_filter = ['category', 'payment_method', 'is_recurring', 'recurring_frequency', 'date']
    list_select_related = ['user', 'category']
    search_fields = ['title', 'description', 'location', 'receipt_note', 'user__username']
    filter_horizontal = ['tags']
    date_hierarchy = 'date'
    raw_id_fields = ['user']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['category', 'user', 'amount', 'period', 'alert_threshold', 'is_active']
    list_filter = ['period', 'is_active']
    list_select_related = ['user', 'category']
    search_fields = ['category__name', 'user__username']


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'target_amount', 'current_amount',
        'progress_display', 'status', 'target_date',
    ]
    list_filter = ['status']
    list_select_related = ['user']
    search_fields = ['title', 'user__username']

    @admin.display(description='Progress')
    def progress_display(self, obj):
        return f"{obj.progress_percentage:.0f}%"


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'theme', 'enable_notifications', 'enable_budget_alerts']
    list_filter = ['currency', 'theme']
    list_select_related = ['user']
    search_fields = ['user__username']