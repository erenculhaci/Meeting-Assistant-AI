import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False
    logger.warning("dateparser not installed. Advanced date parsing will be limited.")


class DateParser:    
    def __init__(self, reference_date: Optional[datetime] = None):
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
        
        # Pattern: MM/DD or MM-DD (current year)
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
        dates = []
        text_lower = text.lower()
        
        # Today
        if re.search(r'\btoday\b', text_lower):
            dates.append(('today', self.reference_date, 'relative'))
        
        # Tomorrow
        if re.search(r'\btomorrow\b', text_lower):
            tomorrow = self.reference_date + timedelta(days=1)
            dates.append(('tomorrow', tomorrow, 'relative'))
        
        # Day after tomorrow
        if re.search(r'\bday\s+after\s+tomorrow\b', text_lower):
            day_after = self.reference_date + timedelta(days=2)
            dates.append(('day after tomorrow', day_after, 'relative'))
        
        # Yesterday
        if re.search(r'\byesterday\b', text_lower):
            yesterday = self.reference_date - timedelta(days=1)
            dates.append(('yesterday', yesterday, 'relative'))
        
        # In X days/weeks/months/hours
        pattern = r'\bin\s+(\d+)\s+(hour|hours|day|days|week|weeks|month|months|year|years)\b'
        for match in re.finditer(pattern, text_lower):
            count = int(match.group(1))
            unit = match.group(2)
            
            if 'hour' in unit:
                target_date = self.reference_date + timedelta(hours=count)
            elif 'day' in unit:
                target_date = self.reference_date + timedelta(days=count)
            elif 'week' in unit:
                target_date = self.reference_date + timedelta(weeks=count)
            elif 'month' in unit:
                # More accurate month calculation
                target_date = self.reference_date + timedelta(days=count * 30)
            elif 'year' in unit:
                target_date = self.reference_date.replace(year=self.reference_date.year + count)
            
            dates.append((match.group(0), target_date, 'relative'))
        
        # Within X days/weeks (deadline meaning)
        pattern = r'\bwithin\s+(\d+)\s+(day|days|week|weeks|month|months)\b'
        for match in re.finditer(pattern, text_lower):
            count = int(match.group(1))
            unit = match.group(2)
            
            if 'day' in unit:
                target_date = self.reference_date + timedelta(days=count)
            elif 'week' in unit:
                target_date = self.reference_date + timedelta(weeks=count)
            elif 'month' in unit:
                target_date = self.reference_date + timedelta(days=count * 30)
            
            dates.append((match.group(0), target_date, 'relative'))
        
        # Next/This week/month/year
        if re.search(r'\bnext\s+week\b', text_lower):
            next_week = self.reference_date + timedelta(weeks=1)
            dates.append(('next week', next_week, 'relative'))
        
        if re.search(r'\bthis\s+week\b', text_lower):
            dates.append(('this week', self.reference_date, 'relative'))
        
        if re.search(r'\bnext\s+month\b', text_lower):
            next_month = self.reference_date + timedelta(days=30)
            dates.append(('next month', next_month, 'relative'))
        
        if re.search(r'\bthis\s+month\b', text_lower):
            dates.append(('this month', self.reference_date, 'relative'))
        
        if re.search(r'\bnext\s+year\b', text_lower):
            next_year = self.reference_date.replace(year=self.reference_date.year + 1)
            dates.append(('next year', next_year, 'relative'))
        
        # End of week/month/year variants
        if re.search(r'\b(by\s+)?(the\s+)?end\s+of\s+(the\s+)?(this\s+)?week\b', text_lower):
            days_until_sunday = (6 - self.reference_date.weekday()) % 7
            if days_until_sunday == 0:
                days_until_sunday = 7
            end_of_week = self.reference_date + timedelta(days=days_until_sunday)
            dates.append(('end of week', end_of_week, 'relative'))
        
        # "by Friday" pattern (end of this week essentially)
        if re.search(r'\b(by\s+)?end\s+of\s+this\s+week\b', text_lower):
            days_until_friday = (4 - self.reference_date.weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7
            end_of_week = self.reference_date + timedelta(days=days_until_friday)
            dates.append(('end of this week', end_of_week, 'relative'))
        
        if re.search(r'\b(by\s+)?month\s+end\b', text_lower):
            # Go to last day of current month
            next_month = self.reference_date.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            dates.append(('month end', end_of_month, 'relative'))
        
        if re.search(r'\b(by\s+)?(the\s+)?end\s+of\s+(the\s+)?(this\s+)?month\b', text_lower):
            # Go to last day of current month
            next_month = self.reference_date.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            dates.append(('end of month', end_of_month, 'relative'))
        
        if re.search(r'\b(by\s+)?(the\s+)?end\s+of\s+(the\s+)?year\b', text_lower):
            end_of_year = self.reference_date.replace(month=12, day=31)
            dates.append(('end of year', end_of_year, 'relative'))
        
        # End of day / EOD / Close of business (COB)
        if re.search(r'\b(by\s+)?(end\s+of\s+day|eod|close\s+of\s+business|cob)\b', text_lower):
            eod = self.reference_date.replace(hour=17, minute=0, second=0, microsecond=0)
            dates.append(('end of day', eod, 'relative'))
        
        # Start/Beginning of week/month
        if re.search(r'\b(by\s+)?(the\s+)?(start|beginning)\s+of\s+(the\s+)?(next\s+)?week\b', text_lower):
            is_next = 'next' in text_lower
            days_until_monday = (7 - self.reference_date.weekday()) % 7
            if days_until_monday == 0 and not is_next:
                days_until_monday = 0
            elif is_next:
                days_until_monday = (7 - self.reference_date.weekday())
            start_of_week = self.reference_date + timedelta(days=days_until_monday)
            dates.append(('start of week', start_of_week, 'relative'))
        
        if re.search(r'\b(by\s+)?(the\s+)?(start|beginning)\s+of\s+(the\s+)?(next\s+)?month\b', text_lower):
            is_next = 'next' in text_lower
            if is_next:
                # First day of next month
                next_month = (self.reference_date.replace(day=28) + timedelta(days=4)).replace(day=1)
                dates.append(('start of next month', next_month, 'relative'))
            else:
                start_of_month = self.reference_date.replace(day=1)
                dates.append(('start of month', start_of_month, 'relative'))
        
        # Early/Mid/Late week/month
        if re.search(r'\bearly\s+(next\s+)?week\b', text_lower):
            is_next = 'next' in text_lower
            days_ahead = 7 if is_next else 0
            early_week = self.reference_date + timedelta(days=days_ahead + 2)
            dates.append(('early week', early_week, 'relative'))
        
        if re.search(r'\bmid[\s-]?week\b', text_lower):
            days_until_wednesday = (2 - self.reference_date.weekday()) % 7
            mid_week = self.reference_date + timedelta(days=days_until_wednesday)
            dates.append(('mid-week', mid_week, 'relative'))
        
        if re.search(r'\blate\s+(next\s+)?week\b', text_lower):
            is_next = 'next' in text_lower
            days_ahead = 7 if is_next else 0
            late_week = self.reference_date + timedelta(days=days_ahead + 5)
            dates.append(('late week', late_week, 'relative'))
        
        # First thing [tomorrow/Monday/etc]
        if re.search(r'\bfirst\s+thing\s+(tomorrow|monday|tuesday|wednesday|thursday|friday)\b', text_lower):
            if 'tomorrow' in text_lower:
                first_thing = self.reference_date + timedelta(days=1)
                dates.append(('first thing tomorrow', first_thing.replace(hour=9, minute=0), 'relative'))
        
        # Before/After lunch
        if re.search(r'\bbefore\s+lunch\b', text_lower):
            before_lunch = self.reference_date.replace(hour=11, minute=30, second=0, microsecond=0)
            dates.append(('before lunch', before_lunch, 'relative'))
        
        if re.search(r'\bafter\s+lunch\b', text_lower):
            after_lunch = self.reference_date.replace(hour=14, minute=0, second=0, microsecond=0)
            dates.append(('after lunch', after_lunch, 'relative'))
        
        # No later than [timeframe]
        if re.search(r'\bno\s+later\s+than\s+(tomorrow|next\s+week|next\s+month)\b', text_lower):
            if 'tomorrow' in text_lower:
                deadline = self.reference_date + timedelta(days=1)
                dates.append(('no later than tomorrow', deadline, 'relative'))
            elif 'next week' in text_lower:
                deadline = self.reference_date + timedelta(weeks=1)
                dates.append(('no later than next week', deadline, 'relative'))
            elif 'next month' in text_lower:
                deadline = self.reference_date + timedelta(days=30)
                dates.append(('no later than next month', deadline, 'relative'))
        
        # ASAP / As soon as possible / Urgent / Immediately
        if re.search(r'\b(asap|as\s+soon\s+as\s+possible|urgent|urgently|immediately|right\s+away)\b', text_lower):
            asap_date = self.reference_date + timedelta(hours=24)
            dates.append(('ASAP', asap_date, 'relative'))
        
        return dates
    
    def _extract_advanced_dates(self, text: str) -> List[Tuple[str, datetime, str]]:
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
        dates = self.extract_dates(text)
        
        if len(dates) >= 2:
            # Sort by date
            sorted_dates = sorted(dates, key=lambda x: x[1])
            return (sorted_dates[0][1], sorted_dates[1][1])
        elif len(dates) == 1:
            # Single date - use as both start and end
            return (dates[0][1], dates[0][1])
        
        return None
