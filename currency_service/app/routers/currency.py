from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.services.currency import CurrencyService
from app.schemas.currency import (
    CurrencyInfo, 
    ConversionRequest, 
    ConversionResponse, 
    CurrencyRatesResponse,
    SupportedCurrenciesResponse,
    HealthResponse
)

router = APIRouter(prefix="/api/v1", tags=["currency"])

def get_currency_service() -> CurrencyService:
    """Get currency service instance"""
    return CurrencyService()

@router.get("/currencies", response_model=SupportedCurrenciesResponse)
async def get_supported_currencies(
    service: CurrencyService = Depends(get_currency_service)
) -> SupportedCurrenciesResponse:
    """Get list of top 10 supported currencies"""
    try:
        currencies = await service.get_supported_currencies()
        return SupportedCurrenciesResponse(
            currencies=currencies,
            total_count=len(currencies)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch supported currencies: {str(e)}"
        )

@router.get("/rates", response_model=CurrencyRatesResponse)
async def get_currency_rates(
    base_currency: str = "USD",
    service: CurrencyService = Depends(get_currency_service)
) -> CurrencyRatesResponse:
    """Get current exchange rates for a base currency"""
    try:
        rates_response = await service.get_currency_rates(base_currency)
        if rates_response is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch currency rates at this time"
            )
        return rates_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch currency rates: {str(e)}"
        )

@router.post("/convert", response_model=ConversionResponse)
async def convert_currency(
    request: ConversionRequest,
    service: CurrencyService = Depends(get_currency_service)
) -> ConversionResponse:
    """Convert amount from one currency to another"""
    try:
        # Validate currencies are supported
        supported_currencies = await service.get_supported_currencies()
        supported_codes = {curr.code for curr in supported_currencies}
        
        if request.from_currency not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source currency: {request.from_currency}"
            )
        
        if request.to_currency not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target currency: {request.to_currency}"
            )
        
        conversion_result = await service.convert_amount(
            request.amount,
            request.from_currency,
            request.to_currency
        )
        
        if conversion_result is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to convert {request.from_currency} to {request.to_currency} at this time"
            )
        
        return conversion_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert currency: {str(e)}"
        )

@router.post("/currencies/refresh", response_model=SupportedCurrenciesResponse)
async def refresh_currencies(
    service: CurrencyService = Depends(get_currency_service)
) -> SupportedCurrenciesResponse:
    """Force refresh top 10 currencies list from API"""
    try:
        # Clear cache and fetch fresh data
        currencies = await service._fetch_currencies_from_api()
        if currencies is None:
            currencies = service._get_fallback_currencies()
        
        # Cache the fresh data
        cache_key = f"{service.cache_key_prefix}currencies_top10"
        await service._cache_currencies(currencies, cache_key)
        
        return SupportedCurrenciesResponse(
            currencies=currencies,
            total_count=len(currencies)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh currencies: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: CurrencyService = Depends(get_currency_service)
) -> HealthResponse:
    """Check service health"""
    try:
        health_status = await service.health_check()
        
        overall_status = "healthy" if all(health_status.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=health_status.get("timestamp", "unknown"),
            redis_connected=health_status["redis_connected"],
            api_accessible=health_status["api_accessible"]
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            timestamp="unknown",
            redis_connected=False,
            api_accessible=False
        )
