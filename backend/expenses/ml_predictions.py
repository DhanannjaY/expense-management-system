"""
Machine Learning Prediction Module
Implements Multi-Window Linear Regression and Weighted Prediction algorithms
for expense forecasting without requiring NumPy/Pandas.

Algorithm Summary:
- Three independent Linear Regression models are trained on:
      3-month  (90 days)  — weight 0.5  (most recent, highest priority)
      6-month  (180 days) — weight 0.3
      12-month (365 days) — weight 0.2  (long-term pattern)
- Final Prediction = (3-month × 0.5) + (6-month × 0.3) + (12-month × 0.2)
- If a window has insufficient data (<3 active days), it is excluded
  and the remaining weights are normalized to always sum to 1.0
- Confidence is determined by the average R² across all available windows.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum

logger = logging.getLogger(__name__)

# Time windows and their weights for the multi-window prediction
PREDICTION_WINDOWS = [
    (90,  0.5),   # 3-month  — highest weight (most recent)
    (180, 0.3),   # 6-month
    (365, 0.2),   # 12-month — lowest weight (oldest)
]


class ExpensePrediction:
    """
    Expense prediction using multi-window Linear Regression.
    Pure Python implementation — no NumPy or Pandas required.
    """

    # ─────────────────────────────────────────────────────────────
    # CORE MATH UTILITIES
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def linear_regression(x_values, y_values):
        """
        Calculate linear regression slope and intercept
        using the Ordinary Least Squares (OLS) method.
        Formula: y = mx + b
        Returns: (slope m, intercept b)
        """
        try:
            n = len(x_values)
            if n < 2:
                return 0.0, 0.0

            x_values = [float(x) for x in x_values]
            y_values = [float(y) for y in y_values]

            sum_x  = sum(x_values)
            sum_y  = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)

            denominator = n * sum_x2 - sum_x * sum_x

            if abs(denominator) < 0.0001:
                return 0.0, sum_y / n if n > 0 else 0.0

            slope     = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n

            return slope, intercept

        except Exception:
            logger.exception("Error in linear_regression")
            return 0.0, 0.0

    @staticmethod
    def calculate_r_squared(x_values, y_values, slope, intercept):
        """
        Calculate R² (coefficient of determination).
        Measures how well the regression line fits the data.
        R² = 1 means perfect fit; R² = 0 means no better than the mean.
        """
        try:
            n = len(y_values)
            if n == 0:
                return 0.0

            y_values = [float(y) for y in y_values]
            x_values = [float(x) for x in x_values]

            y_mean = sum(y_values) / n
            y_pred = [slope * x + intercept for x in x_values]

            ss_res = sum((y_act - y_p) ** 2 for y_act, y_p in zip(y_values, y_pred))
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)

            if abs(ss_tot) < 0.0001:
                return 0.0

            r_squared = 1.0 - (ss_res / ss_tot)
            return max(0.0, min(1.0, r_squared))

        except Exception:
            logger.exception("Error in calculate_r_squared")
            return 0.0

    # ─────────────────────────────────────────────────────────────
    # DATA RETRIEVAL
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def get_daily_expenses(cls, user, days=90, category=None):
        """
        Get daily expense totals for the last N days.
        Zero-fills days with no expenses so the time series is continuous.
        Returns: dict {date: Decimal amount}
        """
        try:
            from .models import Expense

            end_date   = date.today()
            start_date = end_date - timedelta(days=days)

            query = Expense.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )

            if category:
                query = query.filter(category=category)

            expenses = query.values('date').annotate(
                total=Sum('amount')
            ).order_by('date')

            daily_data   = {}
            current_date = start_date
            while current_date <= end_date:
                daily_data[current_date] = Decimal('0')
                current_date += timedelta(days=1)

            for expense in expenses:
                if expense['total'] is not None:
                    daily_data[expense['date']] = expense['total']

            return daily_data

        except Exception:
            logger.exception("Error in get_daily_expenses")
            return {}

    # ─────────────────────────────────────────────────────────────
    # SINGLE-WINDOW LINEAR REGRESSION HELPER
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def _run_window_from_series(cls, amounts, prediction_days):
        """
        Run Linear Regression on a pre-sliced list of daily float amounts.
        Returns a result dict or None if insufficient data (< 3 active days).
        """
        if not amounts:
            return None

        non_zero = sum(1 for a in amounts if a > 0)
        if non_zero < 3:
            return None

        x_values = list(range(len(amounts)))
        slope, intercept = cls.linear_regression(x_values, amounts)
        r_squared = cls.calculate_r_squared(x_values, amounts, slope, intercept)

        next_x   = len(amounts)
        lr_daily = max(0.0, slope * next_x + intercept)
        lr_total = lr_daily * prediction_days

        total_exp = sum(amounts)
        avg_daily = total_exp / len(amounts)

        sorted_amounts = sorted(amounts)
        mid            = len(sorted_amounts) // 2
        if len(sorted_amounts) % 2 == 0 and len(sorted_amounts) > 1:
            median_daily = (sorted_amounts[mid - 1] + sorted_amounts[mid]) / 2
        else:
            median_daily = sorted_amounts[mid]

        variance = (
            sum((a - avg_daily) ** 2 for a in amounts) / len(amounts)
            if len(amounts) > 1 else 0.0
        )
        std_dev = variance ** 0.5

        return {
            'lr_daily':     lr_daily,
            'lr_total':     lr_total,
            'r_squared':    r_squared,
            'slope':        slope,
            'avg_daily':    avg_daily,
            'median_daily': median_daily,
            'variance':     variance,
            'std_dev':      std_dev,
            'non_zero':     non_zero,
            'data_points':  len(amounts),
        }

    # ─────────────────────────────────────────────────────────────
    # MAIN PREDICTION — MULTI-WINDOW LR
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def predict_expenses(cls, user, prediction_days=7, category=None, _full_series=None):
        """
        Predict future expenses using Multi-Window Linear Regression.

        Three LR models are trained on 3-month (90d), 6-month (180d),
        and 12-month (365d) windows. Their predictions are combined:

            Final = (3-month × 0.5) + (6-month × 0.3) + (12-month × 0.2)

        If a window lacks sufficient data, it is excluded and the
        remaining weights are re-normalized to sum to 1.0.
        """
        default_result = {
            'prediction_days': prediction_days,
            'algorithms': {
                'linear_regression':   {'daily': 0, 'total': 0},
                'simple_average':      {'daily': 0, 'total': 0},
                'weighted_prediction': {'daily': 0, 'total': 0},
            },
            'recommended_prediction': 0,
            'confidence':       'low',
            'confidence_score': 0,
            'trend':            'stable',
            'trend_strength':   0,
            'statistics': {
                'historical_daily_average': 0,
                'historical_daily_median':  0,
                'standard_deviation':       0,
                'variance':                 0,
                'data_points':              0,
                'non_zero_days':            0,
                'windows_used':             0,
            },
            'confidence_interval': {'min': 0, 'max': 0},
            'window_breakdown': [],
        }

        try:
            max_days = max(w[0] for w in PREDICTION_WINDOWS)
            if _full_series is None:
                daily_map = cls.get_daily_expenses(user, days=max_days, category=category)
                _full_series = [float(v) for v in daily_map.values()]

            if not _full_series:
                default_result['message'] = 'Insufficient data — minimum 3 days of expenses required'
                return default_result

            # ── Step 1: Run LR on each time window ──────────────
            window_results = []
            for days, base_weight in PREDICTION_WINDOWS:
                window_slice = _full_series[-(days + 1):]
                result = cls._run_window_from_series(window_slice, prediction_days)
                if result is not None:
                    window_results.append({
                        'days':        days,
                        'base_weight': base_weight,
                        'result':      result,
                    })

            if not window_results:
                default_result['message'] = 'Insufficient data — minimum 3 days of expenses required'
                return default_result

            # ── Step 2: Normalize weights for available windows ──
            total_weight = sum(w['base_weight'] for w in window_results)
            for w in window_results:
                w['normalized_weight'] = w['base_weight'] / total_weight

            # ── Step 3: Weighted final prediction ───────────────
            weighted_daily = sum(
                w['result']['lr_daily'] * w['normalized_weight']
                for w in window_results
            )
            weighted_total = weighted_daily * prediction_days

            # ── Step 4: Aggregate statistics ─────────────────────
            primary          = window_results[0]['result']
            avg_r_squared    = sum(w['result']['r_squared'] for w in window_results) / len(window_results)
            primary_slope    = primary['slope']
            primary_avg      = primary['avg_daily']
            primary_std_dev  = primary['std_dev']
            primary_variance = primary['variance']
            primary_median   = primary['median_daily']

            total_non_zero = max(w['result']['non_zero']    for w in window_results)
            total_points   = max(w['result']['data_points'] for w in window_results)
            avg_total      = primary_avg * prediction_days

            # ── Step 5: Confidence scoring ────────────────────────
            if avg_r_squared > 0.7 and primary_variance < (primary_avg ** 2):
                confidence = 'high'
            elif avg_r_squared > 0.4 and primary_variance < (primary_avg ** 2 * 2):
                confidence = 'medium'
            else:
                confidence = 'low'

            # ── Step 6: Trend detection ───────────────────────────
            if primary_avg > 0:
                if primary_slope > primary_avg * 0.1:
                    trend = 'increasing'
                elif primary_slope < -primary_avg * 0.1:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'

            # ── Step 7: Confidence interval (√N scaling) ──────────
            spread   = primary_std_dev * (max(1, prediction_days) ** 0.5)
            min_pred = max(0.0, weighted_total - spread)
            max_pred = weighted_total + spread

            return {
                'prediction_days': prediction_days,
                'algorithms': {
                    'linear_regression': {
                        'daily': round(primary['lr_daily'], 2),
                        'total': round(primary['lr_total'], 2),
                    },
                    'simple_average': {
                        'daily': round(primary_avg, 2),
                        'total': round(avg_total, 2),
                    },
                    'weighted_prediction': {
                        'daily': round(weighted_daily, 2),
                        'total': round(weighted_total, 2),
                    },
                },
                'recommended_prediction': round(max(0.0, weighted_total), 2),
                'confidence':       confidence,
                'confidence_score': round(avg_r_squared, 4),
                'trend':            trend,
                'trend_strength':   round(
                    abs(primary_slope / primary_avg) if primary_avg > 0 else 0, 4
                ),
                'statistics': {
                    'historical_daily_average': round(primary_avg, 2),
                    'historical_daily_median':  round(primary_median, 2),
                    'standard_deviation':       round(primary_std_dev, 2),
                    'variance':                 round(primary_variance, 2),
                    'data_points':              total_points,
                    'non_zero_days':            total_non_zero,
                    'windows_used':             len(window_results),
                },
                'confidence_interval': {
                    'min': round(min_pred, 2),
                    'max': round(max_pred, 2),
                },
                'window_breakdown': [
                    {
                        'window':    f"{w['days'] // 30}-month",
                        'days':      w['days'],
                        'weight':    round(w['normalized_weight'], 3),
                        'lr_daily':  round(w['result']['lr_daily'], 2),
                        'r_squared': round(w['result']['r_squared'], 4),
                        'non_zero':  w['result']['non_zero'],
                    }
                    for w in window_results
                ],
            }

        except Exception as e:
            logger.exception("Error in predict_expenses")
            default_result['message'] = f'Error: {str(e)}'
            return default_result

    # ─────────────────────────────────────────────────────────────
    # CATEGORY PREDICTIONS
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def get_category_predictions(cls, user, prediction_days=7):
        """
        Get predictions for each expense category.
        Only includes categories with actual spending data.
        """
        try:
            from .models import Category

            max_days    = max(w[0] for w in PREDICTION_WINDOWS)
            categories  = Category.objects.all()
            predictions = {}

            for category in categories:
                try:
                    daily_map   = cls.get_daily_expenses(user, days=max_days, category=category)
                    full_series = [float(a) for a in daily_map.values()]
                    if sum(full_series[-91:]) == 0:
                        continue

                    prediction = cls.predict_expenses(
                        user, prediction_days, category, _full_series=full_series
                    )

                    predictions[category.name] = {
                        'category_id':   category.id,
                        'color':         category.color,
                        'prediction':    prediction.get('recommended_prediction', 0),
                        'confidence':    prediction.get('confidence', 'low'),
                        'trend':         prediction.get('trend', 'stable'),
                        'daily_average': prediction.get('statistics', {}).get('historical_daily_average', 0),
                        'windows_used':  prediction.get('statistics', {}).get('windows_used', 0),
                    }

                except Exception:
                    logger.exception("Error predicting category %s", category.name)
                    continue

            return predictions

        except Exception:
            logger.exception("Error in get_category_predictions")
            return {}

    # ─────────────────────────────────────────────────────────────
    # MONTHLY FORECAST
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def get_monthly_forecast(cls, user):
        """
        Get full 30-day forecast with weekly breakdown
        and per-category predictions.
        """
        try:
            max_days    = max(w[0] for w in PREDICTION_WINDOWS)
            daily_map   = cls.get_daily_expenses(user, days=max_days)
            full_series = [float(v) for v in daily_map.values()]

            month = cls.predict_expenses(user, prediction_days=30, _full_series=full_series)

            weekly_forecast = []
            for i in range(4):
                start_day    = i * 7 + 1
                end_day      = min((i + 1) * 7, 30)
                days_in_week = end_day - start_day + 1

                week_pred = cls.predict_expenses(user, days_in_week, _full_series=full_series)
                weekly_forecast.append({
                    'week':       i + 1,
                    'days':       f'{start_day}–{end_day}',
                    'prediction': week_pred.get('recommended_prediction', 0),
                    'confidence': week_pred.get('confidence', 'low'),
                })

            category_predictions = cls.get_category_predictions(user, 30)

            return {
                'monthly_total':       month.get('recommended_prediction', 0),
                'confidence':          month.get('confidence', 'low'),
                'trend':               month.get('trend', 'stable'),
                'weekly_breakdown':    weekly_forecast,
                'category_breakdown':  category_predictions,
                'confidence_interval': month.get('confidence_interval', {'min': 0, 'max': 0}),
                'statistics':          month.get('statistics', {}),
                'window_breakdown':    month.get('window_breakdown', []),
            }

        except Exception:
            logger.exception("Error in get_monthly_forecast")
            return {
                'monthly_total':       0,
                'confidence':          'low',
                'trend':               'stable',
                'weekly_breakdown':    [],
                'category_breakdown':  {},
                'confidence_interval': {'min': 0, 'max': 0},
                'statistics':          {},
                'window_breakdown':    [],
            }