"""
Expense Management System — Test Suite
Covers models, API endpoints, validation, ML predictions, and security.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from decimal import Decimal
from datetime import date, timedelta

from expenses.models import Category, Tag, Expense, Budget, SavingsGoal, UserPreference
from expenses.ml_predictions import ExpensePrediction


# ═══════════════════════════ HELPERS ═══════════════════════════

def make_user(username='testuser', password='testpass123'):
    user = User.objects.create_user(username=username, email=f'{username}@test.com', password=password)
    UserPreference.objects.create(user=user)
    return user

def make_category(name='Food', color='#10b981'):
    cat, _ = Category.objects.get_or_create(name=name, defaults={'color': color})
    return cat

def auth_client(user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


# ═══════════════════════════ MODEL TESTS ═══════════════════════════

class CategoryModelTest(TestCase):
    def test_create_category(self):
        cat = Category.objects.create(name='Travel', icon='plane', color='#0ea5e9')
        self.assertEqual(str(cat), 'Travel')
        self.assertEqual(cat.color, '#0ea5e9')

    def test_category_unique_name(self):
        Category.objects.create(name='Unique')
        with self.assertRaises(Exception):
            Category.objects.create(name='Unique')

    def test_category_default_icon(self):
        cat = Category.objects.create(name='Test Cat')
        self.assertEqual(cat.icon, 'ellipsis-h')


class CategoryAPITest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client = auth_client(self.user)
        self.category = make_category()

    def test_non_staff_cannot_modify_shared_category(self):
        response = self.client.patch(
            f'/api/categories/{self.category.id}/',
            {'icon': 'updated-icon'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(f'/api/categories/{self.category.id}/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    def test_non_staff_cannot_create_shared_category(self):
        response = self.client.post(
            '/api/categories/',
            {'name': 'New Category', 'icon': 'folder'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_staff_category_icon_must_be_a_safe_class_name(self):
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])

        response = self.client.patch(
            f'/api/categories/{self.category.id}/',
            {'icon': 'folder" onmouseover="alert(1)'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)


class ExpenseModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_category()

    def test_create_expense(self):
        exp = Expense.objects.create(
            user=self.user, title='Test', amount=Decimal('100.00'),
            category=self.cat, date=date.today(), payment_method='cash'
        )
        self.assertEqual(str(exp), 'Test — Rs.100.00')
        self.assertEqual(exp.amount, Decimal('100.00'))

    def test_expense_ordering(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        e1 = Expense.objects.create(user=self.user, title='Old', amount=50, category=self.cat, date=yesterday)
        e2 = Expense.objects.create(user=self.user, title='New', amount=80, category=self.cat, date=today)
        expenses = list(Expense.objects.filter(user=self.user))
        self.assertEqual(expenses[0], e2)  # newest first

    def test_expense_indexes_exist(self):
        indexes = [idx.fields for idx in Expense._meta.indexes]
        self.assertIn(['user', 'date'], indexes)


class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_category()

    def test_create_budget(self):
        b = Budget.objects.create(
            user=self.user, category=self.cat, amount=Decimal('5000'),
            period='monthly', alert_threshold=80
        )
        self.assertIn('monthly', str(b))
        self.assertTrue(b.is_active)

    def test_budget_unique_together(self):
        Budget.objects.create(user=self.user, category=self.cat, amount=1000, period='monthly')
        with self.assertRaises(Exception):
            Budget.objects.create(user=self.user, category=self.cat, amount=2000, period='monthly')


class SavingsGoalModelTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_progress_percentage(self):
        goal = SavingsGoal.objects.create(
            user=self.user, title='Laptop', target_amount=50000, current_amount=25000
        )
        self.assertEqual(goal.progress_percentage, 50.0)

    def test_progress_capped_at_100(self):
        goal = SavingsGoal.objects.create(
            user=self.user, title='Done', target_amount=1000, current_amount=1500
        )
        self.assertEqual(goal.progress_percentage, 100.0)

    def test_zero_target_returns_zero(self):
        goal = SavingsGoal(user=self.user, title='X', target_amount=0, current_amount=0)
        self.assertEqual(goal.progress_percentage, 0)


# ═══════════════════════════ AUTH API TESTS ═══════════════════════════

class AuthAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'newuser', 'email': 'new@test.com',
            'password': 'password123', 'confirm_password': 'password123',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data['success'])
        self.assertIn('token', res.data)

    def test_register_duplicate_username(self):
        make_user('dup')
        res = self.client.post('/api/auth/register/', {
            'username': 'dup', 'email': 'dup2@test.com',
            'password': 'password123', 'confirm_password': 'password123',
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('username', res.data['errors'])

    def test_register_password_mismatch(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'mismatch', 'email': 'mm@test.com',
            'password': 'password123', 'confirm_password': 'differentpass',
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_register_short_password(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'shortpw', 'email': 'sp@test.com',
            'password': 'abc', 'confirm_password': 'abc',
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_login_success(self):
        make_user('logintest', 'mypassword123')
        res = self.client.post('/api/auth/login/', {
            'username': 'logintest', 'password': 'mypassword123'
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('token', res.data)

    def test_login_wrong_password(self):
        make_user('wrongpw', 'correctpass')
        res = self.client.post('/api/auth/login/', {
            'username': 'wrongpw', 'password': 'wrongpass'
        }, format='json')
        self.assertEqual(res.status_code, 401)

    def test_verify_token(self):
        user = make_user('verifytest')
        client = auth_client(user)
        res = client.get('/api/auth/verify/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['authenticated'])

    def test_change_password(self):
        user = make_user('passwordchange')
        client = auth_client(user)
        res = client.post('/api/auth/change-password/', {
            'current_password': 'testpass123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456',
        }, format='json')
        self.assertEqual(res.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass456'))

    def test_access_without_token(self):
        res = self.client.get('/api/expenses/')
        self.assertIn(res.status_code, [401, 403])


# ═══════════════════════════ EXPENSE API TESTS ═══════════════════════════

class ExpenseAPITest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.other = make_user('otheruser')
        self.cat = make_category()
        self.client = auth_client(self.user)

    def test_create_expense(self):
        res = self.client.post('/api/expenses/', {
            'title': 'Coffee', 'amount': '120.00', 'category': self.cat.id,
            'date': str(date.today()), 'payment_method': 'cash',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['title'], 'Coffee')

    def test_create_expense_negative_amount(self):
        res = self.client.post('/api/expenses/', {
            'title': 'Bad', 'amount': '-50', 'category': self.cat.id,
            'date': str(date.today()),
        }, format='json')
        self.assertNotEqual(res.status_code, 201)

    def test_create_expense_future_date(self):
        future = str(date.today() + timedelta(days=5))
        res = self.client.post('/api/expenses/', {
            'title': 'Future', 'amount': '100', 'category': self.cat.id, 'date': future,
        }, format='json')
        self.assertNotEqual(res.status_code, 201)

    def test_cannot_assign_another_users_tag(self):
        private_tag = Tag.objects.create(user=self.other, name='Private')
        response = self.client.post('/api/expenses/', {
            'title': 'Tagged expense',
            'amount': '100',
            'category': self.cat.id,
            'date': str(date.today()),
            'tags': [private_tag.id],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Expense.objects.filter(user=self.user).exists())

    def test_list_only_own_expenses(self):
        Expense.objects.create(user=self.user, title='Mine', amount=100, category=self.cat, date=date.today())
        Expense.objects.create(user=self.other, title='Theirs', amount=200, category=self.cat, date=date.today())
        res = self.client.get('/api/expenses/')
        results = res.data.get('results', res.data)
        titles = [e['title'] for e in results]
        self.assertIn('Mine', titles)
        self.assertNotIn('Theirs', titles)

    def test_delete_expense(self):
        exp = Expense.objects.create(user=self.user, title='Del', amount=50, category=self.cat, date=date.today())
        res = self.client.delete(f'/api/expenses/{exp.id}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Expense.objects.filter(id=exp.id).exists())

    def test_cannot_delete_others_expense(self):
        exp = Expense.objects.create(user=self.other, title='NotMine', amount=50, category=self.cat, date=date.today())
        res = self.client.delete(f'/api/expenses/{exp.id}/')
        self.assertIn(res.status_code, [403, 404])

    def test_dashboard_endpoint(self):
        res = self.client.get('/api/expenses/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('summary', res.data)
        self.assertIn('daily_trend', res.data)

    def test_bulk_delete(self):
        ids = [
            Expense.objects.create(user=self.user, title=f'E{i}', amount=10, category=self.cat, date=date.today()).id
            for i in range(3)
        ]
        res = self.client.delete('/api/expenses/bulk_delete/', {'ids': ids}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Expense.objects.filter(id__in=ids).count(), 0)

    def test_search_filter(self):
        Expense.objects.create(user=self.user, title='Grocery Shopping', amount=500, category=self.cat, date=date.today())
        Expense.objects.create(user=self.user, title='Taxi Ride', amount=100, category=self.cat, date=date.today())
        res = self.client.get('/api/expenses/?search=Grocery')
        results = res.data.get('results', res.data)
        self.assertTrue(all('Grocery' in e['title'] for e in results))


# ═══════════════════════════ BUDGET API TESTS ═══════════════════════════

class BudgetAPITest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_category()
        self.client = auth_client(self.user)

    def test_create_budget(self):
        res = self.client.post('/api/budgets/', {
            'category': self.cat.id, 'amount': '10000', 'period': 'monthly', 'alert_threshold': 80,
        }, format='json')
        self.assertEqual(res.status_code, 201)

    def test_duplicate_budget_rejected(self):
        self.client.post('/api/budgets/', {
            'category': self.cat.id, 'amount': '5000', 'period': 'monthly',
        }, format='json')
        res = self.client.post('/api/budgets/', {
            'category': self.cat.id, 'amount': '8000', 'period': 'monthly',
        }, format='json')
        self.assertNotEqual(res.status_code, 201)

    def test_budget_analysis_endpoint(self):
        Budget.objects.create(user=self.user, category=self.cat, amount=5000, period='monthly')
        res = self.client.get('/api/budgets/analysis/')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

    def test_budget_status_safe(self):
        Budget.objects.create(user=self.user, category=self.cat, amount=10000, period='monthly', alert_threshold=80)
        Expense.objects.create(user=self.user, title='Small', amount=500, category=self.cat, date=date.today())
        res = self.client.get('/api/budgets/analysis/')
        item = next((b for b in res.data if b['category'] == self.cat.name), None)
        self.assertIsNotNone(item)
        self.assertEqual(item['status'], 'safe')

    def test_budget_threshold_validation(self):
        res = self.client.post('/api/budgets/', {
            'category': self.cat.id, 'amount': '5000', 'period': 'monthly', 'alert_threshold': 150,
        }, format='json')
        self.assertNotEqual(res.status_code, 201)


# ═══════════════════════════ SAVINGS GOAL API TESTS ═══════════════════════════

class SavingsGoalAPITest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client = auth_client(self.user)

    def test_create_goal(self):
        res = self.client.post('/api/savings-goals/', {
            'title': 'Emergency Fund', 'target_amount': '100000', 'current_amount': '0',
        }, format='json')
        self.assertEqual(res.status_code, 201)

    def test_add_funds(self):
        goal = SavingsGoal.objects.create(user=self.user, title='Laptop', target_amount=50000, current_amount=0)
        res = self.client.post(f'/api/savings-goals/{goal.id}/add_funds/', {'amount': 10000}, format='json')
        self.assertEqual(res.status_code, 200)
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal('10000'))

    def test_add_funds_caps_at_target(self):
        goal = SavingsGoal.objects.create(user=self.user, title='Capped', target_amount=1000, current_amount=900)
        self.client.post(f'/api/savings-goals/{goal.id}/add_funds/', {'amount': 500}, format='json')
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal('1000'))
        self.assertEqual(goal.status, 'completed')

    def test_add_funds_rejects_non_finite_amount(self):
        goal = SavingsGoal.objects.create(user=self.user, title='Invalid', target_amount=1000, current_amount=0)
        response = self.client.post(
            f'/api/savings-goals/{goal.id}/add_funds/',
            {'amount': 'NaN'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal('0'))


# ═══════════════════════════ ML PREDICTION TESTS ═══════════════════════════

class MLPredictionTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_category()

    def _make_expenses(self, n=30):
        today = date.today()
        for i in range(n):
            Expense.objects.create(
                user=self.user, title=f'Exp {i}', amount=Decimal('500'),
                category=self.cat, date=today - timedelta(days=i)
            )

    def test_prediction_with_sufficient_data(self):
        self._make_expenses(30)
        result = ExpensePrediction.predict_expenses(self.user, prediction_days=7)
        self.assertIn('recommended_prediction', result)
        self.assertGreaterEqual(result['recommended_prediction'], 0)

    def test_prediction_with_insufficient_data(self):
        Expense.objects.create(user=self.user, title='Single', amount=100, category=self.cat, date=date.today())
        result = ExpensePrediction.predict_expenses(self.user, prediction_days=7)
        self.assertEqual(result['recommended_prediction'], 0)

    def test_prediction_returns_all_keys(self):
        result = ExpensePrediction.predict_expenses(self.user, prediction_days=7)
        required_keys = ['recommended_prediction', 'confidence', 'trend', 'statistics', 'algorithms']
        for key in required_keys:
            self.assertIn(key, result)

    def test_prediction_confidence_levels(self):
        self._make_expenses(90)
        result = ExpensePrediction.predict_expenses(self.user, prediction_days=30)
        self.assertIn(result['confidence'], ['high', 'medium', 'low'])

    def test_linear_regression_flat_data(self):
        slope, intercept = ExpensePrediction.linear_regression([0,1,2,3,4], [100,100,100,100,100])
        self.assertAlmostEqual(slope, 0, places=5)
        self.assertAlmostEqual(intercept, 100, places=5)

    def test_r_squared_perfect_fit(self):
        x = [0,1,2,3,4]
        y = [10,20,30,40,50]
        slope, intercept = ExpensePrediction.linear_regression(x, y)
        r2 = ExpensePrediction.calculate_r_squared(x, y, slope, intercept)
        self.assertAlmostEqual(r2, 1.0, places=4)

    def test_category_predictions(self):
        self._make_expenses(20)
        result = ExpensePrediction.get_category_predictions(self.user, 7)
        self.assertIsInstance(result, dict)

    def test_monthly_forecast(self):
        self._make_expenses(30)
        result = ExpensePrediction.get_monthly_forecast(self.user)
        self.assertIn('monthly_total', result)
        self.assertIn('weekly_breakdown', result)
        self.assertEqual(len(result['weekly_breakdown']), 4)


# ═══════════════════════════ SECURITY TESTS ═══════════════════════════

class SecurityTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_category()

    def test_unauthenticated_expense_access(self):
        client = APIClient()
        res = client.get('/api/expenses/')
        self.assertIn(res.status_code, [401, 403])

    def test_unauthenticated_dashboard_access(self):
        client = APIClient()
        res = client.get('/api/expenses/dashboard/')
        self.assertIn(res.status_code, [401, 403])

    def test_cross_user_expense_access(self):
        user2 = make_user('user2')
        exp = Expense.objects.create(user=user2, title='Private', amount=100, category=self.cat, date=date.today())
        client = auth_client(self.user)
        res = client.get(f'/api/expenses/{exp.id}/')
        self.assertIn(res.status_code, [403, 404])

    def test_password_not_in_response(self):
        client = APIClient()
        res = client.post('/api/auth/login/', {
            'username': self.user.username, 'password': 'testpass123'
        }, format='json')
        self.assertNotIn('password', str(res.data))

    def test_sql_injection_in_search(self):
        client = auth_client(self.user)
        res = client.get("/api/expenses/?search='; DROP TABLE expenses; --")
        self.assertIn(res.status_code, [200, 400])  # Should not 500


# ═══════════════════════════ ANALYTICS API TESTS ═══════════════════════════

class AnalyticsAPITest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_category()
        self.client = auth_client(self.user)

    def test_analytics_overview(self):
        res = self.client.get('/api/analytics/overview/?period=month')
        self.assertEqual(res.status_code, 200)
        self.assertIn('summary', res.data)
        self.assertIn('daily_trend', res.data)
        self.assertIn('by_category', res.data)

    def test_predictions_endpoint(self):
        res = self.client.get('/api/analytics/predictions/?days=7')
        self.assertEqual(res.status_code, 200)
        self.assertIn('recommended_prediction', res.data)

    def test_monthly_forecast_endpoint(self):
        res = self.client.get('/api/analytics/monthly-forecast/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('monthly_total', res.data)


class UserPreferenceAPITest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client = auth_client(self.user)

    def test_update_preferences_uses_owned_detail_route(self):
        preference = self.user.preference
        response = self.client.put(
            f'/api/preferences/{preference.id}/',
            {'theme': 'dark'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        preference.refresh_from_db()
        self.assertEqual(preference.theme, 'dark')

    def test_user_route_does_not_ignore_requested_user_id(self):
        other_user = make_user('otherprofile')
        response = self.client.put(
            f'/api/users/{other_user.id}/',
            {'first_name': 'Unauthorized'},
            format='json',
        )
        self.assertEqual(response.status_code, 404)
        other_user.refresh_from_db()
        self.assertNotEqual(other_user.first_name, 'Unauthorized')

    def test_profile_update_rejects_duplicate_email(self):
        other_user = make_user('emailowner')
        response = self.client.put(
            f'/api/users/{self.user.id}/',
            {'email': other_user.email},
            format='json',
        )
        self.assertEqual(response.status_code, 400)