
# expenses/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import datetime, timedelta


class Category(models.Model):
    """Category model for expense classification"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='folder')
    color = models.CharField(max_length=7, default='#3B82F6')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """Main expense model"""
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('other', 'Other')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    description = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='cash')
    tags = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - Rs.{self.amount}"

class Budget(models.Model):
    """Budget model for expense limits"""
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    alert_threshold = models.IntegerField(default=80)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'category', 'period']
    
    def __str__(self):
        return f"{self.category.name} - Rs.{self.amount} ({self.period})"
    
class UserPreference(models.Model):
    """User preferences and settings"""
    CURRENCY_CHOICES = [
        ('NPR', 'Nepalese Rupee (Rs.)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NPR')
    enable_notifications = models.BooleanField(default=True)
    enable_budget_alerts = models.BooleanField(default=True)
    theme = models.CharField(max_length=20, default='light')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
