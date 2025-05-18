#!/usr/bin/env python3
"""
Network Resilience Module - Provides robust networking patterns for the Football Match Tracking System

This module adds retry/backoff and circuit-breaker patterns to make network operations 
more resilient in the face of transient failures or service degradation.

Usage:
    from network_resilience import resilient_fetch, CircuitBreaker
"""

import time
import random
import asyncio
import aiohttp
import logging
from functools import wraps
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Type, Union
from datetime import datetime, timedelta

from log_config import get_logger

# Setup logger for this module
logger = get_logger("network_resilience")

class CircuitBreakerError(Exception):
    """Exception raised when a circuit breaker is open."""
    pass

class CircuitBreaker:
    """
    Circuit Breaker pattern implementation to prevent cascading failures.
    
    The circuit breaker has three states:
    - CLOSED: Requests flow normally
    - OPEN: Requests are immediately rejected
    - HALF_OPEN: Limited requests are allowed to test if the service is healthy again
    """
    
    # Circuit breaker states
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    
    def __init__(
        self, 
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Name of this circuit breaker (used for logging)
            failure_threshold: Number of consecutive failures before opening the circuit
            recovery_timeout: Time in seconds before transitioning from OPEN to HALF_OPEN
            half_open_max_calls: Maximum number of calls allowed in HALF_OPEN state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # State tracking
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        
        logger.info(f"Circuit breaker '{name}' initialized in CLOSED state")
    
    def __call__(self, func):
        """
        Decorator to wrap a function with circuit breaker protection.
        
        Args:
            func: The function to wrap
            
        Returns:
            Wrapped function with circuit breaker logic
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper
    
    def _state_transition(self, new_state):
        """Transition to a new state and log the change."""
        old_state = self.state
        self.state = new_state
        logger.info(f"Circuit breaker '{self.name}' state change: {old_state} -> {new_state}")
    
    async def call(self, func, *args, **kwargs):
        """
        Call the protected function with circuit breaker logic.
        
        Args:
            func: The function to call
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            CircuitBreakerError: If the circuit is open
        """
        self.total_calls += 1
        
        # Check if circuit is OPEN
        if self.state == self.OPEN:
            # Check if recovery timeout has elapsed
            if (self.last_failure_time and 
                datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)):
                # Transition to HALF_OPEN
                self._state_transition(self.HALF_OPEN)
                self.half_open_calls = 0
                logger.info(f"Circuit breaker '{self.name}' allowing test request in HALF_OPEN state")
            else:
                # Circuit is still OPEN, reject the request
                self.failed_calls += 1
                logger.warning(f"Circuit breaker '{self.name}' rejected request in OPEN state")
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")
        
        # Check if circuit is HALF_OPEN and we've reached the limit
        if self.state == self.HALF_OPEN and self.half_open_calls >= self.half_open_max_calls:
            self.failed_calls += 1
            logger.warning(f"Circuit breaker '{self.name}' rejected request in HALF_OPEN state (max calls reached)")
            raise CircuitBreakerError(f"Circuit breaker '{self.name}' is HALF_OPEN and at capacity")
        
        # Increment HALF_OPEN call counter if needed
        if self.state == self.HALF_OPEN:
            self.half_open_calls += 1
        
        # Call the protected function
        try:
            result = await func(*args, **kwargs)
            
            # Success - handle state transitions
            self.successful_calls += 1
            if self.state == self.HALF_OPEN:
                # If all half-open calls are successful, close the circuit
                if self.half_open_calls >= self.half_open_max_calls:
                    self._state_transition(self.CLOSED)
                    self.failure_count = 0
                    logger.info(f"Circuit breaker '{self.name}' closed after successful test calls")
            
            # Reset failure count on success
            if self.state == self.CLOSED:
                self.failure_count = 0
                
            return result
            
        except Exception as e:
            # Failure - handle state transitions
            self.failed_calls += 1
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == self.CLOSED and self.failure_count >= self.failure_threshold:
                # Too many failures, open the circuit
                self._state_transition(self.OPEN)
                logger.warning(f"Circuit breaker '{self.name}' opened after {self.failure_count} consecutive failures")
            
            if self.state == self.HALF_OPEN:
                # Any failure in HALF_OPEN returns to OPEN
                self._state_transition(self.OPEN)
                logger.warning(f"Circuit breaker '{self.name}' reopened after failure in HALF_OPEN state")
            
            # Reraise the original exception
            raise

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    initial_backoff: float = 1.0
    max_backoff: float = 30.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retry_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        aiohttp.ClientError,
        asyncio.TimeoutError,
        ConnectionError,
    ])

async def resilient_fetch(
    url: str, 
    session: aiohttp.ClientSession = None,
    retry_config: RetryConfig = None,
    circuit_breaker: CircuitBreaker = None,
    timeout: float = 10.0,
    method: str = "GET",
    **kwargs
) -> Dict:
    """
    Perform a resilient HTTP fetch with retry and circuit breaker protection.
    
    Args:
        url: URL to fetch
        session: Optional aiohttp session to use
        retry_config: Configuration for retry behavior
        circuit_breaker: Optional circuit breaker instance
        timeout: Request timeout in seconds
        method: HTTP method to use
        **kwargs: Additional arguments to pass to the request
        
    Returns:
        Response JSON as a dictionary
        
    Raises:
        Various HTTP exceptions if all retries fail
        CircuitBreakerError if the circuit breaker is open
    """
    retry_config = retry_config or RetryConfig()
    
    # Create session if one was not provided
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
    
    # Track attempts for logging
    attempt = 0
    last_exception = None
    
    # Apply circuit breaker if provided
    if circuit_breaker:
        # Define the inner fetch function to be protected by the circuit breaker
        @circuit_breaker
        async def protected_fetch():
            nonlocal attempt, last_exception
            return await _fetch_with_retry(url, session, retry_config, timeout, method, 
                                        attempt, last_exception, **kwargs)
        
        try:
            result = await protected_fetch()
        finally:
            if close_session:
                await session.close()
        return result
    else:
        # No circuit breaker, use retry-only approach
        try:
            return await _fetch_with_retry(url, session, retry_config, timeout, method, 
                                        attempt, last_exception, **kwargs)
        finally:
            if close_session:
                await session.close()

async def _fetch_with_retry(
    url, session, retry_config, timeout, method, attempt, last_exception, **kwargs
):
    """Internal function to handle the retry logic for HTTP requests."""
    backoff = retry_config.initial_backoff
    
    while attempt <= retry_config.max_retries:
        attempt += 1
        
        try:
            logger.debug(f"Request attempt {attempt}/{retry_config.max_retries + 1} to {url}")
            
            # Set timeout for this request
            kwargs['timeout'] = aiohttp.ClientTimeout(total=timeout)
            
            async with session.request(method, url, **kwargs) as response:
                # Check HTTP status code
                response.raise_for_status()
                
                # Parse JSON response
                result = await response.json()
                logger.debug(f"Request to {url} succeeded on attempt {attempt}")
                return result
                
        except tuple(retry_config.retry_exceptions) as e:
            last_exception = e
            
            # Check if we've hit max retries
            if attempt > retry_config.max_retries:
                logger.warning(f"Request to {url} failed after {attempt} attempts: {str(e)}")
                raise
            
            # Calculate backoff time with optional jitter
            if retry_config.jitter:
                # Add randomness to prevent thundering herd
                jitter = random.uniform(0, 0.1 * backoff)
                sleep_time = backoff + jitter
            else:
                sleep_time = backoff
                
            # Log and wait
            logger.warning(f"Request to {url} failed (attempt {attempt}): {str(e)}. "
                          f"Retrying in {sleep_time:.2f}s")
            
            # Wait before next attempt
            await asyncio.sleep(sleep_time)
            
            # Increase backoff for next attempt, but don't exceed max
            backoff = min(backoff * retry_config.backoff_factor, retry_config.max_backoff)
            
        except Exception as e:
            # Non-retriable exception
            logger.error(f"Non-retriable error in request to {url}: {str(e)}")
            raise
    
    # We should never reach here due to the retry loop logic, but just in case
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError(f"Request to {url} failed for unknown reasons")

# Example usage
async def example_usage():
    """Example of how to use the resilient_fetch function."""
    # Create a circuit breaker for the API
    api_circuit_breaker = CircuitBreaker(
        name="football-api",
        failure_threshold=3,
        recovery_timeout=60
    )
    
    # Create a custom retry configuration
    retry_config = RetryConfig(
        max_retries=5,
        initial_backoff=0.5,
        max_backoff=15.0
    )
    
    # Make a resilient request
    try:
        result = await resilient_fetch(
            "https://api.example.com/matches",
            circuit_breaker=api_circuit_breaker,
            retry_config=retry_config,
            headers={"Authorization": "Bearer TOKEN"}
        )
        return result
    except Exception as e:
        logger.error(f"Failed to fetch data: {str(e)}")
        return None

if __name__ == "__main__":
    # Example of direct usage
    asyncio.run(example_usage())
