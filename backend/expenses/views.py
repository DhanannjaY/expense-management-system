from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from expenses.models import Expense, Budget, UserPreference, Category
from expenses.serializers import (ExpenseSerializer, BudgetSerializer, CategorySerializer, UserSerializer, UserPreferenceSerializer)
from expenses.ml_predictions import ExpensePrediction

import re


# ================= FUNCTION-BASED AUTH VIEWS =================
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration endpoint"""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    confirm_password = request.data.get('confirm_password', '')
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()

    errors = {}

    # Username validation
    if not username:
        errors['username'] = 'Username is required'
    elif len(username) < 3:
        errors['username'] = 'Username must be at least 3 characters'
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors['username'] = 'Username can only contain letters, numbers, and underscores'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already exists'

    # Email validation
    if not email:
        errors['email'] = 'Email is required'
    elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        errors['email'] = 'Invalid email format'
    elif User.objects.filter(email=email).exists():
        errors['email'] = 'Email already registered'

    # Password validation
    if not password:
        errors['password'] = 'Password is required'
    elif len(password) < 6:
        errors['password'] = 'Password must be at least 6 characters'
    elif password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match'

    if errors:
        return Response(
            {'success': False, 'errors': errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create user preferences
        UserPreference.objects.create(user=user)

        return Response(
            {
                'success': True,
                'message': 'Registration successful. Please login.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            },
            status=status.HTTP_201_CREATED
        )

    except IntegrityError:
        return Response(
            {'success': False, 'error': 'Registration failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'success': False, 'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {'success': False, 'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            'success': True,
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': user.get_full_name() or user.username
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
    except Token.DoesNotExist:
        pass

    logout(request)

    return Response(
        {'success': True, 'message': 'Logout successful'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """Verify authentication token"""
    return Response(
        {
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'name': request.user.get_full_name() or request.user.username
            }
        }
    )


# ================= EXPENSE VIEWSET =================
class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(
            user=self.request.user
        ).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard statistics and data"""
        # Get date range (last 30 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Get expenses in date range
        expenses = Expense.objects.filter(
            user=request.user,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate summary statistics
        summary = expenses.aggregate(
            total_expenses=Sum('amount'),
            transaction_count=Count('id'),
            average_transaction=Avg('amount')
        )
        
        # Handle None values
        summary['total_expenses'] = summary['total_expenses'] or 0
        summary['transaction_count'] = summary['transaction_count'] or 0
        summary['average_transaction'] = summary['average_transaction'] or 0
        
        # Get daily trend (last 7 days)
        seven_days_ago = end_date - timedelta(days=7)
        daily_expenses = {}
        
        for expense in expenses.filter(date__gte=seven_days_ago):
            date_str = expense.date.isoformat()
            daily_expenses[date_str] = daily_expenses.get(date_str, 0) + float(expense.amount)
        
        # Create daily trend list
        daily_trend = []
        for i in range(7):
            date = seven_days_ago + timedelta(days=i)
            date_str = date.isoformat()
            daily_trend.append({
                'date': date_str,
                'amount': daily_expenses.get(date_str, 0)
            })
        
        # Get category breakdown
        category_breakdown = expenses.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:5]
        
        return Response({
            'summary': summary,
            'daily_trend': daily_trend,
            'by_category': list(category_breakdown)
        })


# ================= BUDGET VIEWSET =================
class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(
            user=self.request.user
        ).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def analysis(self, request):
        """Budget analysis with spending comparison"""
        budgets = self.get_queryset().filter(is_active=True)
        
        analysis = []
        for budget in budgets:
            # Get current period expenses
            end_date = timezone.now().date()
            
            if budget.period == 'weekly':
                start_date = end_date - timedelta(days=7)
            elif budget.period == 'monthly':
                start_date = end_date - timedelta(days=30)
            else:  # yearly
                start_date = end_date - timedelta(days=365)
            
            spent = Expense.objects.filter(
                user=request.user,
                category=budget.category,
                date__gte=start_date,
                date__lte=end_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            percentage = (float(spent) / float(budget.amount)) * 100 if budget.amount > 0 else 0
            
            # Determine status
            if percentage >= 100:
                status_label = 'over'
            elif percentage >= budget.alert_threshold:
                status_label = 'warning'
            else:
                status_label = 'safe'
            
            analysis.append({
                'id': budget.id,
                'category': budget.category.name,
                'budget_amount': float(budget.amount),
                'spent_amount': float(spent),
                'percentage_used': percentage,
                'status': status_label,
                'period': budget.period
            })
        
        return Response(analysis)


# ================= CATEGORY VIEWSET =================
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Categories are shared across all users
        return Category.objects.all()

    def perform_create(self, serializer):
        # Don't save user for categories
        serializer.save()

# ================= USER PREFERENCE VIEWSET =================
class UserPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserPreferenceSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        return Response(UserPreferenceSerializer(pref).data)

    def update(self, request, *args, **kwargs):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ================= USER VIEWSET =================
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user
    
# ================= ANALYTICS ENDPOINTS =================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expense_predictions(request):
    """ML-powered prediction using Linear Regression + Weighted Algorithm"""
    prediction_days = int(request.query_params.get('days', 7))
    category_id = request.query_params.get('category', None)
    category = None
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            pass
    prediction = ExpensePrediction.predict_expenses(
        request.user, prediction_days, category
    )
    return Response(prediction)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_forecast(request):
    """Full monthly forecast with weekly breakdown and per-category predictions"""
    forecast = ExpensePrediction.get_monthly_forecast(request.user)
    return Response(forecast)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_predictions(request):
    """Per-category predictions"""
    prediction_days = int(request.query_params.get('days', 7))
    predictions = ExpensePrediction.get_category_predictions(
        request.user, prediction_days
    )
    return Response(predictions)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password — called by settings.html"""
    current  = request.data.get('current_password', '')
    new_pw   = request.data.get('new_password', '')
    confirm  = request.data.get('confirm_password', '')

    if not current or not new_pw:
        return Response({'success': False, 'error': 'All fields are required'},
                        status=status.HTTP_400_BAD_REQUEST)
    if not request.user.check_password(current):
        return Response({'success': False, 'error': 'Current password is incorrect'},
                        status=status.HTTP_400_BAD_REQUEST)
    if len(new_pw) < 6:
        return Response({'success': False, 'error': 'New password must be at least 6 characters'},
                        status=status.HTTP_400_BAD_REQUEST)
    if new_pw != confirm:
        return Response({'success': False, 'error': 'New passwords do not match'},
                        status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(new_pw)
    request.user.save()
    # Re-issue token so user stays logged in
    request.user.auth_token.delete()
    token = Token.objects.create(user=request.user)
    return Response({'success': True, 'message': 'Password changed successfully',
                     'token': token.key})