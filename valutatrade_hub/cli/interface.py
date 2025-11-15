import json
import sys
import shlex
from pathlib import Path
from typing import Optional, List, Dict, Any

# Импорты из нашей системы
from ..core.models import User, Wallet, Portfolio
from ..core.exceptions import InsufficientFundsError, ApiRequestError
from ..core.currencies import get_currency, get_all_currencies, CurrencyNotFoundError


class CLIState:
    """Состояние CLI для хранения текущего пользователя."""
    
    def __init__(self):
        self.current_user: Optional[User] = None
        self.data_dir = Path("data")


# Функции для работы с данными (оставляем без изменений)
def load_users(data_dir: Path) -> list:
    """Загрузка пользователей из JSON."""
    users_file = data_dir / "users.json"
    if users_file.exists():
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_users(data_dir: Path, users: list) -> None:
    """Сохранение пользователей в JSON."""
    users_file = data_dir / "users.json"
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_portfolios(data_dir: Path) -> list:
    """Загрузка портфелей из JSON."""
    portfolios_file = data_dir / "portfolios.json"
    if portfolios_file.exists():
        with open(portfolios_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_portfolios(data_dir: Path, portfolios: list) -> None:
    """Сохранение портфелей в JSON."""
    portfolios_file = data_dir / "portfolios.json"
    with open(portfolios_file, 'w', encoding='utf-8') as f:
        json.dump(portfolios, f, ensure_ascii=False, indent=2)


def load_rates(data_dir: Path) -> dict:
    """Загрузка курсов из JSON."""
    rates_file = data_dir / "rates.json"
    
    if rates_file.exists():
        try:
            with open(rates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ApiRequestError(f"Ошибка загрузки курсов: {e}")
    else:
        raise ApiRequestError("Файл с курсами не найден")


def get_next_user_id(users: list) -> int:
    """Получение следующего ID пользователя."""
    if not users:
        return 1
    return max(user['user_id'] for user in users) + 1


def find_user_by_username(users: list, username: str) -> Optional[dict]:
    """Поиск пользователя по имени."""
    for user in users:
        if user['username'] == username:
            return user
    return None


def find_portfolio_by_user_id(portfolios: list, user_id: int) -> Optional[dict]:
    """Поиск портфеля по ID пользователя."""
    for portfolio in portfolios:
        if portfolio['user_id'] == user_id:
            return portfolio
    return None


def parse_args(args: List[str]) -> Dict[str, Any]:
    """Парсинг аргументов командной строки с помощью shlex."""
    parsed = {'command': args[0] if args else None}
    
    i = 1
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            key = arg[2:]
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                parsed[key] = args[i + 1]
                i += 2
            else:
                parsed[key] = True
                i += 1
        else:
            i += 1
    
    return parsed


def print_help():
    """Вывод справки по командам."""
    print("ValutaTrade Hub - Платформа для торговли валютами")
    print("\nДоступные команды:")
    print("  register --username <name> --password <pass>    Регистрация нового пользователя")
    print("  login --username <name> --password <pass>       Вход в систему")
    print("  show-portfolio [--base <currency>]              Показать портфель пользователя")
    print("  buy --currency <code> --amount <number>         Купить валюту")
    print("  sell --currency <code> --amount <number>        Продать валюту")
    print("  get-rate --from <code> --to <code>              Получить текущий курс валюты")
    print("  help                                            Показать эту справку")
    print("  exit                                            Выйти из приложения")
    print("\nПримеры:")
    print("  register --username alice --password 1234")
    print("  login --username alice --password 1234")
    print("  buy --currency BTC --amount 0.05")


# Команды CLI
def register_command(args: Dict[str, Any], state: CLIState):
    """Регистрация нового пользователя."""
    try:
        username = args.get('username')
        password = args.get('password')
        
        if not username or not password:
            print("Ошибка: необходимо указать --username и --password")
            return
        
        # Загрузка существующих пользователей
        users = load_users(state.data_dir)
        
        # Проверка уникальности username
        if find_user_by_username(users, username):
            print(f"Имя пользователя '{username}' уже занято")
            return
        
        # Проверка длины пароля
        if len(password) < 4:
            print("Пароль должен быть не короче 4 символов")
            return
        
        # Создание нового пользователя
        user_id = get_next_user_id(users)
        user = User(user_id, username, password)
        
        # Сохранение пользователя
        users.append(user.to_dict())
        save_users(state.data_dir, users)
        
        # Создание пустого портфеля
        portfolios = load_portfolios(state.data_dir)
        portfolio = Portfolio(user_id)
        portfolios.append(portfolio.to_dict())
        save_portfolios(state.data_dir, portfolios)
        
        print(f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****")
        
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")


def login_command(args: Dict[str, Any], state: CLIState):
    """Вход в систему."""
    try:
        username = args.get('username')
        password = args.get('password')
        
        if not username or not password:
            print("Ошибка: необходимо указать --username и --password")
            return
        
        # Загрузка пользователей
        users = load_users(state.data_dir)
        
        # Поиск пользователя
        user_data = find_user_by_username(users, username)
        if not user_data:
            print(f"Пользователь '{username}' не найден")
            return
        
        # Создание объекта пользователя и проверка пароля
        user = User.from_dict(user_data)
        if not user.verify_password(password):
            print("Неверный пароль")
            return
        
        # Установка текущего пользователя
        state.current_user = user
        print(f"Вы вошли как '{username}'")
        
    except Exception as e:
        print(f"Ошибка при входе: {e}")


def show_portfolio_command(args: Dict[str, Any], state: CLIState):
    """Показать портфель пользователя."""
    try:
        base = args.get('base', 'USD')
        
        # Проверка авторизации
        if not state.current_user:
            print("Сначала выполните login")
            return
        
        # Загрузка портфелей
        portfolios = load_portfolios(state.data_dir)
        portfolio_data = find_portfolio_by_user_id(portfolios, state.current_user.user_id)
        
        if not portfolio_data:
            print("Портфель не найден")
            return
        
        portfolio = Portfolio.from_dict(portfolio_data)
        
        # Загрузка курсов
        try:
            rates = load_rates(state.data_dir)
        except ApiRequestError as e:
            print(f"Внимание: {e}")
            print("Используются базовые курсы для расчета")
            rates = {
                'EUR_USD': {'rate': 1.08},
                'BTC_USD': {'rate': 50000.0},
                'ETH_USD': {'rate': 3000.0}
            }
        
        # Получение информации о портфеле
        if not portfolio.wallets:
            print("Портфель пуст")
            return
        
        print(f"Портфель пользователя '{state.current_user.username}' (база: {base}):")
        
        total_value = 0
        exchange_rates = {}
        
        # Преобразование курсов в удобный формат
        for key, value in rates.items():
            if key != 'source' and key != 'last_refresh':
                exchange_rates[key] = value['rate']
        
        for currency_code, wallet in portfolio.wallets.items():
            balance = wallet.balance
            
            if currency_code == base:
                value_in_base = balance
                print(f"- {currency_code}: {balance:.2f} → {value_in_base:.2f} {base}")
                total_value += value_in_base
            else:
                # Поиск курса
                rate_key = f"{currency_code}_{base}"
                if rate_key in exchange_rates:
                    rate = exchange_rates[rate_key]
                    value_in_base = balance * rate
                    print(f"- {currency_code}: {balance:.4f} → {value_in_base:.2f} {base}")
                    total_value += value_in_base
                else:
                    print(f"- {currency_code}: {balance:.4f} → курс не найден")
        
        print("-" * 40)
        print(f"ИТОГО: {total_value:,.2f} {base}")
        
    except Exception as e:
        print(f"Ошибка при показе портфеля: {e}")


def buy_command(args: Dict[str, Any], state: CLIState):
    """Купить валюту."""
    try:
        currency = args.get('currency')
        amount_str = args.get('amount')
        
        if not currency or not amount_str:
            print("Ошибка: необходимо указать --currency и --amount")
            return
        
        # Валидация валюты через новую систему
        currency_obj = get_currency(currency)
        
        try:
            amount = float(amount_str)
        except ValueError:
            print("Ошибка: amount должен быть числом")
            return
        
        # Проверка авторизации
        if not state.current_user:
            print("Сначала выполните login")
            return
        
        # Валидация входа
        currency = currency.upper().strip()
        if amount <= 0:
            print("'amount' должен быть положительным числом")
            return
        
        # Загрузка данных
        portfolios = load_portfolios(state.data_dir)
        portfolio_data = find_portfolio_by_user_id(portfolios, state.current_user.user_id)
        
        if not portfolio_data:
            print("Портфель не найден")
            return
        
        portfolio = Portfolio.from_dict(portfolio_data)
        
        # Получение или создание кошелька
        wallet = portfolio.get_or_create_wallet(currency)
        
        # Загрузка курсов для оценочной стоимости
        rates = load_rates(state.data_dir)
        exchange_rates = {}
        for key, value in rates.items():
            if key != 'source' and key != 'last_refresh':
                exchange_rates[key] = value['rate']
        
        # Расчет оценочной стоимости
        rate_key = f"{currency}_USD"
        rate = exchange_rates.get(rate_key, 0)
        estimated_cost = amount * rate if rate > 0 else 0
        
        # Пополнение кошелька
        old_balance = wallet.balance
        wallet.deposit(amount)
        
        # Сохранение изменений
        portfolio_data = portfolio.to_dict()
        for i, p in enumerate(portfolios):
            if p['user_id'] == state.current_user.user_id:
                portfolios[i] = portfolio_data
                break
        
        save_portfolios(state.data_dir, portfolios)
        
        # Вывод результата
        if rate > 0:
            print(f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
            print(f"Оценочная стоимость покупки: {estimated_cost:,.2f} USD")
        else:
            print(f"Покупка выполнена: {amount:.4f} {currency}")
        
        print(f"Изменения в портфеле:")
        print(f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}")
        
    except CurrencyNotFoundError as e:
        print(str(e))
        print("Проверьте правильность кода валюты")
        
    except ValueError as e:
        print(f"Ошибка валидации: {e}")
    except Exception as e:
        print(f"Ошибка при покупке: {e}")


def sell_command(args: Dict[str, Any], state: CLIState):
    """Продать валюту."""
    try:
        currency = args.get('currency')
        amount_str = args.get('amount')
        
        if not currency or not amount_str:
            print("Ошибка: необходимо указать --currency и --amount")
            return
        
        # Валидация валюты через новую систему
        currency_obj = get_currency(currency)
        
        try:
            amount = float(amount_str)
        except ValueError:
            print("Ошибка: amount должен быть числом")
            return
        
        # Проверка авторизации
        if not state.current_user:
            print("Сначала выполните login")
            return
        
        # Валидация входа
        currency = currency.upper().strip()
        if amount <= 0:
            print("'amount' должен быть положительным числом")
            return
        
        # Загрузка данных
        portfolios = load_portfolios(state.data_dir)
        portfolio_data = find_portfolio_by_user_id(portfolios, state.current_user.user_id)
        
        if not portfolio_data:
            print("Портфель не найден")
            return
        
        portfolio = Portfolio.from_dict(portfolio_data)
        
        # Получение кошелька
        wallet = portfolio.get_wallet(currency)
        if not wallet:
            print(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке.")
            return
        
        # Загрузка курсов для оценочной выручки
        rates = load_rates(state.data_dir)
        exchange_rates = {}
        for key, value in rates.items():
            if key != 'source' and key != 'last_refresh':
                exchange_rates[key] = value['rate']
        
        # Расчет оценочной выручки
        rate_key = f"{currency}_USD"
        rate = exchange_rates.get(rate_key, 0)
        estimated_revenue = amount * rate if rate > 0 else 0
        
        # Снятие средств
        old_balance = wallet.balance
        
        try:
            wallet.withdraw(amount)
        except InsufficientFundsError as e:
            print(str(e))
            return
        
        # Сохранение изменений
        portfolio_data = portfolio.to_dict()
        for i, p in enumerate(portfolios):
            if p['user_id'] == state.current_user.user_id:
                portfolios[i] = portfolio_data
                break
        
        save_portfolios(state.data_dir, portfolios)
        
        # Вывод результата
        if rate > 0:
            print(f"Продажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
            print(f"Оценочная выручка: {estimated_revenue:,.2f} USD")
        else:
            print(f"Продажа выполнена: {amount:.4f} {currency}")
        
        print(f"Изменения в портфеле:")
        print(f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}")
        
    except CurrencyNotFoundError as e:
        print(str(e))
        print("Проверьте правильность кода валюты")
        
    except ValueError as e:
        print(f"Ошибка валидации: {e}")
    except Exception as e:
        print(f"Ошибка при продаже: {e}")


def get_rate_command(args: Dict[str, Any], state: CLIState):
    """Получить текущий курс валюты."""
    try:
        from_currency = args.get('from')
        to_currency = args.get('to')
        
        if not from_currency or not to_currency:
            print("Ошибка: необходимо указать --from и --to")
            return
        
        # Валидация кодов валют через новую систему
        from_currency_obj = get_currency(from_currency)
        to_currency_obj = get_currency(to_currency)
        
        # Валидация кодов валют
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()
        
        if not from_currency or not to_currency:
            print("Коды валют не могут быть пустыми")
            return
        
        # Загрузка курсов
        rates = load_rates(state.data_dir)
        
        # Поиск прямого курса
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in rates and rate_key not in ['source', 'last_refresh']:
            rate_data = rates[rate_key]
            rate = rate_data['rate']
            updated_at = rate_data['updated_at']
            
            print(f"Курс {from_currency}→{to_currency}: {rate:.6f} (обновлено: {updated_at})")
            
            # Обратный курс
            if rate != 0:
                reverse_rate = 1 / rate
                print(f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.6f}")
            return
        
        # Поиск обратного курса
        reverse_rate_key = f"{to_currency}_{from_currency}"
        if reverse_rate_key in rates and reverse_rate_key not in ['source', 'last_refresh']:
            rate_data = rates[reverse_rate_key]
            reverse_rate = rate_data['rate']
            if reverse_rate != 0:
                rate = 1 / reverse_rate
                updated_at = rate_data['updated_at']
                
                print(f"Курс {from_currency}→{to_currency}: {rate:.6f} (расчетный, обновлено: {updated_at})")
                print(f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.6f}")
            return
        
        # Поиск через USD если прямого курса нет
        if from_currency != 'USD' and to_currency != 'USD':
            usd_to_target_key = f"USD_{to_currency}"
            source_to_usd_key = f"{from_currency}_USD"
            
            if usd_to_target_key in rates and source_to_usd_key in rates:
                usd_to_target = rates[usd_to_target_key]['rate']
                source_to_usd = rates[source_to_usd_key]['rate']
                
                if usd_to_target != 0 and source_to_usd != 0:
                    calculated_rate = source_to_usd * usd_to_target
                    print(f"Курс {from_currency}→{to_currency}: {calculated_rate:.6f} (расчетный)")
                    
                    # Обратный курс
                    reverse_rate = 1 / calculated_rate if calculated_rate != 0 else 0
                    print(f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.6f}")
                    return
        
        print(f"Курс {from_currency}→{to_currency} недоступен. Повторите попытку позже.")
        print(f"Доступные курсы: {[k for k in rates.keys() if k not in ['source', 'last_refresh']]}")
        
    except CurrencyNotFoundError as e:
        print(str(e))
        print("Используйте 'help get-rate' или проверьте список доступных валют")
        available_currencies = list(get_all_currencies().keys())
        print(f"Доступные валюты: {', '.join(available_currencies)}")
        
    except Exception as e:
        print(f"Ошибка при получении курса: {e}")


def interactive_mode():
    """Интерактивный режим с циклом while."""
    state = CLIState()
    
    print("Добро пожаловать в ValutaTrade Hub!")
    print("Введите 'help' для списка команд, 'exit' для выхода")
    
    while True:
        try:
            # Чтение команды от пользователя
            user_input = input("\nvtrade> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Выход из ValutaTrade Hub. До свидания!")
                break
            
            # Парсинг введенной команды с помощью shlex
            try:
                args_list = shlex.split(user_input)
            except ValueError as e:
                print(f"Ошибка парсинга команды: {e}")
                continue
                
            args = parse_args(args_list)
            command = args.get('command')
            
            # Выполнение команды
            if command == 'register':
                register_command(args, state)
            elif command == 'login':
                login_command(args, state)
            elif command == 'show-portfolio':
                show_portfolio_command(args, state)
            elif command == 'buy':
                buy_command(args, state)
            elif command == 'sell':
                sell_command(args, state)
            elif command == 'get-rate':
                get_rate_command(args, state)
            elif command in ['help', '--help', '-h']:
                print_help()
            else:
                print(f"Неизвестная команда: {command}")
                print("Введите 'help' для списка команд")
                
        except KeyboardInterrupt:
            print("\n\nВыход из ValutaTrade Hub. До свидания!")
            break
        except EOFError:
            print("\n\nВыход из ValutaTrade Hub. До свидания!")
            break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")


def main():
    """Основная функция CLI."""
    # Если нет аргументов - запускаем интерактивный режим
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        # Старый режим с аргументами командной строки
        state = CLIState()
        
        # Парсинг аргументов с помощью shlex (для корректной обработки кавычек)
        command_line = ' '.join(sys.argv[1:])
        try:
            args_list = shlex.split(command_line)
        except ValueError as e:
            print(f"Ошибка парсинга команд: {e}")
            return
        
        args = parse_args(args_list)
        command = args.get('command')
        
        # Выполнение команды
        if command == 'register':
            register_command(args, state)
        elif command == 'login':
            login_command(args, state)
        elif command == 'show-portfolio':
            show_portfolio_command(args, state)
        elif command == 'buy':
            buy_command(args, state)
        elif command == 'sell':
            sell_command(args, state)
        elif command == 'get-rate':
            get_rate_command(args, state)
        elif command in ['help', '--help', '-h']:
            print_help()
        else:
            print(f"Неизвестная команда: {command}")
            print_help()


if __name__ == '__main__':
    main()