
## iCalendar Overview

iCalendar (also known as the iCal format) is a widely used file format for exchanging calendar
information. It allows users to share event, scheduling, and task information across different
applications and platforms, such as Google Calendar, Apple Calendar, and Microsoft Outlook.

The format is defined in RFC 5545 (published in September 2009), which obsoleted earlier RFCs
like 2445. iCalendar uses a plain text format with a structured syntax that is both human-readable
and machine-parsable.

Features
- Interoperability: Enables different calendar systems to exchange information seamlessly.
- Versatility: Supports events, to-dos, journal entries, and free/busy scheduling.
- Time Zones: Provides robust time zone support.
- Recurrence: Allows specification of repeating events or tasks.
- Attachments: Enables linking or embedding files.
- Alarms and Reminders: Supports notifications for events and tasks.

### iCalendar Data Scheme Overview

An iCalendar file typically has the .ics extension and consists of plain text content
structured into components, properties, and values.

1. Components

The primary building blocks of an iCalendar file are components that describe different calendar entities:
- VCALENDAR: The root component; contains metadata and other components.
- VEVENT: Represents calendar events (e.g., meetings, birthdays).
- VTODO: Describes tasks or to-dos (e.g., assignments, shopping lists).
- VJOURNAL: For journal entries or notes.
- VFREEBUSY: Specifies availability for scheduling (free/busy time).
- VALARM: Defines alarms and reminders for events or tasks.
- VTIMEZONE: Provides time zone information.

Each component begins with `BEGIN:<component>` and ends with `END:<component>`.

2. Properties

Properties define attributes of components. Common properties include:
- VERSION: Specifies the iCalendar version (e.g., 2.0 in RFC 5545).
- PRODID: Identifies the product generating the iCalendar data.
- DTSTART: Specifies the start date/time of an event or task.
- DTEND: Specifies the end date/time of an event.
- SUMMARY: A brief summary or title for an event/task.
- UID: A unique identifier for the calendar object.
- LOCATION: Specifies the event's location.
- DESCRIPTION: Provides additional details about the event/task.
- RRULE: Defines recurrence rules for repeating events/tasks.
- ATTENDEE: Lists participants for an event.
- ORGANIZER: Identifies the event's organizer.

3. Values

Properties can have values of different types, such as dates, text, or binary data.
- Dates and times are usually in the YYYYMMDDTHHMMSSZ format (UTC with Z) or local time.

Example iCalendar File

Below is an example of an .ics file for a meeting:

```icalendar
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//NONSGML Example Calendar//EN
BEGIN:VEVENT
UID:123456789@example.com
DTSTAMP:20241217T120000Z
DTSTART:20241220T150000Z
DTEND:20241220T160000Z
SUMMARY:Team Meeting
DESCRIPTION:Monthly planning meeting.
LOCATION:Conference Room A
ORGANIZER;CN=John Doe:mailto:john.doe@example.com
ATTENDEE;CN=Jane Smith:mailto:jane.smith@example.com
END:VEVENT
END:VCALENDAR
```

### Data Scheme

Hierarchical Structure
- VCALENDAR is the container; it wraps all other components.
- Components like VEVENT can contain properties like SUMMARY, UID, DTSTART.

Recurrence Rules (RRULE)

Defines repeating patterns for events. For example:

```icalendar
RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20241231T235959Z
```

- FREQ: Frequency of repetition (e.g., DAILY, WEEKLY, MONTHLY).
- BYDAY: Days of the week (e.g., MO for Monday).
- UNTIL: End date/time for the recurrence.

### Time Zones

Time zone data is specified using VTIMEZONE components, ensuring accurate time handling:

```icalendar
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:20241101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
END:STANDARD
END:VTIMEZONE
```

Summary of RFC 5545
- Defines the structure and syntax of the iCalendar format.
- Specifies MIME types (text/calendar) for interoperability.
- Provides detailed rules for encoding, recurrence, and time zone management.
- Addresses extensions through the X- prefix for non-standard properties.

For full details, you can consult the [RFC 5545](https://datatracker.ietf.org/doc/html/rfc5545) specification.
