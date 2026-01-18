from icalendar import Calendar
import os

# Load the ICS file
ics_file = './helgdagar.ics'

with open(ics_file, 'rb') as f:
    calendar = Calendar.from_ical(f.read())

# Extract events with recurrence rules
recurrent_events = []

for event in calendar.subcomponents:
    if event.name == "VEVENT":
        # Check for recurrence rule
        rrule = event.get('RRULE')
        if rrule:
            recurrent_events.append({
                "summary": event.get('SUMMARY'),
                "start": event.get('DTSTART').dt,
                "end": event.get('DTEND').dt,
                "rrule": rrule.to_ical().decode('utf-8')
            })

# Print out the recurrent events
for event in recurrent_events:
    print(f"Event: {event['summary']}")
    print(f"Start: {event['start']}")
    print(f"End: {event['end']}")
    print(f"Recurrence Rule: {event['rrule']}")
    print("-" * 40)