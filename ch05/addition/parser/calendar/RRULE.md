
## Overview of RRULE in iCalendar

Mostly many of the parsing of iCalendar files are handled through easy reasoning.

The RRULE (Recurrence Rule) property in iCalendar defines how an event recurs over time.
It allows events to repeat based on specific frequencies, intervals, and optional constraints
like specific days, months, or positions.

An RRULE has the following key components:
1. FREQ: Specifies the frequency of recurrence.
	- Values: YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY.
	- Example: FREQ=WEEKLY means the event repeats every week.
2. INTERVAL: Specifies how often the recurrence happens, based on the FREQ.
	- Default: 1 (every time the frequency occurs).
	- Example: FREQ=WEEKLY;INTERVAL=2 means every 2 weeks.
3. COUNT: Specifies the number of occurrences.
	- Example: FREQ=DAILY;COUNT=5 means the event occurs 5 times.
4. UNTIL: Specifies the end date for the recurrence in UTC format (YYYYMMDDTHHMMSSZ).
	- Example: FREQ=MONTHLY;UNTIL=20241231T000000Z means the event recurs monthly until December 31, 2024.
5. BYDAY: Specifies days of the week.
	- Values: MO (Monday), TU, WE, TH, FR, SA, SU.
	- Example: BYDAY=MO,WE,FR means every Monday, Wednesday, and Friday.
6. BYMONTH: Specifies the months of the year.
	- Values: 1 (January) through 12 (December).
	- Example: BYMONTH=1,6 means January and June.
7. BYMONTHDAY: Specifies days of the month.
	- Values: 1 through 31 (positive) or -1 (last day of the month).
	- Example: BYMONTHDAY=1,15 means the 1st and 15th of each month.
8. BYSETPOS: Specifies the nth occurrence in the frequency.
	- Example: BYDAY=MO;BYSETPOS=2 means the second Monday of the month.


### Syntax of an RRULE in iCalendar

The RRULE is added to an event using the RRULE property.

```icalendar
BEGIN:VEVENT
SUMMARY:Team Meeting
DTSTART;TZID=Europe/Stockholm:20240101T090000
RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR
END:VEVENT
```

### Examples of RRULEs for Different Frequencies

1. Daily Recurrence: Example: An event repeats daily for 10 occurrences.

```icalendar
DTSTART;TZID=Europe/Stockholm:20240101T090000
RRULE:FREQ=DAILY;COUNT=10
```

This means the event starts on January 1, 2024, and recurs daily for 10 times.

2. Weekly Recurrence: Example: An event occurs every other week on Mondays and Fridays.

```icalendar
DTSTART;TZID=Europe/Stockholm:20240101T090000
RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,FR
```

This means the event recurs every two weeks on Monday and Friday.


3. Monthly Recurrence: Example: An event occurs on the 1st and 15th of every month.

```icalendar
DTSTART;TZID=Europe/Stockholm:20240101T090000
RRULE:FREQ=MONTHLY;BYMONTHDAY=1,15
```

This means the event recurs on the 1st and 15th of each month, starting from January 1, 2024.

4. Yearly Recurrence: Example: An event occurs annually on June 21.

```icalendar
DTSTART;TZID=Europe/Stockholm:20240621T090000
RRULE:FREQ=YEARLY
```

This means the event recurs every year on June 21.

5. Specific Days with BYSETPOS: Example: An event occurs on the second Monday of each month.

```icalendar
DTSTART;TZID=Europe/Stockholm:20240101T090000
RRULE:FREQ=MONTHLY;BYDAY=MO;BYSETPOS=2
```

This means the event recurs on the second Monday of every month.

6. Recurring Until a Specific Date: Example: An event repeats weekly on Wednesdays until December 31, 2024.

```icalendar
DTSTART;TZID=Europe/Stockholm:20240101T090000
RRULE:FREQ=WEEKLY;BYDAY=WE;UNTIL=20241231T235959Z
```

This means the event ends after December 31, 2024.

Notes on RRULE Behavior
- If both COUNT and UNTIL are specified, COUNT takes precedence.
- The DTSTART property acts as the base date from which recurrences are calculated.
- You can combine multiple constraints (e.g., FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,FR).

Parsing RRULEs Programmatically

To parse and generate dates from RRULEs, you can:
- Use libraries like icalendar in Python.
- Write custom logic to handle patterns like FREQ, BYDAY, and UNTIL.


### Exceptions

One of the most challenging aspects of parsing iCalendar data, in my experience, is handling the RRULE property,
especially when it includes exceptions to the recurrence pattern. These exceptions, defined using properties
like EXDATE (dates to exclude) or RDATE (additional dates outside the rule), add complexity to parsing, as they
require precise adjustment of the calculated occurrences to align with the intended schedule. Ensuring accurate
handling of these exceptions demands not only a thorough understanding of the iCalendar standard but also careful
implementation to reconcile the base rule with its modifications.


#### Concepts for Handling Exceptions in iCalendar

