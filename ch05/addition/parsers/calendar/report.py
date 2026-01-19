import datetime
import csv
from typing import List, Dict, Any
from collections import defaultdict

# mock calendar event data
events = [
    {'id': 7248439392057609069, 'title': 'Access-A-Ride Pickup', 'tag': 'work', 'location': '1000 Broadway Ave.\\, Brooklyn',
     'start': datetime.datetime(2024, 10, 2, 10, 34), 'duration': 0.5},
    {'id': -3046634699688398392, 'title': 'Access-A-Ride Pickup', 'tag': 'work', 'location': '900 Jay St.\\, Brooklyn',
     'start': datetime.datetime(2024, 10, 2, 20, 0), 'duration': 0.5},
    {"id": 1, "title": "Team Meeting", "tag": "work", "location": "Conference Room A",
     "start": datetime.datetime(2024, 10, 1, 10, 0), "duration": 1.5},
    {"id": 2, "title": "Lunch with Client", "tag": "business", "location": "Downtown Cafe",
     "start": datetime.datetime(2024, 10, 2, 12, 0), "duration": 2.0},
    {"id": 3, "title": "Project Review", "tag": "work", "location": "Conference Room A",
     "start": datetime.datetime(2024, 10, 5, 15, 0), "duration": 2.5},
]

# DSL parser
class Report:
    def __init__(self, name: str):
        self.name = name
        self.filter_criteria = None
        self.aggregations = []
        self.output_format = "PlainText"
        self.output_options = {}
        self.visualization = None

    def filter(self, condition):
        self.filter_criteria = condition

    def aggregate(self, *aggregations):
        self.aggregations.extend(aggregations)

    def output(self, format: str, **options):
        self.output_format = format
        self.output_options = options

    def visualize(self, chart_type: str, **options):
        self.visualization = {"type": chart_type, **options}

    def generate(self, events: List[Dict[str, Any]]):

        # Step 1: Filter events
        filtered_events = [event for event in events if self.filter_criteria(event)]

        # Step 2: Perform aggregations
        results = {}
        for agg in self.aggregations:
            results.update(agg(filtered_events))

        # Step 3: Output results
        if self.output_format == "PlainText":
            self.output_plaintext(results)
        elif self.output_format == "CSV":
            self.output_csv(results)
        elif self.output_format == "Markdown":
            self.output_markdown(results)
        # Visualization placeholder, not impl.
        if self.visualization:
            self.render_visualization(results)

    def output_plaintext(self, results):
        print(f"Report: {self.name}")
        for key, value in results.items():
            print(f"{key}: {value}")

    def output_csv(self, results):
        filename = self.output_options.get("filename", f"{self.name}.csv")
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Metric", "Value"])
            for key, value in results.items():
                writer.writerow([key, value])
        print(f"CSV report saved to {filename}")

    def output_markdown(self, results):
        print(f"# {self.output_options.get('title', self.name)}")
        for key, value in results.items():
            print(f"- *{key}*: {value}")

    def render_visualization(self, results):
        # Placeholder for visualization
        print(f"Generating {self.visualization['type']} visualization...")

# aggregation
def count_events(events):
    return {"total_events": len(events)}

def sum_duration(events):
    total_duration = sum(event.get("duration", 0) for event in events)
    return {"total_hours": total_duration}

# filter conditions
def events_between(start_date, end_date):
    def condition(event):
        return start_date <= event["start"] <= end_date
    return condition

def events_with_tag(tag):
    def condition(event):
        return event.get("tag") == tag
    return condition

# DSL Script
def example_report():
    report = Report("Monthly Summary")
    report.filter(events_between(datetime.datetime(2024, 10, 1), datetime.datetime(2024, 10, 31)))
    report.aggregate(count_events, sum_duration)
    report.output("Markdown", title="October 2024 Events Summary")
    report.generate(events)

example_report()
