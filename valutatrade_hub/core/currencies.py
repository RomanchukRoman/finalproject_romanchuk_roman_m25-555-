from abc import ABC, abstractmethod
from typing import Dict
from ..core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для валют."""
    
    def __init__(self, name: str, code: str):
        """
        Инициализация валюты.
        
        Args:
            name: Человекочитаемое имя (например, "US Dollar", "Bitcoin")
            code: ISO-код или общепринятый тикер ("USD", "EUR", "BTC", "ETH")
        """
        self._validate_code(code)
        self._validate_name(name)
        
        self.name = name
        self.code = code
    
    def _validate_code(self, code: str) -> None:
        """Валидация кода валюты."""
        if not isinstance(code, str):
            raise ValueError("Код валюты должен быть строкой")
        if not 2 <= len(code) <= 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")
        if not code.isupper():
            raise ValueError("Код валюты должен быть в верхнем регистре")
        if ' ' in code:
            raise ValueError("Код валюты не может содержать пробелы")
    
    def _validate_name(self, name: str) -> None:
        """Валидация имени валюты."""
        if not isinstance(name, str):
            raise ValueError("Имя валюты должно быть строкой")
        if not name.strip():
            raise ValueError("Имя валюты не может быть пустым")
    
    @abstractmethod
    def get_display_info(self) -> str:
        """
        Строковое представление для UI/логов.
        
        Returns:
            Строка с информацией о валюте
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code='{self.code}', name='{self.name}')"


class FiatCurrency(Currency):
    """Класс для фиатных валют."""
    
    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты.
        
        Args:
            name: Человекочитаемое имя (например, "US Dollar")
            code: ISO-код ("USD", "EUR")
            issuing_country: Страна/зона эмиссии (например, "United States", "Eurozone")
        """
        super().__init__(name, code)
        self.issuing_country = issuing_country
    
    def get_display_info(self) -> str:
        """
        Строковое представление фиатной валюты.
        
        Returns:
            Строка в формате: "[FIAT] USD — US Dollar (Issuing: United States)"
        """
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"
    
    def __repr__(self) -> str:
        return f"FiatCurrency(code='{self.code}', name='{self.name}', issuing_country='{self.issuing_country}')"


class CryptoCurrency(Currency):
    """Класс для криптовалют."""
    
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        """
        Инициализация криптовалюты.
        
        Args:
            name: Человекочитаемое имя (например, "Bitcoin")
            code: Тикер ("BTC", "ETH")
            algorithm: Алгоритм (например, "SHA-256", "Ethash")
            market_cap: Рыночная капитализация (по умолчанию 0.0)
        """
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
    
    def get_display_info(self) -> str:
        """
        Строковое представление криптовалюты.
        
        Returns:
            Строка в формате: "[CRYPTO] BTC — Bitcoin (Algo: SHA-256, MCAP: 1.12e12)"
        """
        mcap_display = f"{self.market_cap:.2e}" if self.market_cap > 1e9 else f"{self.market_cap:,.2f}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_display})"
    
    def __repr__(self) -> str:
        return f"CryptoCurrency(code='{self.code}', name='{self.name}', algorithm='{self.algorithm}', market_cap={self.market_cap})"


# Реестр валют
_currency_registry: Dict[str, Currency] = {}


def _initialize_currencies():
    """Инициализация реестра валют."""
    # Фиатные валюты
    fiats = [
        FiatCurrency("US Dollar", "USD", "United States"),
        FiatCurrency("Euro", "EUR", "Eurozone"),
        FiatCurrency("Russian Ruble", "RUB", "Russia"),
        FiatCurrency("British Pound", "GBP", "United Kingdom"),
        FiatCurrency("Japanese Yen", "JPY", "Japan"),
    ]
    
    # Криптовалюты
    cryptos = [
        CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        CryptoCurrency("Ethereum", "ETH", "Ethash", 3.5e11),
        CryptoCurrency("Litecoin", "LTC", "Scrypt", 5.8e9),
        CryptoCurrency("Cardano", "ADA", "Ouroboros", 1.2e10),
    ]
    
    # Добавляем все валюты в реестр
    for currency in fiats + cryptos:
        _currency_registry[currency.code] = currency


def get_currency(code: str) -> Currency:
    """
    Фабричный метод для получения валюты по коду.
    
    Args:
        code: Код валюты
        
    Returns:
        Объект Currency
        
    Raises:
        CurrencyNotFoundError: Если валюта с указанным кодом не найдена
    """
    code = code.upper().strip()
    
    if not _currency_registry:
        _initialize_currencies()
    
    if code not in _currency_registry:
        raise CurrencyNotFoundError(code)
    
    return _currency_registry[code]


def get_all_currencies() -> Dict[str, Currency]:
    """
    Получить все доступные валюты.
    
    Returns:
        Словарь всех валют (код -> объект Currency)
    """
    if not _currency_registry:
        _initialize_currencies()
    
    return _currency_registry.copy()


def get_currency_types_count() -> Dict[str, int]:
    """
    Получить количество валют по типам.
    
    Returns:
        Словарь с количеством валют каждого типа
    """
    if not _currency_registry:
        _initialize_currencies()
    
    counts = {"fiat": 0, "crypto": 0}
    for currency in _currency_registry.values():
        if isinstance(currency, FiatCurrency):
            counts["fiat"] += 1
        elif isinstance(currency, CryptoCurrency):
            counts["crypto"] += 1
    
    return counts


# Инициализируем реестр при импорте модуля
_initialize_currencies()