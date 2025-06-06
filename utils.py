"""
Utility functions for the S&P 500 monitoring bot
"""

import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to retry a function on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {str(e)}")
                        break
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # If we get here, all retries failed
            return None
            
        return wrapper
    return decorator

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format a currency amount for display
    
    Args:
        amount: The amount to format
        currency: Currency code (default: USD)
        
    Returns:
        Formatted currency string
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_percentage(percentage: float, show_sign: bool = True) -> str:
    """
    Format a percentage for display
    
    Args:
        percentage: The percentage to format
        show_sign: Whether to show + sign for positive values
        
    Returns:
        Formatted percentage string
    """
    sign = ""
    if show_sign and percentage > 0:
        sign = "+"
    elif percentage < 0:
        sign = "-"
        percentage = abs(percentage)
    
    return f"{sign}{percentage:.2f}%"

def get_market_status_emoji(market_state: str) -> str:
    """
    Get emoji for market status
    
    Args:
        market_state: Market state string from Yahoo Finance
        
    Returns:
        Appropriate emoji for the market state
    """
    status_emojis = {
        'REGULAR': '🟢',  # Market open
        'CLOSED': '🔴',   # Market closed
        'PRE': '🟡',      # Pre-market
        'POST': '🟠',     # After-hours
        'PREPRE': '⚪',   # Pre-pre market
        'POSTPOST': '⚫'  # Post-post market
    }
    
    return status_emojis.get(market_state, '⚪')

def validate_environment_variables() -> bool:
    """
    Validate that all required environment variables are set
    
    Returns:
        True if all variables are valid, False otherwise
    """
    import os
    
    required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def log_system_info():
    """Log system information for debugging purposes"""
    import platform
    import sys
    
    logger.info("=== System Information ===")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Architecture: {platform.architecture()}")
    logger.info("=== End System Information ===")
