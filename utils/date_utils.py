"""
Date handling utilities for standardized date operations across the application.
Provides consistent parsing, formatting, and validation of dates and times.
"""

import re
from datetime import datetime, date
from dateutil import parser as date_parser
from typing import Any, Dict, Optional, Tuple, Union


# Date format constants
DATE_FORMAT = "%d-%m-%Y"  # Standard date format: DD-MM-YYYY
TIME_FORMAT_12H = "%I:%M %p"  # 12-hour time format with AM/PM: 10:30 PM
TIME_FORMAT_24H = "%H:%M"  # 24-hour time format: 22:30
DATETIME_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"  # ISO format for timestamps


def parse_date(date_str: str, dayfirst: bool = True) -> Optional[date]:
    """
    Parse a date string into a date object using fuzzy matching.
    
    Args:
        date_str: Date string to parse
        dayfirst: Whether to treat the first number as day (European format)
                 rather than month (US format)
    
    Returns:
        A date object, or None if parsing fails
    """
    if not date_str:
        return None
        
    try:
        # Handle 'N/A' or similar values
        if isinstance(date_str, str) and date_str.lower() in ['n/a', 'na', 'none', 'not available', 'not specified']:
            return None
            
        return date_parser.parse(date_str, fuzzy=True, dayfirst=dayfirst).date()
    except (ValueError, TypeError) as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None


def parse_time(time_str: str) -> Optional[datetime.time]:
    """
    Parse a time string into a time object using fuzzy matching.
    
    Args:
        time_str: Time string to parse
    
    Returns:
        A time object, or None if parsing fails
    """
    if not time_str:
        return None
        
    try:
        # Handle 'N/A' or similar values
        if isinstance(time_str, str) and time_str.lower() in ['n/a', 'na', 'none', 'not available', 'not specified']:
            return None
            
        return date_parser.parse(time_str, fuzzy=True).time()
    except (ValueError, TypeError) as e:
        print(f"Error parsing time '{time_str}': {e}")
        return None


def format_date(date_obj: Optional[Union[date, datetime]]) -> str:
    """
    Format a date object to the standard date format (DD-MM-YYYY).
    
    Args:
        date_obj: Date or datetime object to format
    
    Returns:
        Formatted date string, or empty string if date_obj is None
    """
    if not date_obj:
        return ""
        
    return date_obj.strftime(DATE_FORMAT)


def format_time_12h(time_obj: Optional[Union[datetime.time, datetime]]) -> str:
    """
    Format a time object to 12-hour format (10:30 PM).
    
    Args:
        time_obj: Time or datetime object to format
    
    Returns:
        Formatted time string, or empty string if time_obj is None
    """
    if not time_obj:
        return ""
        
    return time_obj.strftime(TIME_FORMAT_12H)


def format_time_24h(time_obj: Optional[Union[datetime.time, datetime]]) -> str:
    """
    Format a time object to 24-hour format (22:30).
    
    Args:
        time_obj: Time or datetime object to format
    
    Returns:
        Formatted time string, or empty string if time_obj is None
    """
    if not time_obj:
        return ""
        
    return time_obj.strftime(TIME_FORMAT_24H)


def normalize_date_format(date_str: str) -> str:
    """
    Convert any date string to the standard date format (DD-MM-YYYY).
    
    Args:
        date_str: Date string to normalize
    
    Returns:
        Normalized date string, or original string if parsing fails
    """
    date_obj = parse_date(date_str)
    if date_obj:
        return format_date(date_obj)
    return date_str


def normalize_time_format(time_str: str, use_24h: bool = False) -> str:
    """
    Convert any time string to the standard time format.
    
    Args:
        time_str: Time string to normalize
        use_24h: Whether to use 24-hour format (default: False, uses 12-hour format)
    
    Returns:
        Normalized time string, or original string if parsing fails
    """
    time_obj = parse_time(time_str)
    if time_obj:
        if use_24h:
            return format_time_24h(time_obj)
        else:
            return format_time_12h(time_obj)
    return time_str