1. EXDATE (Exception Dates):
	- Specifies specific dates that should be excluded from the recurrence pattern.
	- Format: A list of DATETIME values.
	- Example:

```icalendar
RRULE:FREQ=DAILY;COUNT=5
EXDATE;TZID=Europe/Stockholm:20240102T090000
```

In this example, the event repeats daily for 5 occurrences but skips January 2, 2024.

2. RDATE (Recurrence Dates):
	- Specifies additional dates that should be included, even if they don't follow the RRULE.
	- Format: A list of DATETIME values.
	- Example:

```icalendar
RRULE:FREQ=DAILY;COUNT=5
RDATE;TZID=Europe/Stockholm:20240107T090000
```

In this example, the event includes January 7, 2024, as an additional occurrence.

3. Combining RRULE, EXDATE, and RDATE:
	- The RRULE defines the main pattern.
	- EXDATE specifies exceptions to the pattern.
	- RDATE specifies additional occurrences outside the pattern.

Example iCalendar Event with Exceptions

```icalendar
BEGIN:VEVENT
SUMMARY:Daily Standup
DTSTART;TZID=Europe/Stockholm:20240101T090000
RRULE:FREQ=DAILY;COUNT=7
EXDATE;TZID=Europe/Stockholm:20240103T090000,20240105T090000
RDATE;TZID=Europe/Stockholm:20240108T090000
END:VEVENT
```

- RRULE: Repeats daily for 7 occurrences starting January 1, 2024.
- EXDATE: Skips January 3 and January 5.
- RDATE: Adds January 8 as an additional occurrence.

Final Dates: January 1, 2, 4, 6, 7, 8.

### Projects

#### Beginner-Level Projects

1. Basic Parsing and Display:
	- Objective: Parse a simple .ics file and extract basic event details such as SUMMARY, DTSTART, and DTEND.
	- Tasks:
	    - Extract event information and display it in plain text.
	    - Handle time zones from the TZID property in a basic way.
	- Learning Outcome: Familiarity with the iCalendar format and string parsing techniques.

2. Recurring Events:
	- Objective: Parse and calculate dates for events with RRULE.
	- Tasks:
	    - Implement support for daily, weekly, and monthly frequencies.
	    - Handle intervals (e.g. every 2 weeks).
	- Learning Outcome: Algorithmic thinking for handling recurrences.

#### Intermediate-Level Projects
3. Exceptions and Adjustments:
	- Objective: Extend the recurrence handling by supporting EXDATE and RDATE.
	- Tasks:
	    - Implement logic to exclude and add specific dates to the calculated recurrence pattern.
	    - Validate against a sample .ics file with multiple exceptions.
	- Learning Outcome: Combining rule-based logic with exception handling.
4. Advanced Recurrence Patterns:
	- Objective: Support additional iCalendar recurrence features, such as BYDAY, BYMONTH, and BYSETPOS.
	- Tasks:
	    - Handle complex patterns like "the second Tuesday of every month" or "every Monday and Wednesday in March."
	    - Combine multiple constraints (e.g. BYDAY and BYMONTH).
	- Learning Outcome: Parsing and implementing advanced patterns in real-world standards.

#### Advanced-Level Projects

5. Full Calendar Parser:
	- Objective: Build a Python library to parse .ics files fully and output structured JSON.
	- Tasks:
	    - Handle all event fields, including DESCRIPTION, LOCATION, and alarms (VALARM).
	    - Support multiple events and recurring patterns with exceptions.
	    - Validate and test against real-world .ics files from popular calendar services (Google Calendar, Outlook).
	- Learning Outcome: Building a reusable library and working with diverse datasets.

6. Integration with Python Databases:
	- Objective: Store parsed calendar data in a relational database.
	- Tasks:
	    - Design a database schema to store events, recurrences, and exceptions.
	    - Write Python scripts to parse .ics files and populate the database.
	    - Query the database to generate reports like "all events in a given week."
	- Learning Outcome: Combining parsing with database integration.

#### Final Project

7. Interactive Calendar Visualization:
	- Objective: Create a visual, interactive calendar using JavaScript, backed by Python-parsed data.
	- Tasks:
	    - Parse .ics files in Python and serve the event data as an API (e.g. using Flask or FastAPI).
	    - Create a front-end calendar interface in JavaScript (e.g. with libraries like FullCalendar.js or plain HTML/CSS/JS).
	    - Display events with tooltips, date selection, and navigation by month or week.
	    - Add filters for categories (e.g. "only work meetings").
	- Learning Outcome: Full-stack development skills, combining data processing, API design, and front-end visualization.

#### Additional Challenge Ideas

- Time Zone Handling: Parse and convert event times across multiple time zones.
- Conflict Detection: Identify overlapping events or schedule conflicts.
- Export to iCalendar: Create a tool to generate .ics files from structured data (e.g. JSON or database entries).
- Multi-User Support: Parse calendars from multiple users, merge events, and resolve conflicts for a shared calendar.

