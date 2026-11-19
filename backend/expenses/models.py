"""
Expense Management System — Models
Enhanced with tags, recurring expenses, savings goals, and user preferences.
"""
from datetime import date, timedelta
import calendar
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


def advance_recurring_date(current_date: date, frequency: str) -> date:
    """Safely advance a date by daily, weekly, monthly, or yearly intervals."""
    if frequency == 'daily':
        return current_date + timedelta(days=1)
    if frequency == 'weekly':
        return current_date + timedelta(weeks=1)
    if frequency == 'monthly':
        year = current_date.year + (current_date.month // 12)
        month = (current_date.month % 12) + 1
        max_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(current_date.day, max_day))
    if frequency == 'yearly':
        year = current_date.year + 1
        max_day = calendar.monthrange(year, current_date.month)[1]
        return date(year, current_date.month, min(current_date.day, max_day))
    return current_date + timedelta(days=30)


class Category(models.Model):
    ICON_CHOICES = [
        ('shopping-cart', 'Shopping'),
        ('utensils', 'Food'),
        ('home', 'Housing'),
        ('car', 'Transportation'),
        ('heartbeat', 'Healthcare'),
        ('graduation-cap', 'Education'),
        ('film', 'Entertainment'),
        ('bolt', 'Utilities'),
        ('user', 'Personal Care'),
        ('briefcase', 'Work'),
        ('plane', 'Travel'),
        ('ellipsis-h', 'Other'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='ellipsis-h')
    color = models.CharField(max_length=7, default='#6366f1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """User-defined tags for flexible expense labeling."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Expense(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('other', 'Other'),
    ]

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='expenses')
    date = models.DateField()
    description = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='cash')
    tags = models.ManyToManyField(Tag, blank=True, related_name='expenses')
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, blank=True)
    next_recurring_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    receipt_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_recurring', 'next_recurring_date']),
        ]

    def save(self, *args, **kwargs):
        if self.is_recurring and self.recurring_frequency:
            if not self.next_recurring_date:
                self.next_recurring_date = advance_recurring_date(self.date, self.recurring_frequency)
        else:
            self.recurring_frequency = ''
            self.next_recurring_date = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — Rs.{self.amount}"


class Budget(models.Model):
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    alert_threshold = models.IntegerField(
        default=80,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'category', 'period']
        ordering = ['category__name']

    def __str__(self):
        return f"{self.category.name} — Rs.{self.amount} ({self.period})"


class SavingsGoal(models.Model):
    """Track savings targets alongside expenses."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    title = models.CharField(max_length=200)
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.current_amount >= self.target_amount and self.status == 'active':
            self.status = 'completed'
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self) -> float:
        if self.target_amount > 0:
            return round(min(100.0, float(self.current_amount / self.target_amount * 100)), 2)
        return 0.0

    @property
    def remaining_amount(self) -> Decimal:
        return max(Decimal('0.00'), self.target_amount - self.current_amount)

    @property
    def days_remaining(self):
        if not self.target_date:
            return None
        return (self.target_date - date.today()).days

    def __str__(self):
        return f"{self.title} — {self.user.username}"


class UserPreference(models.Model):
    CURRENCY_CHOICES = [
        ('NPR', 'Nepalese Rupee (Rs.)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('INR', 'Indian Rupee (₹)'),
        ('GBP', 'British Pound (£)'),
    ]

    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System'),
    ]

    CURRENCY_SYMBOLS = {
        'NPR': 'Rs.',
        'USD': '$',
        'EUR': '€',
        'INR': '₹',
        'GBP': '£',
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NPR')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    enable_notifications = models.BooleanField(default=True)
    enable_budget_alerts = models.BooleanField(default=True)
    week_starts_on = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text='0=Monday, 6=Sunday',
    )
    date_format = models.CharField(max_length=20, default='%Y-%m-%d')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences — {self.user.username}"

    @property
    def currency_symbol(self) -> str:
        return self.CURRENCY_SYMBOLS.get(self.currency, 'Rs.')