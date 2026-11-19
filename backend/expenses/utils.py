"""
Expense Management System — Utilities
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'success': False,
            'status_code': response.status_code,
            'errors': response.data,
        }

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                error_data['message'] = str(response.data['detail'])
            else:
                error_data['message'] = 'Validation error. Please check the submitted data.'
        else:
            error_data['message'] = str(response.data)

        response.data = error_data

    return response


def get_date_range(period):
    """Return (start_date, end_date) for a given period string."""
    from datetime import date, timedelta

    today = date.today()

    if period == 'weekly':
        start = today - timedelta(days=7)
    elif period == 'monthly':
        start = today.replace(day=1)
    elif period == 'quarterly':
        month = ((today.month - 1) // 3) * 3 + 1
        start = today.replace(month=month, day=1)
    elif period == 'yearly':
        start = today.replace(month=1, day=1)
    else:
        start = today - timedelta(days=30)

    return start, today


def format_currency(amount, symbol='Rs.'):
    """Format a number as currency string."""
    return f"{symbol}{amount:,.2f}"