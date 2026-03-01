# expenses/ml_predictions.py
"""
Machine Learning Prediction Module
Implements Multi-Window Linear Regression and Weighted Prediction algorithms
for expense forecasting without requiring NumPy/Pandas.

Algorithm Summary (matches Section 3.3 of project report):
  - Three independent Linear Regression models are trained on:
      3-month  (90 days)  — weight 0.5  (most recent, highest priority)
      6-month  (180 days) — weight 0.3
      12-month (365 days) — weight 0.2  (long-term pattern)
  - Final Prediction = (3-month × 0.5) + (6-month × 0.3) + (12-month × 0.2)
  - If a window has insufficient data (<3 active days), it is excluded
    and the remaining weights are normalized to always sum to 1.0
  - Confidence is determined by the average R² across all available windows.
"""

from datetime import datetime, timedelta
from django.db.models import Sum
from decimal import Decimal


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
                return 0, 0

            x_values = [float(x) for x in x_values]
            y_values = [float(y) for y in y_values]

            sum_x  = sum(x_values)
            sum_y  = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)

            denominator = (n * sum_x2 - sum_x * sum_x)

            if abs(denominator) < 0.0001:
                # Vertical line — return flat average
                return 0, sum_y / n if n > 0 else 0

            slope     = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n

            return slope, intercept

        except Exception as e:
            print(f"Error in linear_regression: {e}")
            return 0, 0

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
                return 0

            y_values  = [float(y) for y in y_values]
            x_values  = [float(x) for x in x_values]

            y_mean    = sum(y_values) / n
            y_pred    = [slope * x + intercept for x in x_values]

            ss_res = sum((y_act - y_p) ** 2 for y_act, y_p in zip(y_values, y_pred))
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)

            if abs(ss_tot) < 0.0001:
                return 0  # No variance in data — R² undefined

            r_squared = 1 - (ss_res / ss_tot)
            return max(0.0, min(1.0, r_squared))

        except Exception as e:
            print(f"Error in calculate_r_squared: {e}")
            return 0

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

            end_date   = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            query = Expense.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date
            )

            if category:
                query = query.filter(category=category)

            expenses = query.values('date').annotate(
                total=Sum('amount')
            ).order_by('date')

            # Build continuous daily series (zero-fill missing days)
            daily_data   = {}
            current_date = start_date
            while current_date <= end_date:
                daily_data[current_date] = Decimal('0')
                current_date += timedelta(days=1)

            for expense in expenses:
                if expense['total'] is not None:
                    daily_data[expense['date']] = expense['total']

            return daily_data

        except Exception as e:
            print(f"Error in get_daily_expenses: {e}")
            return {}

    # ─────────────────────────────────────────────────────────────
    # SINGLE-WINDOW LINEAR REGRESSION HELPER
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def _run_window(cls, user, days, prediction_days, category=None):
        """
        Run Linear Regression on a single time window.
        Returns a result dict or None if insufficient data.

        Used internally by predict_expenses() for each of the
        3-month, 6-month, and 12-month windows.
        """
        daily = cls.get_daily_expenses(user, days=days, category=category)
        if not daily:
            return None

        amounts   = [float(v) for v in daily.values()]
        non_zero  = sum(1 for a in amounts if a > 0)

        if non_zero < 3:
            return None  # Not enough active spending days

        x_values  = list(range(len(amounts)))
        slope, intercept = cls.linear_regression(x_values, amounts)
        r_squared = cls.calculate_r_squared(x_values, amounts, slope, intercept)

        # Project next value beyond the training window
        next_x   = len(amounts)
        lr_daily = max(0.0, slope * next_x + intercept)
        lr_total = lr_daily * prediction_days

        # Historical statistics for this window
        total_exp = sum(amounts)
        avg_daily = total_exp / max(len(amounts), 1)

        sorted_amounts = sorted(amounts)
        mid            = len(sorted_amounts) // 2
        if len(sorted_amounts) % 2 == 0 and len(sorted_amounts) > 1:
            median_daily = (sorted_amounts[mid - 1] + sorted_amounts[mid]) / 2
        else:
            median_daily = sorted_amounts[mid] if sorted_amounts else 0

        variance = (
            sum((a - avg_daily) ** 2 for a in amounts) / len(amounts)
            if len(amounts) > 1 else 0
        )
        std_dev = variance ** 0.5

        return {
            'lr_daily':    lr_daily,
            'lr_total':    lr_total,
            'r_squared':   r_squared,
            'slope':       slope,
            'avg_daily':   avg_daily,
            'median_daily': median_daily,
            'variance':    variance,
            'std_dev':     std_dev,
            'non_zero':    non_zero,
            'data_points': len(amounts),
        }

    # ─────────────────────────────────────────────────────────────
    # MAIN PREDICTION — MULTI-WINDOW LR
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def predict_expenses(cls, user, prediction_days=7, category=None):
        """
        Predict future expenses using Multi-Window Linear Regression.

        Three LR models are trained on 3-month (90d), 6-month (180d),
        and 12-month (365d) windows. Their predictions are combined:

            Final = (3-month × 0.5) + (6-month × 0.3) + (12-month × 0.2)

        If a window lacks sufficient data, it is excluded and the
        remaining weights are re-normalized to sum to 1.0.

        ALWAYS returns all required keys — even if prediction fails.
        """
        default_result = {
            'prediction_days': prediction_days,
            'algorithms': {
                'linear_regression': {'daily': 0, 'total': 0},
                'simple_average':    {'daily': 0, 'total': 0},
                'weighted_prediction': {'daily': 0, 'total': 0},
            },
            'recommended_prediction': 0,
            'confidence':       'low',
            'confidence_score': 0,
            'trend':            'stable',
            'trend_strength':   0,
            'statistics': {
                'historical_daily_average':  0,
                'historical_daily_median':   0,
                'standard_deviation':        0,
                'variance':                  0,
                'data_points':               0,
                'non_zero_days':             0,
                'windows_used':              0,
            },
            'confidence_interval': {'min': 0, 'max': 0},
        }

        try:
            # ── Step 1: Run LR on each time window ──────────────
            window_results = []
            for days, base_weight in PREDICTION_WINDOWS:
                result = cls._run_window(user, days, prediction_days, category)
                if result is not None:
                    window_results.append({
                        'days':        days,
                        'base_weight': base_weight,
                        'result':      result,
                    })

            if not window_results:
                default_result['message'] = (
                    'Insufficient data — minimum 3 days of expenses required'
                )
                return default_result

            # ── Step 2: Normalize weights for available windows ──
            # e.g. if only 3-month and 6-month data exist (weights 0.5+0.3=0.8),
            # normalize: 3-month → 0.5/0.8 = 0.625, 6-month → 0.3/0.8 = 0.375
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
            # Use the shortest available window for primary stats
            # (most representative of recent behaviour)
            primary = window_results[0]['result']

            avg_r_squared = sum(
                w['result']['r_squared'] for w in window_results
            ) / len(window_results)

            # Overall slope from primary (shortest) window for trend
            primary_slope    = primary['slope']
            primary_avg      = primary['avg_daily']
            primary_std_dev  = primary['std_dev']
            primary_variance = primary['variance']
            primary_median   = primary['median_daily']

            total_non_zero  = max(w['result']['non_zero']   for w in window_results)
            total_points    = max(w['result']['data_points'] for w in window_results)

            # Simple average prediction (from primary window)
            avg_total = primary_avg * prediction_days

            # Best single-window LR (from primary window for display)
            lr_daily_primary = primary['lr_daily']
            lr_total_primary = primary['lr_total']

            # ── Step 5: Confidence scoring ────────────────────────
            # Uses average R² across all windows (bug fix: AND not OR)
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

            # ── Step 7: Confidence interval ───────────────────────
            min_pred = max(0, weighted_total - (primary_std_dev * prediction_days))
            max_pred = weighted_total + (primary_std_dev * prediction_days)

            return {
                'prediction_days': prediction_days,
                'algorithms': {
                    'linear_regression': {
                        'daily': round(lr_daily_primary, 2),
                        'total': round(lr_total_primary, 2),
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
                'recommended_prediction': round(max(0, weighted_total), 2),
                'confidence':       confidence,
                'confidence_score': round(avg_r_squared, 4),
                'trend':            trend,
                'trend_strength':   round(
                    abs(primary_slope / primary_avg) if primary_avg > 0 else 0, 4
                ),
                'statistics': {
                    'historical_daily_average':  round(primary_avg, 2),
                    'historical_daily_median':   round(primary_median, 2),
                    'standard_deviation':        round(primary_std_dev, 2),
                    'variance':                  round(primary_variance, 2),
                    'data_points':               total_points,
                    'non_zero_days':             total_non_zero,
                    'windows_used':              len(window_results),
                },
                'confidence_interval': {
                    'min': round(min_pred, 2),
                    'max': round(max_pred, 2),
                },
                # Window breakdown — useful for debugging / viva
                'window_breakdown': [
                    {
                        'window':     f"{w['days'] // 30}-month",
                        'days':       w['days'],
                        'weight':     round(w['normalized_weight'], 3),
                        'lr_daily':   round(w['result']['lr_daily'], 2),
                        'r_squared':  round(w['result']['r_squared'], 4),
                        'non_zero':   w['result']['non_zero'],
                    }
                    for w in window_results
                ],
            }

        except Exception as e:
            print(f"Error in predict_expenses: {e}")
            import traceback
            traceback.print_exc()
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

            categories  = Category.objects.all()
            predictions = {}

            for category in categories:
                try:
                    # Check if this category has any expense data
                    # Use shortest window (90 days) for the existence check
                    daily = cls.get_daily_expenses(
                        user, days=90, category=category
                    )
                    total = sum(float(a) for a in daily.values())
                    if total == 0:
                        continue

                    prediction = cls.predict_expenses(
                        user, prediction_days, category
                    )

                    predictions[category.name] = {
                        'category_id':  category.id,
                        'color':        category.color,
                        'prediction':   prediction.get('recommended_prediction', 0),
                        'confidence':   prediction.get('confidence', 'low'),
                        'trend':        prediction.get('trend', 'stable'),
                        'daily_average': prediction.get(
                            'statistics', {}
                        ).get('historical_daily_average', 0),
                        'windows_used': prediction.get(
                            'statistics', {}
                        ).get('windows_used', 0),
                    }

                except Exception as e:
                    print(f"Error for category {category.name}: {e}")
                    continue

            return predictions

        except Exception as e:
            print(f"Error in get_category_predictions: {e}")
            import traceback
            traceback.print_exc()
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
            month = cls.predict_expenses(user, prediction_days=30)

            # Weekly breakdown (4 weeks)
            weekly_forecast = []
            for i in range(4):
                start_day    = i * 7 + 1
                end_day      = min((i + 1) * 7, 30)
                days_in_week = end_day - start_day + 1

                week_pred = cls.predict_expenses(user, days_in_week)
                weekly_forecast.append({
                    'week':       i + 1,
                    'days':       f'{start_day}–{end_day}',
                    'prediction': week_pred.get('recommended_prediction', 0),
                    'confidence': week_pred.get('confidence', 'low'),
                })

            category_predictions = cls.get_category_predictions(user, 30)

            return {
                'monthly_total':      month.get('recommended_prediction', 0),
                'confidence':         month.get('confidence', 'low'),
                'trend':              month.get('trend', 'stable'),
                'weekly_breakdown':   weekly_forecast,
                'category_breakdown': category_predictions,
                'confidence_interval': month.get(
                    'confidence_interval', {'min': 0, 'max': 0}
                ),
                'statistics':         month.get('statistics', {}),
                'window_breakdown':   month.get('window_breakdown', []),
            }

        except Exception as e:
            print(f"Error in get_monthly_forecast: {e}")
            return {
                'monthly_total':      0,
                'confidence':         'low',
                'trend':              'stable',
                'weekly_breakdown':   [],
                'category_breakdown': {},
                'confidence_interval': {'min': 0, 'max': 0},
                'statistics':         {},
                'window_breakdown':   [],
            }