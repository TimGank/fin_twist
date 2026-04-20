import io
import matplotlib.pyplot as plt
import pandas as pd # <-- Добавили pandas
from core.db import get_expense_stats, get_user_expenses # <-- Добавили get_user_expenses

def generate_stats_chart(user_id: int) -> io.BytesIO | None:
    """Генерирует круговую диаграмму трат и возвращает ее в виде байтов (в памяти)."""
    data = get_expense_stats(user_id)

    if not data:
        return None  # Если трат нет, возвращаем пустоту

    # Разделяем данные на два списка для графика
    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    # Настраиваем стиль графика (чтобы было красиво)
    plt.style.use('ggplot')
    plt.figure(figsize=(7, 7))

    # Рисуем "пирог" с процентами
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140,
            textprops={'fontsize': 12}, wedgeprops={'edgecolor': 'white'})
    plt.title("Твоя финансовая картина", fontsize=16, fontweight='bold', pad=20)

    # ТОТ САМЫЙ СЕНЬОРСКИЙ ТРЮК: Сохраняем картинку в оперативную память
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)  # Перематываем "пленку" байтов в начало, чтобы бот смог ее прочитать

    plt.close()  # Обязательно очищаем память, чтобы сервер не взорвался от утечек

    return buf


def generate_excel_export(user_id: int) -> io.BytesIO | None:
    """Генерирует Excel-файл со всеми тратами в памяти."""
    raw_data = get_user_expenses(user_id)

    if not raw_data:
        return None

    # Превращаем сырые данные из базы в мощный DataFrame
    df = pd.DataFrame(raw_data, columns=['Сумма', 'Категория', 'Описание', 'Дата'])

    # Сеньорский штрих: делаем дату красивой и читаемой (убираем лишние миллисекунды)
    df['Дата'] = pd.to_datetime(df['Дата']).dt.strftime('%Y-%m-%d %H:%M')

    # Создаем буфер в оперативной памяти
    buf = io.BytesIO()

    # Записываем датафрейм в буфер как Excel-файл
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='История трат')

        # Делаем колонки пошире для красоты (автоширина)
        worksheet = writer.sheets['История трат']
        worksheet.column_dimensions['A'].width = 12  # Сумма
        worksheet.column_dimensions['B'].width = 15  # Категория
        worksheet.column_dimensions['C'].width = 30  # Описание
        worksheet.column_dimensions['D'].width = 20  # Дата

    buf.seek(0)  # Перематываем байты в начало
    return buf