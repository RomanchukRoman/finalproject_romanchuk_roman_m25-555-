# ValutaTrade Hub

Платформа для отслеживания и симуляции торговли валютами.

## Демо

[![asciicast](https://asciinema.org/a/LPCGdXajDALrcjWn1TE462tXS.svg)](https://asciinema.org/a/LPCGdXajDALrcjWn1TE462tXS)

## Установка и запуск

```bash
git clone <repository-url>
cd finalproject_romanchuk_roman_m25-555
poetry install
poetry run project
```

## Доступные команды

```bash
  register --username <name> --password <pass>    Регистрация нового пользователя
  login --username <name> --password <pass>       Вход в систему
  show-portfolio [--base <currency>]              Показать портфель пользователя
  buy --currency <code> --amount <number>         Купить валюту
  sell --currency <code> --amount <number>        Продать валюту
  get-rate --from <code> --to <code>              Получить текущий курс валюты
  help                                            Показать эту справку
  exit                                            Выйти из приложения

Примеры:
  register --username alice --password 1234
  login --username alice --password 1234
  buy --currency BTC --amount 0.05
  show-portfolio --base USD
  get-rate --from USD --to BTC
  ```

## Структура проекта

```bash
  finalproject_romanchuk_roman_m25-555/
├── data/                   # Данные (JSON файлы)
│   ├── users.json          # Пользователи
│   ├── portfolios.json     # Портфели
│   └── rates.json          # Курсы валют
├── valutatrade_hub/
│   ├── core/               # Бизнес-логика
│   │   ├── models.py       # User, Wallet, Portfolio
│   │   ├── currencies.py   # Иерархия валют
│   │   └── exceptions.py   # Обработка ошибок
│   ├── cli/
│   │   └── interface.py    # Командный интерфейс
│   └── decorators.py       # Логирование операций
├── main.py                 # Точка входа
└── pyproject.toml          # Конфигурация Poetry
```

## Поддерживаемые валюты
Фиатные: USD, EUR, RUB, GBP, JPY
Криптовалюты: BTC, ETH, LTC, ADA

## Автор
Romanchuk Roman
M25-555
r.romanchuk@ya.ru