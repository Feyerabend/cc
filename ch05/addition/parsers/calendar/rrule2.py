import re
from datetime import datetime, timedelta

# RRULE, get recurring event dates within the given date range
def parse_rrule(rrule, start_date, end_date):
    dates = []

    # optional components
    count_match = re.search(r"COUNT=(\d+)", rrule)
    count = int(count_match.group(1)) if count_match else None

    interval_match = re.search(r"INTERVAL=(\d+)", rrule)
    interval = int(interval_match.group(1)) if interval_match else 1

    bymonth_match = re.search(r"BYMONTH=([\d,]+)", rrule)
    bymonths = list(map(int, bymonth_match.group(1).split(','))) if bymonth_match else None

    bymonthday_match = re.search(r"BYMONTHDAY=([\d,-]+)", rrule)
    bymonthdays = list(map(int, bymonthday_match.group(1).split(','))) if bymonthday_match else None

    byday_match = re.search(r"BYDAY=([A-Z]{2}(,\-?\d)?)+", rrule)
    if byday_match:
        byday_items = byday_match.group(0).split(',')
        days_of_week = {
            'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6
        }
        bydays = [days_of_week[day[:2]] for day in byday_items]
        positions = [int(day[2:]) if len(day) > 2 else None for day in byday_items]
    else:
        bydays, positions = None, None

    current_date = start_date

    # yearly recurrence
    if "YEARLY" in rrule:
        while current_date <= end_date:
            if count and len(dates) >= count:
                break
            if bymonths and current_date.month not in bymonths:
                current_date = current_date.replace(year=current_date.year + 1)
                continue
            if bymonthdays and current_date.day not in bymonthdays:
                current_date = current_date + timedelta(days=1)  # next day
                continue
            dates.append(current_date)
            current_date = current_date.replace(year=current_date.year + interval)

    # monthly recurrence
    elif "MONTHLY" in rrule:
        while current_date <= end_date:
            if count and len(dates) >= count:
                break
            if bymonthdays and current_date.day not in bymonthdays:
                current_date += timedelta(days=1)
                continue
            dates.append(current_date)
            current_date = current_date.replace(month=(current_date.month + interval - 1) % 12 + 1,
                                                year=current_date.year + (current_date.month + interval - 1) // 12)

    # weekly recurrence
    elif "WEEKLY" in rrule:
        while current_date <= end_date:
            if count and len(dates) >= count:
                break
            if bydays and current_date.weekday() not in bydays:
                current_date += timedelta(days=1)
                continue
            dates.append(current_date)
            current_date += timedelta(weeks=interval)

    # daily recurrence
    elif "DAILY" in rrule:
        while current_date <= end_date:
            if count and len(dates) >= count:
                break
            dates.append(current_date)
            current_date += timedelta(days=interval)

    return dates


# check if a date is within given range
def is_within_range(date, start_date, end_date):
    return start_date <= date <= end_date


# ICS file
ics_file = './helgdagar.ics'

#  date range
start_year = 2023
end_year = 2025
range_start = datetime(start_year, 1, 1)
range_end = datetime(end_year, 12, 31)

with open(ics_file, 'r') as f:
    ics_data = f.read()

# regular expression to match events with recurrence rules
event_pattern = re.compile(
    r"BEGIN:VEVENT.*?"
    r"SUMMARY;LANGUAGE=sv:(.*?)\s"  # summary
    r".*?DTSTART;VALUE=DATE:(\d{8})\s"  # start date
    r".*?DTEND;VALUE=DATE:(\d{8})\s"  # end date
    r".*?RRULE:(.*?)\s"  # recurrence rule
    r"END:VEVENT", re.DOTALL
)

# all events matching the pattern
recurrent_events = event_pattern.findall(ics_data)

# print the recurrent events within the date range
for event in recurrent_events:
    summary, start_date_str, end_date_str, rrule = event
    # start and end date from the event data
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    end_date = datetime.strptime(end_date_str, "%Y%m%d")
    
    # the event's recurring dates within the given range
    event_dates = parse_rrule(rrule, start_date, range_end)
    
    # print event and its occurrences
    if event_dates:
        print(f"Event: {summary}")
        for date in event_dates:
            if is_within_range(date, range_start, range_end):
                print(f"  Occurs on: {date.strftime('%Y-%m-%d')}")
        print("-" * 40)