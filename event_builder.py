from datetime import datetime, timedelta

class EventBuilder:
    def __init__(self):
        self.event_data = ""

    def add_event(self):
        summary = input("Enter event summary: ")

        # Get event start date
        start_date_str = input("Enter event start date (YYYY-MM-DD): ")
        start_time_str = input("Enter event start time (HH:MM AM/PM): ")
        start_datetime = self.parse_datetime(start_date_str, start_time_str)

        # Get event end date
        end_date_str = input("Enter event end date (YYYY-MM-DD): ")
        end_time_str = input("Enter event end time (HH:MM AM/PM): ")
        end_datetime = self.parse_datetime(end_date_str, end_time_str)

        # Get other event details
        location = input("Enter event location: ")
        description = input("Enter event description: ")

        event = f"BEGIN:VEVENT\nSUMMARY:{summary}\nDTSTART:{start_datetime}\nDTEND:{end_datetime}\nLOCATION:{location}\nDESCRIPTION:{description}\nEND:VEVENT\n"

        self.event_data += event

    def parse_datetime(self, date_str, time_str):
        # Convert date and time strings to datetime object
        datetime_str = f"{date_str} {time_str}"
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")

        # Format datetime object to the desired format
        formatted_datetime = datetime_obj.strftime("%Y%m%dT%H%M%SZ")

        return formatted_datetime

    def generate_calendar(self):
        calendar = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//davical5 Corp.//CalDAV Client//EN\n"
        calendar += self.event_data
        calendar += "END:VCALENDAR"

        return calendar
                


