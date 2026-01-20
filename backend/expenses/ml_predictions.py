# expenses/ml_predictions.py
"""
Machine Learning Prediction Module
Implements Linear Regression and Weighted Prediction algorithms
for expense forecasting without requiring NumPy/Pandas
"""

from datetime import datetime, timedelta
from django.db.models import Sum
from decimal import Decimal


class ExpensePrediction:
    """
    Expense prediction using machine learning algorithms.
    Uses pure Python implementation (no NumPy required).
    """
    
    @staticmethod
    def linear_regression(x_values, y_values):
        """
        Calculate linear regression parameters using Least Squares Method.
        Formula: y = mx + b
        """
        try:
            n = len(x_values)
            if n < 2:
                return 0, 0
            
            x_values = [float(x) for x in x_values]
            y_values = [float(y) for y in y_values]
            
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            denominator = (n * sum_x2 - sum_x * sum_x)
            
            if abs(denominator) < 0.0001:
                average = sum_y / n if n > 0 else 0
                return 0, average
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            return slope, intercept
            
        except Exception as e:
            print(f"Error in linear_regression: {e}")
            return 0, 0
    
    @staticmethod
    def calculate_r_squared(x_values, y_values, slope, intercept):
        """Calculate R² (coefficient of determination)."""
        try:
            n = len(y_values)
            if n == 0:
                return 0
            
            y_values = [float(y) for y in y_values]
            x_values = [float(x) for x in x_values]
            
            y_mean = sum(y_values) / n
            y_predicted = [slope * x + intercept for x in x_values]
            
            ss_res = sum((y_actual - y_pred) ** 2 for y_actual, y_pred in zip(y_values, y_predicted))
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)
            
            if abs(ss_tot) < 0.0001:
                return 0
            
            r_squared = 1 - (ss_res / ss_tot)
            return max(0.0, min(1.0, r_squared))
            
        except Exception as e:
            print(f"Error in calculate_r_squared: {e}")
            return 0
    
    @classmethod
    def get_daily_expenses(cls, user, days=30, category=None):
        """Get daily expense totals for the last N days."""
        try:
            from .models import Expense
            
            end_date = datetime.now().date()
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
            
            daily_data = {}
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
    
    @classmethod
    def predict_expenses(cls, user, prediction_days=7, category=None):
        """
        Predict future expenses using Linear Regression and Weighted Algorithm.
        
        ALWAYS returns all required keys, even if prediction fails.
        """
        # Default return structure
        default_result = {
            'prediction_days': prediction_days,
            'algorithms': {
                'linear_regression': {'daily': 0, 'total': 0},
                'simple_average': {'daily': 0, 'total': 0},
                'weighted_prediction': {'daily': 0, 'total': 0}
            },
            'recommended_prediction': 0,
            'confidence': 'low',
            'confidence_score': 0,
            'trend': 'stable',
            'trend_strength': 0,
            'statistics': {
                'historical_daily_average': 0,
                'historical_daily_median': 0,
                'standard_deviation': 0,
                'variance': 0,
                'data_points': 0,
                'non_zero_days': 0
            },
            'confidence_interval': {'min': 0, 'max': 0}
        }
        
        try:
            # Get historical data
            daily_expenses = cls.get_daily_expenses(user, days=30, category=category)
            
            if not daily_expenses:
                default_result['message'] = 'No expense data available'
                return default_result
            
            # Check if we have enough data
            non_zero_days = sum(1 for amount in daily_expenses.values() if float(amount) > 0)
            
            if non_zero_days < 3:
                default_result['message'] = 'Insufficient data (minimum 3 days required)'
                default_result['statistics']['non_zero_days'] = non_zero_days
                return default_result
            
            # Prepare data
            dates = sorted(daily_expenses.keys())
            amounts = [float(daily_expenses[date]) for date in dates]
            x_values = list(range(len(amounts)))
            
            # Calculate linear regression
            slope, intercept = cls.linear_regression(x_values, amounts)
            r_squared = cls.calculate_r_squared(x_values, amounts, slope, intercept)
            
            # Predictions
            next_x = len(amounts)
            lr_daily = slope * next_x + intercept
            lr_total = lr_daily * prediction_days
            
            # Historical average
            total_expenses = sum(amounts)
            avg_daily = total_expenses / max(len(amounts), 1)
            
            # Median
            sorted_amounts = sorted(amounts)
            median_idx = len(sorted_amounts) // 2
            if len(sorted_amounts) % 2 == 0 and len(sorted_amounts) > 1:
                median_daily = (sorted_amounts[median_idx - 1] + sorted_amounts[median_idx]) / 2
            else:
                median_daily = sorted_amounts[median_idx] if sorted_amounts else 0
            
            avg_total = avg_daily * prediction_days
            
            # Weighted prediction
            weighted_daily = lr_daily * 0.7 + avg_daily * 0.3
            weighted_total = weighted_daily * prediction_days
            
            # Statistics
            if len(amounts) > 1:
                variance = sum((x - avg_daily) ** 2 for x in amounts) / len(amounts)
                std_dev = variance ** 0.5
            else:
                variance = 0
                std_dev = 0
            
            # Confidence
            if r_squared > 0.7 and variance < (avg_daily ** 2):
                confidence = 'high'
            elif r_squared > 0.4 or variance < (avg_daily ** 2 * 2):
                confidence = 'medium'
            else:
                confidence = 'low'
            
            # Trend
            if avg_daily > 0:
                if slope > avg_daily * 0.1:
                    trend = 'increasing'
                elif slope < -avg_daily * 0.1:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            # Confidence interval
            min_pred = weighted_total - (std_dev * prediction_days)
            max_pred = weighted_total + (std_dev * prediction_days)
            
            # Return complete structure
            return {
                'prediction_days': prediction_days,
                'algorithms': {
                    'linear_regression': {
                        'daily': max(0, lr_daily),
                        'total': max(0, lr_total)
                    },
                    'simple_average': {
                        'daily': avg_daily,
                        'total': avg_total
                    },
                    'weighted_prediction': {
                        'daily': max(0, weighted_daily),
                        'total': max(0, weighted_total)
                    }
                },
                'recommended_prediction': max(0, weighted_total),
                'confidence': confidence,
                'confidence_score': r_squared,
                'trend': trend,
                'trend_strength': abs(slope / avg_daily) if avg_daily > 0 else 0,
                'statistics': {
                    'historical_daily_average': avg_daily,
                    'historical_daily_median': median_daily,
                    'standard_deviation': std_dev,
                    'variance': variance,
                    'data_points': len(amounts),
                    'non_zero_days': non_zero_days
                },
                'confidence_interval': {
                    'min': max(0, min_pred),
                    'max': max_pred
                }
            }
            
        except Exception as e:
            print(f"Error in predict_expenses: {e}")
            import traceback
            traceback.print_exc()
            default_result['message'] = f'Error: {str(e)}'
            return default_result
    
    @classmethod
    def get_category_predictions(cls, user, prediction_days=7):
        """Get predictions for each expense category."""
        try:
            from .models import Category
            
            categories = Category.objects.all()
            predictions = {}
            
            for category in categories:
                try:
                    # Get expenses for this category
                    daily_expenses = cls.get_daily_expenses(user, days=30, category=category)
                    
                    # Check if category has any expenses
                    total = sum(float(amount) for amount in daily_expenses.values())
                    if total == 0:
                        continue
                    
                    # Get prediction for this category
                    prediction = cls.predict_expenses(user, prediction_days, category)
                    
                    # Safely extract values with defaults
                    predictions[category.name] = {
                        'category_id': category.id,
                        'color': category.color,
                        'prediction': prediction.get('recommended_prediction', 0),
                        'confidence': prediction.get('confidence', 'low'),
                        'trend': prediction.get('trend', 'stable'),
                        'daily_average': prediction.get('statistics', {}).get('historical_daily_average', 0)
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
    
    @classmethod
    def get_monthly_forecast(cls, user):
        """Get detailed monthly forecast."""
        try:
            month = cls.predict_expenses(user, 30)
            
            # Weekly breakdown
            weekly_forecast = []
            for i in range(4):
                start_day = i * 7 + 1
                end_day = min((i + 1) * 7, 30)
                days_in_week = end_day - start_day + 1
                
                week_pred = cls.predict_expenses(user, days_in_week)
                
                weekly_forecast.append({
                    'week': i + 1,
                    'days': f'{start_day}-{end_day}',
                    'prediction': week_pred.get('recommended_prediction', 0),
                    'confidence': week_pred.get('confidence', 'low')
                })
            
            category_predictions = cls.get_category_predictions(user, 30)
            
            return {
                'monthly_total': month.get('recommended_prediction', 0),
                'confidence': month.get('confidence', 'low'),
                'trend': month.get('trend', 'stable'),
                'weekly_breakdown': weekly_forecast,
                'category_breakdown': category_predictions,
                'confidence_interval': month.get('confidence_interval', {'min': 0, 'max': 0}),
                'statistics': month.get('statistics', {})
            }
            
        except Exception as e:
            print(f"Error in get_monthly_forecast: {e}")
            return {
                'monthly_total': 0,
                'confidence': 'low',
                'trend': 'stable',
                'weekly_breakdown': [],
                'category_breakdown': {},
                'confidence_interval': {'min': 0, 'max': 0},
                'statistics': {}
            }