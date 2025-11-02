"""
Date parsing utilities for extracting and normalizing dates from text.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Try to import dateparser for advanced parsing
try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False
    logger.warning("dateparser not installed. Advanced date parsing will be limited.")


class DateParser:
    """Parse and normalize dates from natural language text."""
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Initialize the date parser.
        
        Args:
            reference_date: Reference date for relative date parsing (default: today)
        """
        self.reference_date = reference_date or datetime.now()
        
        # Month mappings
        self.months = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
    def extract_dates(self, text: str) -> List[Tuple[str, datetime, str]]:
        """
        Extract all dates from text.
        
        Args:
            text: Input text
            
        Returns:
            List of tuples (original_text, parsed_date, date_type)
        """
        dates = []
        
        # Pattern 1: Explicit dates (November 5th, Nov 5, 11/5, 2024-11-05)
        explicit_dates = self._extract_explicit_dates(text)
        dates.extend(explicit_dates)
        
        # Pattern 2: Relative dates (tomorrow, next week, in 3 days)
        relative_dates = self._extract_relative_dates(text)
        dates.extend(relative_dates)
        
        # Pattern 3: Day of week (Monday, next Friday)
        weekday_dates = self._extract_weekday_dates(text)
        dates.extend(weekday_dates)
        
        # Pattern 4: Advanced natural language dates (if dateparser available)
        if DATEPARSER_AVAILABLE:
            advanced_dates = self._extract_advanced_dates(text)
            dates.extend(advanced_dates)
        
        return dates
    
    def _extract_explicit_dates(self, text: str) -> List[Tuple[str, datetime, str]]:
        """Extract explicitly mentioned dates."""
        dates = []
        
        # Pattern: Month Day(st/nd/rd/th), Year (optional)
        # Example: November 5th, Nov 15, December 1st 2024
        pattern1 = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(?:(\d{4}))?\b'
        
        for match in re.finditer(pattern1, text.lower()):
            month_str = match.group(1)
            day = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else self.reference_date.year
            
            try:
                month = self.months[month_str]
                date = datetime(year, month, day)
                dates.append((match.group(0), date, 'explicit'))
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse date: {match.group(0)} - {e}")
        
        # Pattern: ISO format (2024-11-05, 11/05/2024, 11-05-2024)
        pattern2 = r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b'
        for match in re.finditer(pattern2, text):
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                date = datetime(year, month, day)
                dates.append((match.group(0), date, 'explicit'))
            except ValueError as e:
                logger.warning(f"Failed to parse ISO date: {match.group(0)} - {e}")
        
        # Pattern: MM/DD or MM-DD (current year assumed)
        pattern3 = r'\b(\d{1,2})[-/](\d{1,2})\b'
        for match in re.finditer(pattern3, text):
            try:
                month = int(match.group(1))
                day = int(match.group(2))
                year = self.reference_date.year
                date = datetime(year, month, day)
                dates.append((match.group(0), date, 'explicit'))
            except ValueError as e:
                logger.warning(f"Failed to parse short date: {match.group(0)} - {e}")
        
        return dates
    
    def _extract_relative_dates(self, text: str) -> List[Tuple[str, datetime, str]]:
        """Extract relative date expressions."""
        dates = []
        text_lower = text.lower()
        
        # Today
        if re.search(r'\btoday\b', text_lower):
            dates.append(('today', self.reference_date, 'relative'))
        
        # Tomorrow
        if re.search(r'\btomorrow\b', text_lower):
            tomorrow = self.reference_date + timedelta(days=1)
            dates.append(('tomorrow', tomorrow, 'relative'))
        
        # Yesterday
        if re.search(r'\byesterday\b', text_lower):
            yesterday = self.reference_date - timedelta(days=1)
            dates.append(('yesterday', yesterday, 'relative'))
        
        # In X days/weeks/months
        pattern = r'\bin\s+(\d+)\s+(day|days|week|weeks|month|months)\b'
        for match in re.finditer(pattern, text_lower):
            count = int(match.group(1))
            unit = match.group(2)
            
            if 'day' in unit:
                target_date = self.reference_date + timedelta(days=count)
            elif 'week' in unit:
                target_date = self.reference_date + timedelta(weeks=count)
            elif 'month' in unit:
                # Approximate: 30 days per month
                target_date = self.reference_date + timedelta(days=count * 30)
            
            dates.append((match.group(0), target_date, 'relative'))
        
        # Next week/month
        if re.search(r'\bnext\s+week\b', text_lower):
            next_week = self.reference_date + timedelta(weeks=1)
            dates.append(('next week', next_week, 'relative'))
        
        if re.search(r'\bnext\s+month\b', text_lower):
            next_month = self.reference_date + timedelta(days=30)
            dates.append(('next month', next_month, 'relative'))
        
        # End of week/month
        if re.search(r'\bend\s+of\s+(the\s+)?week\b', text_lower):
            days_until_sunday = (6 - self.reference_date.weekday()) % 7
            end_of_week = self.reference_date + timedelta(days=days_until_sunday)
            dates.append(('end of week', end_of_week, 'relative'))
        
        if re.search(r'\bend\s+of\s+(the\s+)?month\b', text_lower):
            # Go to last day of current month
            next_month = self.reference_date.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            dates.append(('end of month', end_of_month, 'relative'))
        
        # ASAP / As soon as possible (use today + 1 day as heuristic)
        if re.search(r'\b(asap|as soon as possible)\b', text_lower):
            asap_date = self.reference_date + timedelta(days=1)
            dates.append(('ASAP', asap_date, 'relative'))
        
        return dates
    
    def _extract_advanced_dates(self, text: str) -> List[Tuple[str, datetime, str]]:
        """Extract dates using advanced dateparser library."""
        dates = []
        
        # Common date phrases in meetings
        phrases = [
            r'\bby\s+([A-Z][a-z]+day)\b',  # by Friday
            r'\bby\s+(next\s+\w+)\b',  # by next week
            r'\bby\s+(end\s+of\s+\w+)\b',  # by end of month
            r'\bby\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)\b',  # by November 5th
            r'\bdeadline\s+(?:is\s+)?(\w+\s+\d{1,2})\b',  # deadline is November 5
            r'\bdue\s+(?:on\s+)?(\w+\s+\d{1,2})\b',  # due on November 5
        ]
        
        for pattern in phrases:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1) if match.lastindex else match.group(0)
                
                try:
                    parsed = dateparser.parse(
                        date_str,
                        settings={
                            'RELATIVE_BASE': self.reference_date,
                            'PREFER_DATES_FROM': 'future'
                        }
                    )
                    if parsed:
                        dates.append((date_str, parsed, 'advanced'))
                except Exception as e:
                    logger.debug(f"Failed to parse '{date_str}': {e}")
        
        return dates
    
    def _extract_weekday_dates(self, text: str) -> List[Tuple[str, datetime, str]]:
        """Extract dates specified by day of week."""
        dates = []
        text_lower = text.lower()
        
        weekdays = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        # Pattern: (next|this) (monday|tuesday|...)
        pattern = r'\b(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\b'
        
        for match in re.finditer(pattern, text_lower):
            modifier = match.group(1)
            weekday_str = match.group(2)
            target_weekday = weekdays[weekday_str]
            
            current_weekday = self.reference_date.weekday()
            
            if modifier == 'next':
                days_ahead = (target_weekday - current_weekday + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week
            else:  # 'this'
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0 and self.reference_date.hour > 12:
                    days_ahead = 7  # If it's afternoon, "this Monday" means next Monday
            
            target_date = self.reference_date + timedelta(days=days_ahead)
            dates.append((match.group(0), target_date, 'weekday'))
        
        # Pattern: just weekday name (assume next occurrence)
        for weekday_str, weekday_num in weekdays.items():
            pattern = r'\b' + weekday_str + r'\b'
            if re.search(pattern, text_lower) and not re.search(r'\b(next|this|last)\s+' + weekday_str, text_lower):
                current_weekday = self.reference_date.weekday()
                days_ahead = (weekday_num - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7  # If today, assume next week
                
                target_date = self.reference_date + timedelta(days=days_ahead)
                dates.append((weekday_str, target_date, 'weekday'))
                break  # Only match once per weekday
        
        return dates
    
    def parse_date_range(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Parse a date range from text.
        
        Args:
            text: Text potentially containing date range
            
        Returns:
            Tuple of (start_date, end_date) or None
        """
        dates = self.extract_dates(text)
        
        if len(dates) >= 2:
            # Sort by date
            sorted_dates = sorted(dates, key=lambda x: x[1])
            return (sorted_dates[0][1], sorted_dates[1][1])
        elif len(dates) == 1:
            # Single date - use as both start and end
            return (dates[0][1], dates[0][1])
        
        return None
