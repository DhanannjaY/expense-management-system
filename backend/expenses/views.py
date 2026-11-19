"""
Expense Management System — Views
Full-featured REST API with filtering, analytics, and ML predictions.
"""
import csv
import logging
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Max, Min, Sum
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from rest_framework import filters, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from expenses.ml_predictions import ExpensePrediction
from expenses.models import Budget, Category, Expense, SavingsGoal, Tag, UserPreference
from expenses.serializers import (
    BudgetSerializer,
    CategorySerializer,
    ExpenseCreateSerializer,
    ExpenseSerializer,
    SavingsGoalSerializer,
    TagSerializer,
    UserPreferenceSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


def _serialize_auth_user(user):
    pref, _ = UserPreference.objects.get_or_create(user=user)
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'name': user.get_full_name() or user.username,
        'currency': pref.currency,
        'currency_symbol': pref.currency_symbol,
        'theme': pref.theme,
    }


def _advance_date(current_date, frequency):
    if frequency == 'daily':
        return current_date + timedelta(days=1)
    if frequency == 'weekly':
        return current_date + timedelta(weeks=1)
    if frequency == 'yearly':
        try:
            return current_date.replace(year=current_date.year + 1)
        except ValueError:
            return current_date.replace(year=current_date.year + 1, day=28)
    # Default: monthly
    month = current_date.month + 1
    year = current_date.year + (1 if month > 12 else 0)
    month = 1 if month > 12 else month
    for day in (current_date.day, 30, 29, 28):
        try:
            return current_date.replace(year=year, month=month, day=day)
        except ValueError:
            continue
    return current_date + timedelta(days=30)


def _materialize_recurring_expenses(user):
    """Create any overdue recurring expense instances up to today."""
    today = date.today()
    due_templates = list(
        Expense.objects.filter(
            user=user,
            is_recurring=True,
            next_recurring_date__isnull=False,
            next_recurring_date__lte=today,
        ).prefetch_related('tags')
    )
    for template in due_templates:
        tag_ids = list(template.tags.values_list('id', flat=True))
        due_date = template.next_recurring_date
        guard = 0
        while due_date and due_date <= today and guard < 60:
            guard += 1
            clone = Expense.objects.create(
                user=user,
                title=template.title,
                amount=template.amount,
                category=template.category,
                date=due_date,
                description=template.description,
                payment_method=template.payment_method,
                location=template.location,
                receipt_note=template.receipt_note,
                is_recurring=False,
            )
            if tag_ids:
                clone.tags.set(tag_ids)
            due_date = _advance_date(due_date, template.recurring_frequency)
        template.next_recurring_date = due_date
        template.save(update_fields=['next_recurring_date', 'updated_at'])


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200


