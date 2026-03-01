# expenses/management/commands/import_dataset.py
#
# HOW TO USE:
#   1. Place this file at:
#      expenses/management/commands/import_dataset.py
#
#   2. Make sure these folders exist (create __init__.py in each):
#      expenses/management/__init__.py
#      expenses/management/commands/__init__.py
#
#   3. Place your CSV file anywhere, then run:
#      python manage.py import_dataset --file expense_dataset_250_clean.csv --username testuser001 --clear
#
#   Optional flags:
#      --file      path to your CSV (default: expense_dataset_250_clean.csv)
#      --username  which user to import expenses for (default: testuser001)
#      --clear     add this flag to delete existing expenses for that user first

import csv
import os
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from expenses.models import Expense, Category


# ── Maps CSV payment values → your model's PAYMENT_CHOICES keys ──
PAYMENT_MAP = {
    'cash':         'cash',
    'Cash':         'cash',
    'esewa':        'esewa',
    'eSewa':        'esewa',
    'khalti':       'khalti',
    'Khalti':       'khalti',
    'card':         'card',
    'Credit Card':  'card',
    'Debit Card':   'card',
    'netbanking':   'netbanking',
    'NetBanking':   'netbanking',
    'Net Banking':  'netbanking',
    'other':        'other',
    'Other':        'other',
}

# ── Category colors — matches your UI screenshot ──
CATEGORY_COLORS = {
    'Bills':             '#EF4444',
    'Bills & Utilities': '#F97316',
    'Education':         '#3B82F6',
    'Entertainment':     '#8B5CF6',
    'Food':              '#10B981',
    'Food & Dining':     '#059669',
    'Healthcare':        '#EC4899',
    'Housing':           '#6366F1',
    'Others':            '#6B7280',
    'Personal Care':     '#F59E0B',
    'Shopping':          '#14B8A6',
    'Transportation':    '#0EA5E9',
}

CATEGORY_ICONS = {
    'Bills':             'bolt',
    'Bills & Utilities': 'plug',
    'Education':         'graduation-cap',
    'Entertainment':     'film',
    'Food':              'shopping-basket',
    'Food & Dining':     'utensils',
    'Healthcare':        'heartbeat',
    'Housing':           'home',
    'Others':            'ellipsis-h',
    'Personal Care':     'spa',
    'Shopping':          'shopping-bag',
    'Transportation':    'bus',
}


class Command(BaseCommand):
    help = 'Import expense dataset from CSV into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='expense_dataset_250.csv',
            help='Path to the CSV file (default: expense_dataset_250.csv)'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='testuser001',
            help='Username to assign expenses to (default: testuser001)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing expenses for this user before importing'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        username = options['username']
        clear    = options['clear']

        # ── 1. Resolve file path ──────────────────────────────────────
        if not os.path.isabs(csv_file):
            # look relative to where manage.py lives
            base = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )))
            csv_file = os.path.join(base, csv_file)

        if not os.path.exists(csv_file):
            raise CommandError(
                f'\n❌ File not found: {csv_file}\n'
                f'   Put the CSV next to manage.py and run:\n'
                f'   python manage.py import_dataset --file expense_dataset_250.csv'
            )

        # ── 2. Get or create user ─────────────────────────────────────
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'👤 Using existing user: {username}')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                password='testpass123',
                email=f'{username}@example.com'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Created new user: {username}  (password: testpass123)'
                )
            )

        # ── 3. Optionally clear existing expenses ────────────────────
        if clear:
            deleted, _ = Expense.objects.filter(user=user).delete()
            self.stdout.write(
                self.style.WARNING(f'🗑  Deleted {deleted} existing expenses for {username}')
            )

        # ── 4. Pre-create all 12 categories ──────────────────────────
        self.stdout.write('📂 Setting up categories...')
        category_cache = {}

        for name, color in CATEGORY_COLORS.items():
            icon = CATEGORY_ICONS.get(name, 'folder')
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'color': color, 'icon': icon}
            )
            category_cache[name] = cat
            status = '  created' if created else '  exists'
            self.stdout.write(f'   {status}: {name}')

        # ── 5. Read & import CSV ──────────────────────────────────────
        self.stdout.write(f'\n📥 Reading: {os.path.basename(csv_file)}')

        imported  = 0
        skipped   = 0
        errors    = []

        with open(csv_file, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # row 1 = header
                try:
                    # Title
                    title = row.get('title', '').strip()
                    if not title:
                        errors.append(f'Row {row_num}: empty title — skipped')
                        skipped += 1
                        continue

                    # Amount
                    try:
                        amount = Decimal(str(row.get('amount', '0')).strip())
                        if amount <= 0:
                            raise ValueError('must be > 0')
                    except Exception:
                        errors.append(f'Row {row_num}: invalid amount "{row.get("amount")}" — skipped')
                        skipped += 1
                        continue

                    # Date — CSV uses M/D/YYYY format (e.g. 12/1/2025)
                    raw_date = row.get('date', '').strip()
                    try:
                        expense_date = datetime.strptime(raw_date, '%m/%d/%Y').date()
                    except ValueError:
                        try:
                            expense_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f'Row {row_num}: bad date "{raw_date}" — skipped')
                            skipped += 1
                            continue

                    # Category
                    cat_name = row.get('category', '').strip()
                    category = category_cache.get(cat_name)
                    if not category:
                        # auto-create unknown category
                        category, _ = Category.objects.get_or_create(
                            name=cat_name,
                            defaults={'color': '#6B7280', 'icon': 'folder'}
                        )
                        category_cache[cat_name] = category

                    # Payment method — map CSV value to model key
                    raw_payment = row.get('payment_method', 'cash').strip()
                    payment_method = PAYMENT_MAP.get(raw_payment, 'other')

                    # Description
                    description = row.get('description', '').strip()

                    # Create expense
                    Expense.objects.create(
                        user=user,
                        title=title,
                        amount=amount,
                        category=category,
                        date=expense_date,
                        description=description,
                        payment_method=payment_method,
                    )
                    imported += 1

                except Exception as e:
                    errors.append(f'Row {row_num}: unexpected error — {e}')
                    skipped += 1

        # ── 6. Summary ────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Imported : {imported} expenses')
        )
        if skipped:
            self.stdout.write(
                self.style.WARNING(f'⚠  Skipped  : {skipped} rows')
            )
        if errors:
            self.stdout.write('\nDetails:')
            for err in errors:
                self.stdout.write(f'   {err}')

        self.stdout.write('─' * 50)
        self.stdout.write(
            f'\n🚀 Done! Login as "{username}" to see the data in your app.'
        )
        if user.username == 'testuser001':
            self.stdout.write(f'   Password: testpass123')