def validate_event_dates(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and standardize date fields in an event dictionary.
    
    Args:
        event: Event dictionary containing event details
    
    Returns:
        Event dictionary with standardized date fields
    """
    # Process start_date
    if event.get("start_date"):
        start_date_obj = parse_date(event["start_date"])
        if start_date_obj:
            event["start_date"] = format_date(start_date_obj)
    
    # Process end_date
    if event.get("end_date"):
        end_date_obj = parse_date(event["end_date"])
        if end_date_obj:
            event["end_date"] = format_date(end_date_obj)
    elif event.get("start_date"):
        # If no end_date but start_date exists, set end_date = start_date
        event["end_date"] = event["start_date"]
    
    # Process start_time
    if event.get("start_time"):
        start_time_obj = parse_time(event["start_time"])
        if start_time_obj:
            event["start_time"] = format_time_12h(start_time_obj)
        else:
            event["start_time"] = "12:00 AM"  # Default start time
    else:
        event["start_time"] = "12:00 AM"  # Default start time
    
    # Process end_time
    if event.get("end_time"):
        end_time_obj = parse_time(event["end_time"])
        if end_time_obj:
            event["end_time"] = format_time_12h(end_time_obj)
        else:
            event["end_time"] = "11:59 PM"  # Default end time
    else:
        event["end_time"] = "11:59 PM"  # Default end time
    
    return event


def is_date_in_range(date_to_check: Union[str, date], 
                    start_date: Union[str, date], 
                    end_date: Union[str, date]) -> bool:
    """
    Check if a date is within a given range (inclusive).
    
    Args:
        date_to_check: Date to check
        start_date: Start date of range
        end_date: End date of range
    
    Returns:
        True if date is in range, False otherwise
    """
    # Parse date strings if needed
    if isinstance(date_to_check, str):
        date_to_check_obj = parse_date(date_to_check)
        if not date_to_check_obj:
            return False
    else:
        date_to_check_obj = date_to_check
    
    if isinstance(start_date, str):
        start_date_obj = parse_date(start_date)
        if not start_date_obj:
            return False
    else:
        start_date_obj = start_date
    
    if isinstance(end_date, str):
        end_date_obj = parse_date(end_date)
        if not end_date_obj:
            return False
    else:
        end_date_obj = end_date
    
    # Check if date is in range
    return start_date_obj <= date_to_check_obj <= end_date_obj


def do_date_ranges_overlap(range1_start: Union[str, date], 
                          range1_end: Union[str, date],
                          range2_start: Union[str, date], 
                          range2_end: Union[str, date]) -> bool:
    """
    Check if two date ranges overlap.
    
    Args:
        range1_start: Start date of first range
        range1_end: End date of first range
        range2_start: Start date of second range
        range2_end: End date of second range
    
    Returns:
        True if ranges overlap, False otherwise
    """
    # Parse date strings if needed
    if isinstance(range1_start, str):
        range1_start_obj = parse_date(range1_start)
        if not range1_start_obj:
            return False
    else:
        range1_start_obj = range1_start
    
    if isinstance(range1_end, str):
        range1_end_obj = parse_date(range1_end)
        if not range1_end_obj:
            return False
    else:
        range1_end_obj = range1_end
    
    if isinstance(range2_start, str):
        range2_start_obj = parse_date(range2_start)
        if not range2_start_obj:
            return False
    else:
        range2_start_obj = range2_start
    
    if isinstance(range2_end, str):
        range2_end_obj = parse_date(range2_end)
        if not range2_end_obj:
            return False
    else:
        range2_end_obj = range2_end
    
    # Ranges overlap if one range doesn't entirely come before or after the other
    return not (range1_end_obj < range2_start_obj or range1_start_obj > range2_end_obj) 