from sqlalchemy import func, case
from datetime import datetime, timedelta
from .models import Expense, User

def get_stats(db_session, user_id: int, period: str = "day"):
    """
    Возвращает статистику расходов пользователя за указанный период.
    :param db_session: Сессия базы данных.
    :param user_id: ID пользователя.
    :param period: 'day', 'week', 'month'.
    :return: (total_amount, expenses_by_category)
    """
    today = datetime.utcnow().date()
    if period == "day":
        start_date = datetime.combine(today, datetime.min.time())
    elif period == "week":
        start_date = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
    elif period == "month":
        start_date = datetime.combine(today.replace(day=1), datetime.min.time())
    else:
        return 0, []

    # Запрос для получения общей суммы и расходов по категориям
    query = db_session.query(
        func.sum(Expense.amount),
        Expense.category
    ).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date
    ).group_by(
        Expense.category
    ).order_by(
        func.sum(Expense.amount).desc()
    )
    
    expenses_by_category = query.all()
    
    total_amount = sum(amount for amount, category in expenses_by_category)

    return total_amount, expenses_by_category