# ═══════════════════════════ AUTH VIEWS ═══════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration with full validation."""
    data = request.data
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    errors = {}

    if not username:
        errors['username'] = 'Username is required.'
    elif len(username) < 3 or len(username) > 30:
        errors['username'] = 'Username must be 3–30 characters.'
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors['username'] = 'Only letters, numbers, and underscores.'
    elif User.objects.filter(username__iexact=username).exists():
        errors['username'] = 'Username already taken.'

    if not email:
        errors['email'] = 'Email is required.'
    elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email):
        errors['email'] = 'Invalid email format.'
    elif User.objects.filter(email__iexact=email).exists():
        errors['email'] = 'Email already registered.'

    if not password:
        errors['password'] = 'Password is required.'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    elif password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    if errors:
        return Response({'success': False, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            UserPreference.objects.create(user=user)
            token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'success': True,
            'message': 'Account created successfully.',
            'token': token.key,
            'user': _serialize_auth_user(user),
        }, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response(
            {'success': False, 'error': 'Registration failed. Try again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login and return auth token."""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'success': False, 'error': 'Username and password required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'success': False, 'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({'success': False, 'error': 'Account disabled.'}, status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'success': True,
        'token': token.key,
        'user': _serialize_auth_user(user),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'success': True, 'message': 'Logged out.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    return Response({
        'authenticated': True,
        'user': _serialize_auth_user(request.user),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    current = request.data.get('current_password', '')
    new_pw = request.data.get('new_password', '')
    confirm = request.data.get('confirm_password', '')

    if not all([current, new_pw, confirm]):
        return Response({'success': False, 'error': 'All fields required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.check_password(current):
        return Response({'success': False, 'error': 'Current password incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
    if len(new_pw) < 8:
        return Response({'success': False, 'error': 'Password must be at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)
    if new_pw != confirm:
        return Response({'success': False, 'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(new_pw)
    request.user.save()
    Token.objects.filter(user=request.user).delete()
    token = Token.objects.create(user=request.user)

    return Response({'success': True, 'message': 'Password updated.', 'token': token.key})


# ═══════════════════════════ VIEWSETS ═══════════════════════════

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Category.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location', 'receipt_note']
    ordering_fields = ['date', 'amount', 'created_at', 'title']
    ordering = ['-date', '-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ExpenseCreateSerializer
        return ExpenseSerializer

    def get_queryset(self):
        if self.action in ['list', 'dashboard']:
            _materialize_recurring_expenses(self.request.user)

        qs = Expense.objects.filter(user=self.request.user).select_related('category').prefetch_related('tags')

        # Date range filters
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                qs = qs.filter(date__gte=parsed)
        if date_to:
            parsed = parse_date(date_to)
            if parsed:
                qs = qs.filter(date__lte=parsed)

        # Category filter
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category_id=category)

        # Payment method filter
        payment = self.request.query_params.get('payment_method')
        if payment:
            qs = qs.filter(payment_method=payment)

        # Amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            qs = qs.filter(amount__gte=min_amount)
        if max_amount:
            qs = qs.filter(amount__lte=max_amount)

        # Period shortcut
        period = self.request.query_params.get('period')
        if period:
            today = date.today()
            if period == 'today':
                qs = qs.filter(date=today)
            elif period == 'week':
                qs = qs.filter(date__gte=today - timedelta(days=7))
            elif period == 'month':
                qs = qs.filter(date__gte=today - timedelta(days=30))
            elif period == 'quarter':
                qs = qs.filter(date__gte=today - timedelta(days=90))
            elif period == 'year':
                qs = qs.filter(date__gte=today - timedelta(days=365))

        # Tag filter
        tag = self.request.query_params.get('tag')
        if tag:
            qs = qs.filter(tags__id=tag)

        return qs.distinct()

    def perform_create(self, serializer):
        is_recurring = serializer.validated_data.get('is_recurring', False)
        freq = serializer.validated_data.get('recurring_frequency', '')
        exp_date = serializer.validated_data.get('date', date.today())
        next_date = _advance_date(exp_date, freq) if is_recurring and freq else None
        serializer.save(user=self.request.user, next_recurring_date=next_date)

    def perform_update(self, serializer):
        is_recurring = serializer.validated_data.get('is_recurring', serializer.instance.is_recurring)
        freq = serializer.validated_data.get('recurring_frequency', serializer.instance.recurring_frequency)
        exp_date = serializer.validated_data.get('date', serializer.instance.date)
        next_date = _advance_date(exp_date, freq) if is_recurring and freq else None
        serializer.save(next_recurring_date=next_date)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Comprehensive dashboard stats."""
        _materialize_recurring_expenses(request.user)
        today = date.today()
        month_start = today - timedelta(days=30)
        week_start = today - timedelta(days=7)

        all_expenses = Expense.objects.filter(user=request.user).select_related('category').prefetch_related('tags')
        month_expenses = all_expenses.filter(date__gte=month_start, date__lte=today)
        week_expenses = all_expenses.filter(date__gte=week_start, date__lte=today)
        today_expenses = all_expenses.filter(date=today)

        month_summary = month_expenses.aggregate(
            total=Sum('amount'), count=Count('id'), avg=Avg('amount')
        )
        prev_month_start = month_start - timedelta(days=30)
        prev_month = all_expenses.filter(date__gte=prev_month_start, date__lt=month_start)
        prev_total = prev_month.aggregate(total=Sum('amount'))['total'] or 0

        curr_total = float(month_summary['total'] or 0)
        month_change = ((curr_total - float(prev_total)) / float(prev_total) * 100) if prev_total else 0

        # Daily trend (last 7 days)
        daily_trend = []
        for i in range(7):
            d = today - timedelta(days=6 - i)
            day_total = week_expenses.filter(date=d).aggregate(t=Sum('amount'))['t'] or 0
            daily_trend.append({'date': d.isoformat(), 'amount': float(day_total)})

        # Category breakdown
        by_category = month_expenses.values(
            'category__name', 'category__color', 'category__icon'
        ).annotate(total=Sum('amount'), count=Count('id')).order_by('-total')[:8]

        # Payment method breakdown
        by_payment = month_expenses.values('payment_method').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total')

        # Recent expenses
        recent = ExpenseSerializer(all_expenses[:5], many=True).data

        return Response({
            'summary': {
                'total_expenses': float(month_summary['total'] or 0),
                'transaction_count': month_summary['count'] or 0,
                'average_transaction': float(month_summary['avg'] or 0),
                'today_total': float(today_expenses.aggregate(t=Sum('amount'))['t'] or 0),
                'week_total': float(week_expenses.aggregate(t=Sum('amount'))['t'] or 0),
                'month_change_pct': round(month_change, 1),
            },
            'daily_trend': daily_trend,
            'by_category': list(by_category),
            'by_payment': list(by_payment),
            'recent_expenses': recent,
        })

    @action(detail=False, methods=['post', 'delete'], url_path='bulk-delete')
    def bulk_delete(self, request):
        """Delete multiple expenses."""
        ids = request.data.get('ids', [])
        if not isinstance(ids, list) or not ids:
            return Response({'error': 'No IDs provided.'}, status=status.HTTP_400_BAD_REQUEST)
        deleted = Expense.objects.filter(user=request.user, id__in=ids).delete()
        return Response({'deleted': deleted[0]})

    @action(detail=False, methods=['get'], url_path='export-csv')
    def export_csv(self, request):
        """Export filtered expenses as CSV."""
        qs = self.get_queryset()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Title', 'Category', 'Amount', 'Payment Method', 'Tags', 'Location', 'Receipt Note', 'Description'])
        for exp in qs:
            tags_str = '; '.join(t.name for t in exp.tags.all())
            writer.writerow([
                exp.date,
                exp.title,
                exp.category.name if exp.category else '',
                exp.amount,
                exp.payment_method,
                tags_str,
                exp.location,
                exp.receipt_note,
                exp.description,
            ])
        return response


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Budget.objects.filter(user=self.request.user).select_related('category')
        if self.request.query_params.get('active_only'):
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def analysis(self, request):
        """Budget vs spending analysis for all active budgets."""
        budgets = self.get_queryset().filter(is_active=True)
        today = date.today()
        analysis = []

        for budget in budgets:
            if budget.period == 'weekly':
                start = today - timedelta(days=7)
            elif budget.period == 'monthly':
                start = today.replace(day=1)
            else:
                start = today.replace(month=1, day=1)

            spent = Expense.objects.filter(
                user=request.user,
                category=budget.category,
                date__gte=start,
                date__lte=today,
            ).aggregate(total=Sum('amount'))['total'] or 0

            pct = (float(spent) / float(budget.amount)) * 100 if budget.amount > 0 else 0

            if pct >= 100:
                budget_status = 'over'
            elif pct >= budget.alert_threshold:
                budget_status = 'warning'
            else:
                budget_status = 'safe'

            analysis.append({
                'id': budget.id,
                'category': budget.category.name,
                'category_color': budget.category.color,
                'category_icon': budget.category.icon,
                'budget_amount': float(budget.amount),
                'spent_amount': float(spent),
                'remaining': max(0, float(budget.amount) - float(spent)),
                'percentage_used': round(pct, 1),
                'status': budget_status,
                'period': budget.period,
                'alert_threshold': budget.alert_threshold,
                'notes': budget.notes,
            })

        return Response(sorted(analysis, key=lambda x: x['percentage_used'], reverse=True))


class SavingsGoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_funds(self, request, pk=None):
        goal = self.get_object()
        amount = request.data.get('amount')
        try:
            amount = Decimal(str(amount))
            if not amount.is_finite() or amount <= 0:
                return Response({'error': 'Amount must be positive.'}, status=status.HTTP_400_BAD_REQUEST)
        except (InvalidOperation, TypeError, ValueError):
            return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

        goal.current_amount = min(goal.current_amount + amount, goal.target_amount)
        if goal.current_amount >= goal.target_amount:
            goal.status = 'completed'
        goal.save()
        return Response(SavingsGoalSerializer(goal).data)


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
        pref = self.get_object()
        serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        password = request.data.get('password', '')
        if not password or not user.check_password(password):
            return Response(
                {'error': 'Incorrect password. Account was not deleted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════ ANALYTICS ═══════════════════════════

def _parse_days(raw, default=7):
    try:
        return max(1, min(365, int(raw)))
    except (TypeError, ValueError):
        return default


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expense_predictions(request):
    days = _parse_days(request.query_params.get('days'), default=7)
    category_id = request.query_params.get('category')
    category = None
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
        except (Category.DoesNotExist, ValueError):
            pass
    prediction = ExpensePrediction.predict_expenses(request.user, days, category)
    return Response(prediction)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_forecast(request):
    forecast = ExpensePrediction.get_monthly_forecast(request.user)
    return Response(forecast)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_predictions(request):
    days = _parse_days(request.query_params.get('days'), default=7)
    predictions = ExpensePrediction.get_category_predictions(request.user, days)
    return Response(predictions)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_overview(request):
    """Comprehensive analytics for the analytics page."""
    user = request.user
    period = request.query_params.get('period', 'month')
    today = date.today()

    period_map = {'week': 7, 'month': 30, 'quarter': 90, 'year': 365}
    days = period_map.get(period, 30)
    start = today - timedelta(days=days)

    all_exp = Expense.objects.filter(user=user)
    period_exp = all_exp.filter(date__gte=start, date__lte=today)

    # Daily trend
    daily_data = {}
    for i in range(days):
        d = start + timedelta(days=i)
        daily_data[d.isoformat()] = 0

    for exp in period_exp.values('date').annotate(total=Sum('amount')):
        key = exp['date'].isoformat() if hasattr(exp['date'], 'isoformat') else str(exp['date'])
        daily_data[key] = float(exp['total'])

    daily_trend = [{'date': k, 'amount': v} for k, v in sorted(daily_data.items())]

    # Category breakdown
    by_category = list(period_exp.values(
        'category__name', 'category__color', 'category__icon'
    ).annotate(total=Sum('amount'), count=Count('id')).order_by('-total'))

    # Payment breakdown
    by_payment = list(period_exp.values('payment_method').annotate(
        total=Sum('amount'), count=Count('id')
    ).order_by('-total'))

    # Weekly pattern (day of week)
    weekly_pattern = [0] * 7
    for exp in period_exp:
        weekly_pattern[exp.date.weekday()] += float(exp.amount)

    # Summary stats
    summary = period_exp.aggregate(
        total=Sum('amount'),
        count=Count('id'),
        avg=Avg('amount'),
        max_single=Max('amount'),
        min_single=Min('amount'),
    )

    # Spending streak (consecutive days with spending)
    streak = 0
    for i in range(days):
        d = today - timedelta(days=i)
        if all_exp.filter(date=d).exists():
            streak += 1
        else:
            break

    return Response({
        'period': period,
        'daily_trend': daily_trend,
        'by_category': by_category,
        'by_payment': by_payment,
        'weekly_pattern': weekly_pattern,
        'summary': {
            'total': float(summary['total'] or 0),
            'count': summary['count'] or 0,
            'average': float(summary['avg'] or 0),
            'max_single': float(summary['max_single'] or 0),
            'min_single': float(summary['min_single'] or 0),
            'spending_streak': streak,
        },
    })