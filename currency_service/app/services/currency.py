import redis
import httpx
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.config import settings
from app.schemas.currency import CurrencyInfo, ExchangeRate, ConversionResponse, CurrencyRatesResponse

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.http_client = httpx.AsyncClient(timeout=settings.http_timeout)
        self.cache_key_prefix = "currency:"
        
        # Top 10 most popular currencies for UI
        self.popular_currencies = {
            "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "UAH", "RUB"
        }
        
        # Supported currencies with metadata
        self.supported_currencies = {
            "USD": {"name": "US Dollar", "symbol": "$", "flag": "🇺🇸"},
            "EUR": {"name": "Euro", "symbol": "€", "flag": "🇪🇺"},
            "UAH": {"name": "Ukrainian Hryvnia", "symbol": "₴", "flag": "🇺🇦"},
            "GBP": {"name": "British Pound", "symbol": "£", "flag": "🇬🇧"},
            "JPY": {"name": "Japanese Yen", "symbol": "¥", "flag": "🇯🇵"},
            "CAD": {"name": "Canadian Dollar", "symbol": "C$", "flag": "🇨🇦"},
            "AUD": {"name": "Australian Dollar", "symbol": "A$", "flag": "🇦🇺"},
            "CHF": {"name": "Swiss Franc", "symbol": "CHF", "flag": "🇨🇭"},
            "CNY": {"name": "Chinese Yuan", "symbol": "¥", "flag": "🇨🇳"},
            "RUB": {"name": "Russian Ruble", "symbol": "₽", "flag": "🇷🇺"},
            "INR": {"name": "Indian Rupee", "symbol": "₹", "flag": "🇮🇳"},
            "BRL": {"name": "Brazilian Real", "symbol": "R$", "flag": "🇧🇷"},
            "MXN": {"name": "Mexican Peso", "symbol": "$", "flag": "🇲🇽"},
            "KRW": {"name": "South Korean Won", "symbol": "₩", "flag": "🇰🇷"},
            "SGD": {"name": "Singapore Dollar", "symbol": "S$", "flag": "🇸🇬"},
            "NZD": {"name": "New Zealand Dollar", "symbol": "NZ$", "flag": "🇳🇿"},
            "NOK": {"name": "Norwegian Krone", "symbol": "kr", "flag": "🇳🇴"},
            "SEK": {"name": "Swedish Krona", "symbol": "kr", "flag": "🇸🇪"},
            "DKK": {"name": "Danish Krone", "symbol": "kr", "flag": "🇩🇰"},
            "PLN": {"name": "Polish Zloty", "symbol": "zł", "flag": "🇵🇱"},
            "CZK": {"name": "Czech Koruna", "symbol": "Kč", "flag": "🇨🇿"},
            "HUF": {"name": "Hungarian Forint", "symbol": "Ft", "flag": "🇭🇺"},
            "TRY": {"name": "Turkish Lira", "symbol": "₺", "flag": "🇹🇷"},
            "ZAR": {"name": "South African Rand", "symbol": "R", "flag": "🇿🇦"},
            "AED": {"name": "UAE Dirham", "symbol": "د.إ", "flag": "🇦🇪"},
            "SAR": {"name": "Saudi Riyal", "symbol": "ر.س", "flag": "🇸🇦"},
            "THB": {"name": "Thai Baht", "symbol": "฿", "flag": "🇹🇭"},
            "MYR": {"name": "Malaysian Ringgit", "symbol": "RM", "flag": "🇲🇾"},
            "IDR": {"name": "Indonesian Rupiah", "symbol": "Rp", "flag": "🇮🇩"},
            "PHP": {"name": "Philippine Peso", "symbol": "₱", "flag": "🇵🇭"},
        }
    
    async def get_supported_currencies(self) -> List[CurrencyInfo]:
        """Get list of top 10 supported currencies"""
        try:
            # Try to get from cache first
            cache_key = f"{self.cache_key_prefix}currencies_top10"
            cached_currencies = await self._get_cached_currencies(cache_key)
            if cached_currencies:
                return cached_currencies
            
            # Fetch from API
            currencies = await self._fetch_currencies_from_api()
            if currencies:
                # Cache the currencies
                await self._cache_currencies(currencies, cache_key)
                return currencies
            
            # Fallback to hardcoded list
            logger.warning("Using fallback currency list")
            return self._get_fallback_currencies()
            
        except Exception as e:
            logger.error(f"Error getting supported currencies: {e}")
            return self._get_fallback_currencies()
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get exchange rate between two currencies.
        Returns None if rate cannot be determined.
        """
        if from_currency == to_currency:
            return 1.0
            
        try:
            # Try to get from cache first
            cached_rate = await self._get_cached_rate(from_currency, to_currency)
            if cached_rate is not None:
                logger.info(f"Using cached rate {from_currency}->{to_currency}: {cached_rate}")
                return cached_rate
            
            # Get fresh rates from API
            rates = await self._fetch_exchange_rates(from_currency)
            if rates is None:
                # Try fallback to last known rate
                fallback_rate = await self._get_fallback_rate(from_currency, to_currency)
                if fallback_rate is not None:
                    logger.warning(f"Using fallback rate {from_currency}->{to_currency}: {fallback_rate}")
                    return fallback_rate
                return None
            
            # Calculate rate
            rate = self._calculate_rate(rates, from_currency, to_currency)
            if rate is None:
                return None
                
            # Cache the rate
            await self._cache_rate(from_currency, to_currency, rate)
            await self._cache_fallback_rate(from_currency, to_currency, rate)
            
            logger.info(f"Fetched fresh rate {from_currency}->{to_currency}: {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error getting exchange rate {from_currency}->{to_currency}: {e}")
            # Try fallback
            fallback_rate = await self._get_fallback_rate(from_currency, to_currency)
            if fallback_rate is not None:
                logger.warning(f"Using fallback rate after error {from_currency}->{to_currency}: {fallback_rate}")
                return fallback_rate
            return None
    
    async def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> Optional[ConversionResponse]:
        """
        Convert amount from one currency to another.
        Returns None if conversion cannot be performed.
        """
        if from_currency == to_currency:
            return ConversionResponse(
                amount=amount,
                converted_amount=amount,
                from_currency=from_currency,
                to_currency=to_currency,
                rate=1.0,
                timestamp=datetime.utcnow()
            )
            
        rate = await self.get_exchange_rate(from_currency, to_currency)
        if rate is None:
            return None
            
        converted_amount = round(amount * rate, 2)
        
        return ConversionResponse(
            amount=amount,
            converted_amount=converted_amount,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            timestamp=datetime.utcnow()
        )
    
    async def get_currency_rates(self, base_currency: str = "USD") -> Optional[CurrencyRatesResponse]:
        """Get all exchange rates for a base currency"""
        try:
            rates = await self._fetch_exchange_rates(base_currency)
            if rates is None:
                return None
                
            return CurrencyRatesResponse(
                base_currency=base_currency,
                rates=rates,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error getting currency rates for {base_currency}: {e}")
            return None
    
    async def _fetch_exchange_rates(self, base_currency: str) -> Optional[Dict[str, float]]:
        """Fetch exchange rates from API"""
        try:
            url = f"{settings.currency_api_url}/{base_currency}"
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get("rates", {})
            
            # Cache the entire rates object
            cache_key = f"{self.cache_key_prefix}rates:{base_currency}"
            self.redis_client.setex(
                cache_key, 
                settings.currency_cache_ttl, 
                json.dumps(rates)
            )
            
            logger.info(f"Fetched and cached rates for {base_currency}")
            return rates
            
        except Exception as e:
            logger.error(f"Error fetching exchange rates for {base_currency}: {e}")
            return None
    
    async def _get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get rate from cache"""
        try:
            cache_key = f"{self.cache_key_prefix}rates:{from_currency}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                rates = json.loads(cached_data)
                return self._calculate_rate(rates, from_currency, to_currency)
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached rate: {e}")
            return None
    
    def _calculate_rate(self, rates: Dict[str, float], from_currency: str, to_currency: str) -> Optional[float]:
        """Calculate exchange rate from rates dictionary"""
        try:
            if from_currency == to_currency:
                return 1.0
                
            # If converting from base currency (USD)
            if from_currency == "USD":
                return rates.get(to_currency)
            
            # If converting to base currency (USD)
            if to_currency == "USD":
                from_rate = rates.get(from_currency)
                if from_rate and from_rate > 0:
                    return 1.0 / from_rate
                return None
            
            # Converting between two non-USD currencies via USD
            from_rate = rates.get(from_currency)
            to_rate = rates.get(to_currency)
            
            if from_rate and to_rate and from_rate > 0:
                return to_rate / from_rate
                
            return None
            
        except Exception as e:
            logger.error(f"Error calculating rate: {e}")
            return None
    
    async def _cache_rate(self, from_currency: str, to_currency: str, rate: float):
        """Cache a specific rate"""
        try:
            cache_key = f"{self.cache_key_prefix}rate:{from_currency}:{to_currency}"
            self.redis_client.setex(cache_key, settings.currency_cache_ttl, str(rate))
        except Exception as e:
            logger.error(f"Error caching rate: {e}")
    
    async def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get fallback rate from cache (last known rate)"""
        try:
            cache_key = f"{self.cache_key_prefix}fallback:{from_currency}:{to_currency}"
            cached_rate = self.redis_client.get(cache_key)
            if cached_rate:
                return float(cached_rate)
            return None
        except Exception as e:
            logger.error(f"Error getting fallback rate: {e}")
            return None
    
    async def _cache_fallback_rate(self, from_currency: str, to_currency: str, rate: float):
        """Cache fallback rate (longer TTL)"""
        try:
            cache_key = f"{self.cache_key_prefix}fallback:{from_currency}:{to_currency}"
            # Cache fallback for 24 hours
            self.redis_client.setex(cache_key, settings.fallback_cache_ttl, str(rate))
        except Exception as e:
            logger.error(f"Error caching fallback rate: {e}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check service health"""
        health = {
            "redis_connected": False,
            "api_accessible": False
        }
        
        # Check Redis connection
        try:
            self.redis_client.ping()
            health["redis_connected"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        # Check external API
        try:
            response = await self.http_client.get(settings.currency_api_url, timeout=5.0)
            health["api_accessible"] = response.status_code == 200
        except Exception as e:
            logger.error(f"External API health check failed: {e}")
        
        return health
    
    async def _get_cached_currencies(self, cache_key: str) -> Optional[List[CurrencyInfo]]:
        """Get currencies from cache"""
        try:
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                currencies_data = json.loads(cached_data)
                return [CurrencyInfo(**currency) for currency in currencies_data]
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached currencies: {e}")
            return None
    
    async def _cache_currencies(self, currencies: List[CurrencyInfo], cache_key: str):
        """Cache currencies list"""
        try:
            currencies_data = [currency.model_dump() for currency in currencies]
            # Cache for 24 hours
            self.redis_client.setex(cache_key, 86400, json.dumps(currencies_data))
        except Exception as e:
            logger.error(f"Error caching currencies: {e}")
    
    async def _fetch_currencies_from_api(self) -> Optional[List[CurrencyInfo]]:
        """Fetch top 10 currencies from external API"""
        try:
            # Get rates to extract currency codes
            rates = await self._fetch_exchange_rates("USD")
            if not rates:
                return None
            
            # Create currency info for top 10 currencies only
            currencies = []
            for code in self.popular_currencies:
                if code in rates:  # Only include if available in API
                    if code in self.supported_currencies:
                        # Use our metadata for known currencies
                        info = self.supported_currencies[code]
                        currencies.append(CurrencyInfo(
                            code=code,
                            name=info["name"],
                            symbol=info["symbol"],
                            flag=info["flag"]
                        ))
                    else:
                        # Generate basic info for unknown currencies
                        currencies.append(CurrencyInfo(
                            code=code,
                            name=f"{code} Currency",
                            symbol=code,
                            flag="🌍"
                        ))
            
            logger.info(f"Fetched {len(currencies)} top currencies from API")
            return currencies
            
        except Exception as e:
            logger.error(f"Error fetching currencies from API: {e}")
            return None
    
    def _get_fallback_currencies(self) -> List[CurrencyInfo]:
        """Get fallback currency list (top 10)"""
        currencies = []
        for code in self.popular_currencies:
            if code in self.supported_currencies:
                info = self.supported_currencies[code]
                currencies.append(CurrencyInfo(
                    code=code,
                    name=info["name"],
                    symbol=info["symbol"],
                    flag=info["flag"]
                ))
        return currencies

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
