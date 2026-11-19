"""
Expense Management System — Serializers
"""
from datetime import date as date_type
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Category, Tag, Expense, Budget, SavingsGoal, UserPreference


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def validate_email(self, value):
        value = value.strip()
        users = User.objects.filter(email__iexact=value)
        if self.instance:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise serializers.ValidationError('This email address is already in use.')
        return value


class CategorySerializer(serializers.ModelSerializer):
    expense_count = serializers.SerializerMethodField()
    icon = serializers.RegexField(regex=r'^[a-z0-9-]+$', max_length=50, required=False)

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_expense_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.expenses.filter(user=request.user).count()
        return 0


class TagSerializer(serializers.ModelSerializer):
    color = serializers.RegexField(
        regex=r'^#[0-9A-Fa-f]{6}$',
        max_length=7,
        required=False,
        default='#6366f1',
    )

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Tag name cannot be empty.')
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            qs = Tag.objects.filter(user=request.user, name__iexact=cleaned)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('You already have a tag with this name.')
        return cleaned


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    tag_names = serializers.SerializerMethodField()
    tags_detail = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            'id', 'user', 'title', 'amount', 'category', 'category_name',
            'category_color', 'category_icon', 'date', 'description',
            'payment_method', 'tags', 'tag_names', 'tags_detail',
            'is_recurring', 'recurring_frequency', 'next_recurring_date',
            'location', 'receipt_note', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'next_recurring_date', 'created_at', 'updated_at']

    def get_tag_names(self, obj):
        return [{'id': t.id, 'name': t.name, 'color': t.color} for t in obj.tags.all()]

    def get_tags_detail(self, obj):
        return self.get_tag_names(obj)

    def validate_date(self, value):
        if value > date_type.today():
            raise serializers.ValidationError('Expense date cannot be in the future.')
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        if value > 10_000_000:
            raise serializers.ValidationError('Amount seems unreasonably large.')
        return value

    def validate_title(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError('Title cannot be empty.')
        return value.strip()

    def validate(self, attrs):
        is_recurring = attrs.get('is_recurring', getattr(self.instance, 'is_recurring', False))
        frequency = attrs.get('recurring_frequency', getattr(self.instance, 'recurring_frequency', ''))
        if is_recurring:
            if frequency not in ('daily', 'weekly', 'monthly', 'yearly'):
                raise serializers.ValidationError({
                    'recurring_frequency': 'Select a valid frequency (daily, weekly, monthly, or yearly) for recurring expenses.'
                })
        else:
            attrs['recurring_frequency'] = ''
        return attrs


class ExpenseCreateSerializer(ExpenseSerializer):
    """Serializer for creating/updating expenses — allows user-scoped tag assignment."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.none(),
        many=True,
        required=False,
    )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            fields['tags'].child_relation.queryset = Tag.objects.filter(user=request.user)
        return fields


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)

    class Meta:
        model = Budget
        fields = [
            'id', 'user', 'category', 'category_name', 'category_color',
            'category_icon', 'amount', 'period', 'alert_threshold',
            'notes', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Budget amount must be greater than zero.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        category = attrs.get('category', getattr(self.instance, 'category', None))
        period = attrs.get('period', getattr(self.instance, 'period', 'monthly'))
        if request and category:
            budgets = Budget.objects.filter(
                user=request.user,
                category=category,
                period=period,
            )
            if self.instance:
                budgets = budgets.exclude(pk=self.instance.pk)
            if budgets.exists():
                raise serializers.ValidationError({
                    'category': 'A budget already exists for this category and period.'
                })
        return attrs

    def validate_alert_threshold(self, value):
        if not (10 <= value <= 100):
            raise serializers.ValidationError('Alert threshold must be between 10 and 100.')
        return value


class SavingsGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    remaining_amount = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'user', 'title', 'target_amount', 'current_amount',
            'target_date', 'status', 'notes', 'progress_percentage',
            'remaining_amount', 'days_remaining', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Target amount must be greater than zero.')
        return value

    def validate_current_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('Current amount cannot be negative.')
        return value

    def get_remaining_amount(self, obj):
        return float(max(0, obj.target_amount - obj.current_amount))

    def get_days_remaining(self, obj):
        if obj.target_date:
            delta = obj.target_date - date_type.today()
            return delta.days
        return None


class UserPreferenceSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.ReadOnlyField()

    class Meta:
        model = UserPreference
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at', 'currency_symbol']