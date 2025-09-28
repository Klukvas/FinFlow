from datetime import date, datetime, timedelta
from typing import Optional
from dateutil.relativedelta import relativedelta

from app.models.recurring_payment import RecurringPayment


class PaymentCalculator:
    """Сервис для расчета дат выполнения повторяющихся платежей"""

    @staticmethod
    def calculate_next_execution(recurring_payment: RecurringPayment) -> date:
        """Рассчитать следующую дату выполнения платежа"""
        if recurring_payment.status not in ["active"]:
            return recurring_payment.next_execution

        current_date = recurring_payment.last_executed.date() if recurring_payment.last_executed else recurring_payment.start_date
        schedule_type = recurring_payment.schedule_type
        schedule_config = recurring_payment.schedule_config

        if schedule_type == "daily":
            next_date = current_date + timedelta(days=1)
        elif schedule_type == "weekly":
            day_of_week = schedule_config.get("day_of_week", 0)
            days_ahead = (day_of_week - current_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # Next week
            next_date = current_date + timedelta(days=days_ahead)
        elif schedule_type == "monthly":
            day_of_month = schedule_config.get("day_of_month", 1)
            # Move to next month
            next_month = current_date + relativedelta(months=1)
            # Try to set the day, if it doesn't exist in the month, use the last day
            try:
                next_date = next_month.replace(day=day_of_month)
            except ValueError:
                # Last day of the month
                next_date = next_month.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
        elif schedule_type == "yearly":
            month = schedule_config.get("month", 1)
            day = schedule_config.get("day", 1)
            # Move to next year
            next_year = current_date + relativedelta(years=1)
            try:
                next_date = next_year.replace(month=month, day=day)
            except ValueError:
                # Last day of the month
                next_date = next_year.replace(month=month, day=1) + relativedelta(months=1) - timedelta(days=1)
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")

        # Check if we've reached the end date
        if recurring_payment.end_date and next_date > recurring_payment.end_date:
            return recurring_payment.end_date

        return next_date

    @staticmethod
    def should_execute_today(recurring_payment: RecurringPayment, today: Optional[date] = None) -> bool:
        """Проверить, должен ли платеж выполняться сегодня"""
        if today is None:
            today = date.today()

        if recurring_payment.status != "active":
            return False

        if recurring_payment.next_execution > today:
            return False

        if recurring_payment.end_date and today > recurring_payment.end_date:
            return False

        return True

    @staticmethod
    def calculate_initial_next_execution(schedule_type: str, schedule_config: dict, start_date: date) -> date:
        """Рассчитать первоначальную дату следующего выполнения"""
        if schedule_type == "daily":
            return start_date
        elif schedule_type == "weekly":
            day_of_week = schedule_config.get("day_of_week", 0)
            days_ahead = (day_of_week - start_date.weekday()) % 7
            if days_ahead == 0:
                return start_date  # Today is the target day
            return start_date + timedelta(days=days_ahead)
        elif schedule_type == "monthly":
            day_of_month = schedule_config.get("day_of_month", 1)
            try:
                target_date = start_date.replace(day=day_of_month)
                if target_date >= start_date:
                    return target_date
                else:
                    # Move to next month
                    next_month = start_date + relativedelta(months=1)
                    try:
                        return next_month.replace(day=day_of_month)
                    except ValueError:
                        return next_month.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
            except ValueError:
                # Last day of the month
                return start_date.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
        elif schedule_type == "yearly":
            month = schedule_config.get("month", 1)
            day = schedule_config.get("day", 1)
            try:
                target_date = start_date.replace(month=month, day=day)
                if target_date >= start_date:
                    return target_date
                else:
                    # Move to next year
                    next_year = start_date + relativedelta(years=1)
                    try:
                        return next_year.replace(month=month, day=day)
                    except ValueError:
                        return next_year.replace(month=month, day=1) + relativedelta(months=1) - timedelta(days=1)
            except ValueError:
                # Last day of the month
                return start_date.replace(month=month, day=1) + relativedelta(months=1) - timedelta(days=1)
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
