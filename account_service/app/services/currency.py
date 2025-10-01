import redis
import httpx
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.cache_key_prefix = "currency_rates:"
        
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
    
    async def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert amount from one currency to another.
        Returns None if conversion cannot be performed.
        """
        if from_currency == to_currency:
            return amount
            
        rate = await self.get_exchange_rate(from_currency, to_currency)
        if rate is None:
            return None
            
        return round(amount * rate, 2)
    
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
            self.redis_client.setex(cache_key, 86400, str(rate))
        except Exception as e:
            logger.error(f"Error caching fallback rate: {e}")
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
