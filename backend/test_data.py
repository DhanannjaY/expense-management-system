# test_data.py - Create more sample data
from django.contrib.auth.models import User
from expenses.models import Category, Expense, Budget
from datetime import datetime, timedelta
from decimal import Decimal
import random

def create_test_data():
    user = User.objects.first()
    if not user:
        print("No user found! Create superuser first.")
        return
    
    categories = Category.objects.all()
    if not categories:
        print("No categories found!")
        return
    
    # Create 30 days of random expenses
    for i in range(30):
        date = datetime.now().date() - timedelta(days=i)
        num_expenses = random.randint(1, 3)
        
        for _ in range(num_expenses):
            category = random.choice(categories)
            amount = random.randint(100, 2000)
            
            Expense.objects.create(
                user=user,
                title=f"Expense on {date}",
                amount=Decimal(amount),
                category=category,
                date=date,
                payment_method=random.choice(['cash', 'card', ]),
                description=f"Sample expense for testing"
            )
    
    print(f"Created sample expenses for last 30 days!")
    
    # Create budgets for all categories
    for category in categories:
        if not Budget.objects.filter(user=user, category=category).exists():
            Budget.objects.create(
                user=user,
                category=category,
                amount=Decimal(random.randint(3000, 15000)),
                period='monthly',
                alert_threshold=80
            )
    
    print(f"Created budgets for all categories!")

if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_project.settings')
    django.setup()
    create_test_data()