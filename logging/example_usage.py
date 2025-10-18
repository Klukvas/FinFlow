"""
Example usage of the enhanced structured logging utilities.

This file demonstrates how to integrate the new logging system into your microservices.
"""

import sys
import os
from typing import Optional

# Add the logging directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logging_utils import (
    get_structured_logger, 
    set_request_context, 
    clear_request_context,
    generate_request_id,
    log_function_call
)

# Example service configuration
SERVICE_NAME = "expense_service"
LOG_LEVEL = "INFO"

# Initialize the structured logger
logger = get_structured_logger(__name__, SERVICE_NAME, LOG_LEVEL)

def example_basic_logging():
    """Example of basic structured logging"""
    logger.info("Service started", category="startup")
    logger.warning("This is a warning message", category="general")
    logger.error("This is an error message", category="error")

def example_request_logging():
    """Example of request-scoped logging"""
    # Set request context
    request_id = generate_request_id()
    set_request_context(request_id, user_id=123, service_name=SERVICE_NAME)
    
    logger.info("Processing request", category="request")
    logger.info("Request completed", category="request")
    
    # Clear context
    clear_request_context()

def example_business_operations():
    """Example of business operation logging"""
    logger.log_business_operation(
        operation="create_expense",
        user_id=123,
        resource_id="expense_456",
        details="Created new expense for $50.00"
    )
    
    logger.log_business_operation(
        operation="update_expense",
        user_id=123,
        resource_id="expense_456",
        details="Updated expense amount to $75.00"
    )

def example_api_logging():
    """Example of API request logging"""
    logger.log_api_request(
        method="POST",
        endpoint="/api/expenses",
        status_code=201,
        duration_ms=150.5,
        user_id=123
    )
    
    logger.log_api_request(
        method="GET",
        endpoint="/api/expenses/456",
        status_code=404,
        duration_ms=25.0,
        user_id=123
    )

def example_external_service_logging():
    """Example of external service call logging"""
    logger.log_external_service_call(
        service="category_service",
        endpoint="/api/categories/validate",
        status_code=200,
        duration_ms=45.2
    )
    
    logger.log_external_service_call(
        service="account_service",
        endpoint="/api/accounts/balance",
        status_code=500,
        duration_ms=2000.0,
        error="Connection timeout"
    )

def example_database_logging():
    """Example of database operation logging"""
    logger.log_database_operation(
        operation="INSERT",
        table="expenses",
        duration_ms=12.5,
        user_id=123
    )
    
    logger.log_database_operation(
        operation="UPDATE",
        table="expenses",
        duration_ms=8.2,
        user_id=123,
        error="Constraint violation"
    )

def example_security_logging():
    """Example of security event logging"""
    logger.log_security_event(
        event="unauthorized_access_attempt",
        user_id=456,
        details="Attempted to access expense from different user",
        ip_address="192.168.1.100"
    )
    
    logger.log_authentication(
        email="user@example.com",
        success=True,
        details="Login successful",
        ip_address="192.168.1.50"
    )

@log_function_call
def example_function_with_logging():
    """Example function with automatic logging decorator"""
    logger.info("Inside function with logging", category="function")
    return "Function completed"

def example_error_logging():
    """Example of error logging with exception details"""
    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        logger.error(
            "Division by zero error occurred",
            category="error",
            operation="calculation",
            details=str(e)
        )

if __name__ == "__main__":
    print("=== Structured Logging Examples ===\n")
    
    print("1. Basic Logging:")
    example_basic_logging()
    print()
    
    print("2. Request Logging:")
    example_request_logging()
    print()
    
    print("3. Business Operations:")
    example_business_operations()
    print()
    
    print("4. API Logging:")
    example_api_logging()
    print()
    
    print("5. External Service Logging:")
    example_external_service_logging()
    print()
    
    print("6. Database Logging:")
    example_database_logging()
    print()
    
    print("7. Security Logging:")
    example_security_logging()
    print()
    
    print("8. Function Logging:")
    example_function_with_logging()
    print()
    
    print("9. Error Logging:")
    example_error_logging()
    print()
    
    print("=== Examples Complete ===")
