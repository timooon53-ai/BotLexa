import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

import config  # Импорт настроек

# ======================= НАСТРОЙКИ =======================
user_multipliers = {
    7035308211: 0.30,
    966094117: 0.40,
    7515876699: 0.50,
    7554004957: 0.30
    # добавьте свои ID и множители
}

ALLOWED_USERS_FOR_GET_ACCOUNT = [966094117, 7515876699, 7554004957]
ALLOWED_USERS_FOR_MOVEMENT = [966094117, 7515876699, 7554004957]
ADMIN_ID = config.ADMIN_ID
BOT_TOKEN = config.BOT_TOKEN
ACCOUNTS_FILE_PATH = config.ACCOUNTS_FILE_PATH
BAD_ACCOUNTS_FILE_PATH = config.BAD_ACCOUNTS_FILE_PATH
USERS_FILE_PATH = config.USERS_FILE_PATH
BALANCE_FILE_PATH = config.BALANCE_FILE_PATH
STATS_FILE_PATH = config.STATS_FILE_PATH
TRANSACTIONS_LOG_PATH = config.TRANSACTIONS_LOG_PATH

taxi_section_enabled = True

def init_files():
    if not os.path.exists(ACCOUNTS_FILE_PATH):
        with open(ACCOUNTS_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('Token\n')
    if not os.path.exists(BAD_ACCOUNTS_FILE_PATH):
        open(BAD_ACCOUNTS_FILE_PATH, 'a', encoding='utf-8').close()
    if not os.path.exists(USERS_FILE_PATH):
        open(USERS_FILE_PATH, 'a', encoding='utf-8').close()
    if not os.path.exists(BALANCE_FILE_PATH):
        with open(BALANCE_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('UserID,Balance\n')
    if not os.path.exists(STATS_FILE_PATH):
        with open(STATS_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('UserID,TotalTaken,TotalReturns\n')
    if not os.path.exists(TRANSACTIONS_LOG_PATH):
        open(TRANSACTIONS_LOG_PATH, 'a', encoding='utf-8').close()

# ======================= функции работы с файлами =======================

def save_user(username, user_id, balance=0):
    users = {}
    if os.path.exists(USERS_FILE_PATH):
        with open(USERS_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                users[parts[1]] = line.strip()
    user_line = f"@{username} {user_id} {balance}"
    users[str(user_id)] = user_line
    with open(USERS_FILE_PATH, 'w', encoding='utf-8') as f:
        for u in users.values():
            f.write(u + '\n')

def get_username(user_id):
    if os.path.exists(USERS_FILE_PATH):
        with open(USERS_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[1] == str(user_id):
                return parts[0].lstrip('@')
    return 'unknown'

def get_balance(user_id):
    if os.path.exists(BALANCE_FILE_PATH):
        with open(BALANCE_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) == 2 and parts[0] == str(user_id):
                return int(parts[1])
    return 0

# ВАЖНО: меняем местами функции
def add_balance(user_id, amount):
    # Изначально — увеличение баланса
    balances = {}
    if os.path.exists(BALANCE_FILE_PATH):
        with open(BALANCE_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) == 2:
                balances[parts[0]] = int(parts[1])
    # Теперь делаем списание (уменьшаем)
    current_balance = balances.get(str(user_id), 0)
    new_balance = current_balance - amount
    balances[str(user_id)] = new_balance
    with open(BALANCE_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write('UserID,Balance\n')
        for uid, bal in balances.items():
            f.write(f'{uid},{bal}\n')
    return new_balance

def subtract_balance(user_id, amount):
    # Изначально — списание
    balances = {}
    if os.path.exists(BALANCE_FILE_PATH):
        with open(BALANCE_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) == 2:
                balances[parts[0]] = int(parts[1])
    # Теперь делаем добавление
    current_balance = balances.get(str(user_id), 0)
    new_balance = current_balance + amount
    balances[str(user_id)] = new_balance
    with open(BALANCE_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write('UserID,Balance\n')
        for uid, bal in balances.items():
            f.write(f'{uid},{bal}\n')
    return new_balance

def get_user_stats(user_id):
    total_taken = 0
    total_returns = 0
    if os.path.exists(STATS_FILE_PATH):
        with open(STATS_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) == 3 and parts[0] == str(user_id):
                total_taken = int(parts[1])
                total_returns = int(parts[2])
                break
    return total_taken, total_returns

def increment_total_taken(user_id):
    total_taken, total_returns = get_user_stats(user_id)
    total_taken += 1
    save_user_stats(user_id, total_taken, total_returns)

def increment_total_returns(user_id):
    total_taken, total_returns = get_user_stats(user_id)
    total_returns += 1
    save_user_stats(user_id, total_taken, total_returns)

def save_user_stats(user_id, total_taken, total_returns):
    lines = []
    if os.path.exists(STATS_FILE_PATH):
        with open(STATS_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    updated = False
    for i, line in enumerate(lines[1:], start=1):
        parts = line.strip().split(',')
        if len(parts) == 3 and parts[0] == str(user_id):
            lines[i] = f'{user_id},{total_taken},{total_returns}\n'
            updated = True
            break
    if not updated:
        lines.append(f'{user_id},{total_taken},{total_returns}\n')
    with open(STATS_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write('UserID,TotalTaken,TotalReturns\n')
        for line in lines[1:]:
            f.write(line)

def remove_account_from_file(account):
    if not os.path.exists(ACCOUNTS_FILE_PATH):
        return
    with open(ACCOUNTS_FILE_PATH, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and line.strip() != 'Token']
    if account in lines:
        lines.remove(account)
    with open(ACCOUNTS_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write('Token\n')
        for line in lines:
            f.write(line + '\n')

def add_account_to_bad(account):
    with open(BAD_ACCOUNTS_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(account + '\n')

# ======================= декоратор для админов =======================

def admin_only(func):
    async def wrapper(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
        if update.effective_user.id == ADMIN_ID:
            return await func(update, context)
        else:
            await update.message.reply_text('У вас нет прав доступа!')
    return wrapper

# ======================= обработчики =======================

async def handle_new_user(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    user = update.effective_user
    username = user.username or 'no_username'
    user_id = user.id
    balance = get_balance(user_id)
    save_user(username, user_id, balance)

async def log_balance_change(user_id, amount, category):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # В логах — как есть, с учетом операции
    if amount > 0:
        action = 'пополнил'
    else:
        action = 'списан'
    line = f"{now} - Баланс пользователя {user_id} был {action} на сумму {abs(amount)}. Категория: {category}\n"
    with open(TRANSACTIONS_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line)

async def notify_user_balance_change(user_id, change_type, change_amount, category, bot):
    if change_type == 'пополнил':
        message = f"У вас произошли изменения баланса: {change_type} на {change_amount} ₽. Категория: {category}."
    elif change_type == 'списан':
        message = f"У вас списано {abs(change_amount)} ₽. Категория: {category}."
    else:
        message = f"Обновление баланса: {change_type} {abs(change_amount)} ₽. Категория: {category}."
    try:
        await bot.send_message(chat_id=user_id, text=message)
    except:
        pass

async def select_category_and_notify_admin(update: Update, category):
    await Application.get_current().bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Баланс был пополнен/списан. Категория: {category}"
    )

# ======================= команда /user =======================

@admin_only
async def user_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Использование: /user <ID пользователя>')
        return
    user_id_str = args[0]
    if not user_id_str.isdigit():
        await update.message.reply_text('ID пользователя должно быть числом.')
        return
    user_id = int(user_id_str)

    total_taken, total_returns = get_user_stats(user_id)
    balance = get_balance(user_id)
    username = get_username(user_id)

    message = (
        f"Пользователь: {username} (ID: {user_id})\n"
        f"Баланс: {balance} ₽\n"
        f"Запросов за всё время: {total_returns}"
    )
    await update.message.reply_text(message)

# ======================= команда /start =======================

async def start(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    reply_markup = await main_menu()
    await update.message.reply_text('Бот запущен! Нажмите кнопку ниже.', reply_markup=reply_markup)
    await handle_new_user(update, context)

async def main_menu():
    keyboard = [
        [InlineKeyboardButton("Получить аккаунт", callback_data='get_account')],
        [InlineKeyboardButton("Кабинет", callback_data='cabinet')],
        [InlineKeyboardButton("Заказать такси", callback_data='order_taxi')],
        [InlineKeyboardButton("Движение средств", callback_data='movement')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def show_cabinet(user_id, chat_id, bot):
    balance = get_balance(user_id)
    total_taken, total_returns = get_user_stats(user_id)
    text = (
        f"Ваш ID: {user_id}\n\n"
        f"💰 Баланс: {balance} ₽\n"
        f" ├ Всего взято аккаунтов: {total_taken}\n"
        f" └ Всего возвратов: {total_returns}"
    )
    keyboard = [
        [InlineKeyboardButton("Вернуть аккаунт", callback_data='return_account')],
        [InlineKeyboardButton("Отправить аккаунт", callback_data='send_account')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

# ======================= callback-обработчик =======================

async def button_handler(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or 'no_username'

    if data == 'get_account':
        if user_id not in ALLOWED_USERS_FOR_GET_ACCOUNT:
            await query.message.reply_text('Вам пока не доступна функция получения аккаунтов.\nЕсли вы считаете, что это ошибка, то напишите @DieOnTheWay')
            return
        try:
            with open(ACCOUNTS_FILE_PATH, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and line.strip() != 'Token']
            if not lines:
                await query.message.reply_text('Больше аккаунтов нет.')
                return
            account = lines[0]
            remaining = lines[1:]
            with open(ACCOUNTS_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write('Token\n')
                for acc in remaining:
                    f.write(acc + '\n')
            # лог
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(TRANSACTIONS_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(f"{now_str} - Пользователь {user_id} получил аккаунт: {account}\n")
            # запоминаем для отправки
            context.user_data['last_account'] = account
            # ВНИМАНИЕ: раньше было +180, теперь -180
            amount_for_user = 0
            new_balance = add_balance(user_id, amount_for_user)
            save_user(username, user_id, new_balance)
            await log_balance_change(user_id, amount_for_user, 'аккаунты')
            await notify_user_balance_change(user_id, 'списал', amount_for_user, 'аккаунты', context.bot)
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Вернуть аккаунт", callback_data='return_account')],
                [InlineKeyboardButton("Отправить аккаунт", callback_data='send_account')],
                [InlineKeyboardButton("Выход", callback_data='exit')]
            ])
            await query.message.reply_text(f'Ваш аккаунт: {account}', reply_markup=reply_markup)
        except Exception as e:
            await query.message.reply_text(f'Ошибка: {e}')

    elif data == 'return_account':
        user_data = context.user_data
        account = user_data.get('last_account')
        if not account:
            await query.message.reply_text('Нет аккаунта для возврата.')
            return
        add_account_to_bad(account)
        remove_account_from_file(account)
        # Теперь списание 180
        new_balance = subtract_balance(user_id, 0)
        increment_total_returns(user_id)
        save_user(username, user_id, new_balance)
        # Сообщение
        await log_balance_change(user_id, -0, 'аккаунты')  # списание на 180
        await notify_user_balance_change(user_id, 'списан', 180, 'аккаунты', context.bot)
        await query.message.reply_text('Аккаунт возвращен. Баланс пополнен на 180 рублей.', reply_markup=None)

    elif data == 'send_account':
        user_data = context.user_data
        account = user_data.get('last_account')
        if not account:
            await query.message.reply_text('Нет аккаунта для отправки.')
            return
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Нужно отрефать 🚕\nОт {query.from_user.first_name} (ID:{user_id}):\n*{account}*",
            parse_mode='Markdown'
        )
        remove_account_from_file(account)
        if 'last_account' in context.user_data:
            del context.user_data['last_account']
        await query.message.reply_text('Аккаунт отправлен админу.', reply_markup=None)

    elif data == 'exit':
        reply_markup = await main_menu()
        await query.message.reply_text('Вы в главном меню.', reply_markup=reply_markup)

    elif data == 'cabinet':
        await show_cabinet(user_id, query.message.chat.id, context.bot)

    elif data == 'order_taxi':
        global taxi_section_enabled
        if not taxi_section_enabled:
            await query.message.reply_text("Раздел 'Вызвать такси' сейчас выключен.")
            return
        reply_keyboard = [['Отправить точки текстом', 'Отправить скриншот']]
        await query.message.reply_text(
            'Выберите способ заказа такси кнопками ниже. Учтите, что если вы выбираете "Отправить точки текстом", то цена может отличаться от вашей и будет рассчитана админом по прайсу, который был у него в заказе ☣️',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        # Устанавливаем флаг ожидания варианта
        context.user_data['taxi_choice'] = 'awaiting_method'

    elif data == 'movement':
        if user_id not in ALLOWED_USERS_FOR_MOVEMENT:
            await query.message.reply_text('Вам пока не доступна функция движения средств бота.\nЕсли вы считаете, что это ошибка, то напишите @DieOnTheWay')
            return
        if os.path.exists(TRANSACTIONS_LOG_PATH):
            with open(TRANSACTIONS_LOG_PATH, 'rb') as f:
                await context.bot.send_document(chat_id=query.message.chat.id, document=f, filename='transactions.txt')
        else:
            await query.message.reply_text("Файл с транзакциями не найден.")
    elif data.startswith('category_'):
        category = data.split('_')[1]
        await notify_user_balance_change(ADMIN_ID, 'категория', category, 'category', context.bot)
        await query.message.reply_text(f'Категория "{category}" выбрана.')
    elif data.startswith('transactions_'):
        user_id_trans = int(data.split('_')[1])
        await show_transactions(update, user_id_trans)

async def show_transactions(update: Update, user_id):
    transactions = get_transactions_for_user(user_id)
    if transactions:
        text = "История транзакций:\n" + "\n".join(transactions)
    else:
        text = "У вас пока нет истории транзакций."
    await update.message.reply_text(text)

# ======================= команда /taxi =======================

async def taxi_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text('Доступ только для администратора.')
        return
    if len(context.args) != 2:
        await update.message.reply_text('Использование: /taxi <user_id> <сумма>')
        return
    try:
        user_id_target = int(context.args[0])
        price = float(context.args[1])
        multiplier = user_multipliers.get(user_id_target, 0.40)
        amount = price * multiplier
        new_balance = add_balance(user_id_target, int(amount))
        try:
            await context.bot.send_message(
                chat_id=user_id_target,
                text=f'Вам зачислено {amount:.2f} ₽ ({multiplier*100:.0f}% от {price}).\nВаш текущий баланс: {new_balance} ₽'
            )
        except:
            pass
        await update.message.reply_text(f'Пользователю {user_id_target} зачислено: {amount:.2f} ₽ ({multiplier*100:.0f}% от {price})')
        await notify_user_balance_change(user_id_target, 'зачисление', abs(amount), 'Зачисление', context.bot)
        # Категории
        keyboard = [
            [InlineKeyboardButton("Такси", callback_data='category_taxi')],
            [InlineKeyboardButton("Аккаунты", callback_data='category_accounts')],
            [InlineKeyboardButton("Зачисление", callback_data='category_enrollment')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Выберите категорию для этого движения:', reply_markup=reply_markup)

        # Логируем транзакцию
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"{now} - Такси: пользователю {user_id_target} зачислено {amount:.2f} ₽ ({multiplier*100:.0f}% от {price})\n"
        with open(TRANSACTIONS_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_line)
    except:
        await update.message.reply_text('Некорректные параметры. Используйте /taxi <user_id> <сумма>')

# ======================= команда /info =======================

@admin_only
async def info(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    user_count = 0
    if os.path.exists(USERS_FILE_PATH):
        with open(USERS_FILE_PATH, 'r', encoding='utf-8') as f:
            user_count = len([line for line in f if line.strip()])
    account_count = 0
    if os.path.exists(ACCOUNTS_FILE_PATH):
        with open(ACCOUNTS_FILE_PATH, 'r', encoding='utf-8') as f:
            account_count = len([line for line in f if line.strip() and line.strip() != 'Token'])
    await update.message.reply_markdown(
        "Информация по проекту:\n"
        f"Кол-во юзеров: *{user_count}*\n"
        f"Кол-во аккаунтов под реф: *{account_count}*"
    )

# ======================= команда /commands =======================

@admin_only
async def commands(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    await update.message.reply_text(
        "✨ *Команды для администратора* ✨\n\n"
        "📝 *Управление балансом:*\n"
        "/addbalance `<user_id>` `<amount>` `<category>`  \nПример: `/addbalance 123456789 500 \"Реклама\"`\n— Добавляет указанную сумму баланса пользователю и логирует категорию.\n\n"
        "✍️ *Написать юзеру:*\n"
        "/write `<user_id>` `<text>`  \nПример: `/write 123456789 Привет!`  \n— Отправляет сообщение выбранному пользователю.\n\n"
        "📂 *Загрузить аккаунты:*\n"
        "/addaccount  \nОтправьте файл или список аккаунтов, каждый в новой строке.  \n— Загружает список аккаунтов для дальнейшего использования.\n\n"
        "🔍 *Получить статистику по пользователю:*\n"
        "/user `<user_id>`  \nПример: `/user 123456789`  \n— Показывает статистику аккаунтов, баланс и запросы пользователя.\n\n"
        "ℹ️ *Информация о проекте:*\n"
        "/info  \n— Показывает текущие статистические данные проекта.\n\n"
        "🚗 *Заказать такси (от пользователя):*\n"
        "Отправьте сообщение или скриншот с заказом такси, и бот передаст его админу.\n\n"
        "🛠️ *Дополнительные команды:*\n"
        "/commands — вывод этого списка команд.\n\n"
        "⚙️ *Прочие команды:*\n"
        "/start — запуск бота и приветственное сообщение.\n"
        "/help — помощь по командам.\n"
        "/commands — список команд.\n"
        "/addaccount — добавить аккаунты из файла или текста.\n"
        "/addbalance — изменить баланс пользователя.\n"
        "/write — отправить сообщение пользователю.\n"
        "/info — общая информация о проекте.\n"
        "/taxi — отправить заказ такси админу.\n"
        "/user — получить статистику по пользователю.\n"
        "/delete_account — удалить аккаунт из базы.\n"
        "/addaccount_from_doc — загрузить аккаунты из файла.\n"
        "/stats — получить статистику по всем пользователям.\n"
        "/ban — забанить пользователя.\n"
        "/unban — разбанить пользователя.\n"
        "/broadcast — массовое сообщение.\n"
        "/logout — выйти из системы."
    )

# ======================= команда /stats =======================

@admin_only
async def stats(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    total_users = 0
    total_accounts = 0
    if os.path.exists(USERS_FILE_PATH):
        with open(USERS_FILE_PATH, 'r', encoding='utf-8') as f:
            total_users = len([line for line in f if line.strip()])
    if os.path.exists(ACCOUNTS_FILE_PATH):
        with open(ACCOUNTS_FILE_PATH, 'r', encoding='utf-8') as f:
            total_accounts = len([line for line in f if line.strip() and line.strip() != 'Token'])
    await update.message.reply_text(
        f"Статистика:\nПользователей: {total_users}\nАккаунтов: {total_accounts}"
    )

# ======================= команда /addaccount_from_doc =======================

@admin_only
async def handle_document(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    if not update.message.document:
        await update.message.reply_text('Пожалуйста, отправьте файл с токенами.')
        return
    file = await update.message.document.get_file()
    file_path = 'C:/Users/Administrator/PycharmProjects/Bot/textFiles/uploaded_tokens.txt'
    await file.download_to_drive(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tokens = [line.strip() for line in f if line.strip()]
        with open(ACCOUNTS_FILE_PATH, 'a', encoding='utf-8') as f:
            for token in tokens:
                f.write(token + '\n')
        await update.message.reply_text(f'Добавлено {len(tokens)} токенов.')
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {e}')

# ======================= команда /delete_account =======================

@admin_only
async def delete_account(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Используйте: /delete_account <токен>')
        return
    token = args[0]
    remove_account_from_file(token)
    await update.message.reply_text('Аккаунт удален из файла.')

# ======================= команда /addaccount =======================

@admin_only
async def add_account_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    if not update.message.text:
        await update.message.reply_text('Пожалуйста, отправьте сообщение с токенами.')
        return
    tokens = update.message.text.split('\n')[1:]
    if not tokens:
        await update.message.reply_text('Токены не найдены.')
        return
    added = 0
    for token in tokens:
        token = token.strip()
        if token:
            with open(ACCOUNTS_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(token + '\n')
            added += 1
    await update.message.reply_text(f'Добавлено {added} токенов.')

# ======================= команда /addbalance =======================

@admin_only
async def add_balance_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text('Использование: /addbalance <user_id> <amount> <category>')
        return
    try:
        user_id = int(args[0])
        amount = int(args[1])
        category = args[2]
    except:
        await update.message.reply_text('Некорректный формат.')
        return
    username = get_username(user_id)
    new_balance = add_balance(user_id, amount)
    await update.message.reply_text(
        f'Баланс пользователя {username} (ID:{user_id}) изменен. Новый баланс: {new_balance} ₽'
    )
    save_user(username, user_id, new_balance)
    await log_balance_change(user_id, amount, category)

# ======================= команда /write =======================

@admin_only
async def write_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('Использование: /write <user_id> <text>')
        return
    try:
        user_id = int(args[0])
        text = ' '.join(args[1:])
    except:
        await update.message.reply_text('Некорректный формат.')
        return
    try:
        await context.bot.send_message(chat_id=user_id, text=text)
        await update.message.reply_text(f'Сообщение отправлено пользователю {user_id}')
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {e}')

# ======================= команда /ban =======================

@admin_only
async def ban_user(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Используйте: /ban <user_id>')
        return
    user_id = int(args[0])
    # Логика бана
    await update.message.reply_text(f'Пользователь {user_id} забанен (реализуйте логику).')

# ======================= команда /unban =======================

@admin_only
async def unban_user(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Используйте: /unban <user_id>')
        return
    user_id = int(args[0])
    # Логика разбана
    await update.message.reply_text(f'Пользователь {user_id} разбанен (реализуйте логику).')

# ======================= команда /broadcast =======================

@admin_only
async def broadcast(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    message_text = ' '.join(context.args)
    # Реализуйте рассылку
    await update.message.reply_text('Массовое сообщение (реализуйте).')

# ======================= команда /logout =======================

@admin_only
async def logout(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    await update.message.reply_text('Выход из системы (если есть авторизация).')

# ======================= команда /stats =======================

@admin_only
async def stats(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    total_users = 0
    total_accounts = 0
    if os.path.exists(USERS_FILE_PATH):
        with open(USERS_FILE_PATH, 'r', encoding='utf-8') as f:
            total_users = len([line for line in f if line.strip()])
    if os.path.exists(ACCOUNTS_FILE_PATH):
        with open(ACCOUNTS_FILE_PATH, 'r', encoding='utf-8') as f:
            total_accounts = len([line for line in f if line.strip() and line.strip() != 'Token'])
    await update.message.reply_text(
        f"Статистика:\nПользователей: {total_users}\nАккаунтов: {total_accounts}"
    )

# ======================= команда /addaccount_from_doc =======================

@admin_only
async def handle_document(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    if not update.message.document:
        await update.message.reply_text('Пожалуйста, отправьте файл с токенами.')
        return
    file = await update.message.document.get_file()
    file_path = 'C:/Users/Administrator/PycharmProjects/Bot/textFiles/uploaded_tokens.txt'
    await file.download_to_drive(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tokens = [line.strip() for line in f if line.strip()]
        with open(ACCOUNTS_FILE_PATH, 'a', encoding='utf-8') as f:
            for token in tokens:
                f.write(token + '\n')
        await update.message.reply_text(f'Добавлено {len(tokens)} токенов.')
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {e}')

# ======================= команда /delete_account =======================

@admin_only
async def delete_account(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Используйте: /delete_account <токен>')
        return
    token = args[0]
    remove_account_from_file(token)
    await update.message.reply_text('Аккаунт удален из файла.')

# ======================= команда /addaccount =======================

@admin_only
async def add_account_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    if not update.message.text:
        await update.message.reply_text('Пожалуйста, отправьте сообщение с токенами.')
        return
    tokens = update.message.text.split('\n')[1:]
    if not tokens:
        await update.message.reply_text('Токены не найдены.')
        return
    added = 0
    for token in tokens:
        token = token.strip()
        if token:
            with open(ACCOUNTS_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(token + '\n')
            added += 1
    await update.message.reply_text(f'Добавлено {added} токенов.')

# ======================= команда /addbalance =======================

@admin_only
async def add_balance_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text('Использование: /addbalance <user_id> <amount> <category>')
        return
    try:
        user_id = int(args[0])
        amount = int(args[1])
        category = args[2]
    except:
        await update.message.reply_text('Некорректный формат.')
        return
    username = get_username(user_id)
    new_balance = add_balance(user_id, amount)
    await update.message.reply_text(
        f'Баланс пользователя {username} (ID:{user_id}) изменен. Новый баланс: {new_balance} ₽'
    )
    save_user(username, user_id, new_balance)
    await log_balance_change(user_id, amount, category)

# ======================= команда /starttaxi =======================

async def start_taxi(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    global taxi_section_enabled
    taxi_section_enabled = True
    await update.message.reply_text("Раздел 'Вызвать такси' включен.")

async def stop_taxi(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    global taxi_section_enabled
    taxi_section_enabled = False
    await update.message.reply_text("Раздел 'Вызвать такси' выключен.")

async def movement_command(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS_FOR_MOVEMENT:
        await update.message.reply_text('Вам пока не доступна функция движения средств бота.\nЕсли вы считаете, что это ошибка, то напишите @DieOnTheWay')
        return
    file_path = r'C:\Users\Administrator\PycharmProjects\Bot\textFiles\transactions.txt'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename='transactions.txt')
    else:
        await update.message.reply_text("Файл с транзакциями не найден.")

def main():
    init_files()
    app = Application.builder().token(BOT_TOKEN).build()

    # основные команды
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', start))
    app.add_handler(CommandHandler('commands', commands))
    app.add_handler(CommandHandler('info', info))
    app.add_handler(CommandHandler('addaccount', add_account_command))
    app.add_handler(CommandHandler('addbalance', add_balance_command))
    app.add_handler(CommandHandler('write', write_command))
    app.add_handler(CommandHandler('user', user_command))
    app.add_handler(CommandHandler('starttaxi', start_taxi))
    app.add_handler(CommandHandler('stoptaxi', stop_taxi))
    app.add_handler(CommandHandler('movement', movement_command))
    app.add_handler(CommandHandler('taxi', taxi_command))
    # callback handlers
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(category_callback, pattern='^category_'))
    # message handlers
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    # заменяем вызов handle_taxi_request на сообщение
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.TEXT | filters.Document.ALL,
        lambda update, context: update.effective_chat.send_message(
            text='🚕 Теперь тут такси заказать не получится!\nЗаказывай такси автоматически в любое время суток — @GeniusRequestBot'
        )
    ))
    # для админа - сценарий ответа
    app.add_handler(MessageHandler(filters.User(ADMIN_ID) & filters.TEXT, handle_admin_response))
    # запуск
    app.run_polling()

# ======================= определение category_callback =======================

async def category_callback(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith('category_'):
        category = data.split('_')[1]
        await notify_user_balance_change(ADMIN_ID, 'категория', category, 'category', context.bot)
        await query.message.reply_text(f'Категория "{category}" выбрана.')

# ======================= обработчик сценария ответа админа =======================

async def handle_admin_response(update: Update, context: 'ContextTypes.DEFAULT_TYPE'):
    # пример сценария, который вы хотите: получение ссылки и суммы
    # реализуйте по вашему желанию
    if 'waiting_for_link' in context.user_data:
        user_id_target = context.user_data.pop('waiting_for_link')
        link = update.message.text
        await context.bot.send_message(chat_id=user_id_target, text=f"Вот ссылка: {link}")
        context.user_data['waiting_for_amount'] = user_id_target
        await update.message.reply_text("Введите сумму:")
        return
    if 'waiting_for_amount' in context.user_data:
        user_id_target = context.user_data.pop('waiting_for_amount')
        try:
            amount = float(update.message.text)
        except:
            await update.message.reply_text("Пожалуйста, введите число.")
            return
        multiplier = user_multipliers.get(user_id_target, 0.40)
        total_amount = amount * multiplier
        # тут тоже логика пополнения или списания по вашему усмотрению
        # по условию не меняем, просто оставляем как есть
        new_balance = add_balance(user_id_target, int(total_amount))
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"{now} - Такси: пользователю {user_id_target} зачислено {total_amount:.2f} ₽ ({multiplier*100:.0f}%)\n"
        with open(TRANSACTIONS_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_line)
        await context.bot.send_message(chat_id=user_id_target, text="Ваш заказ завершен. Баланс пополнен.")
        await update.message.reply_text("Баланс пополнен.")
        return

if __name__ == '__main__':
    main()