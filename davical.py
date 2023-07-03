
import requests
import json
import urllib.parse
import vobject
import random
import string
from datetime import datetime
from caldav.davclient import DAVClient


'''
sample card data 
'''
vcard = '''
    BEGIN:VCARD
    VERSION:4.0
    PRODID:-//Thunderbird.net/NONSGML Thunderbird CardBook V86.0
    FN:Davical Main
    N:Davical;Main;;;
    EMAIL;PREF=1:goodman@noman.ca
    REV:20230617T132145Z
    END:VCARD
    '''

'''
sample Calendar event data , ical data
Important to know and consider that calendar server time zone is UTC
'''
event_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//davical5 Corp.//CalDAV Client//EN
BEGIN:VEVENT
SUMMARY:new event 2
DTSTART:20230711T235900Z
DTEND:20230712T040000Z
LOCATION:Example Location
DESCRIPTION:This is an example added to calendar name with ics.
END:VEVENT
END:VCALENDAR"""


class DavicalClient:
    def __init__(self, httplink, username, password ):
        self.httplink = httplink 
        self.username = username
        self.password = password
        self.card_endpoint = '/{username}/{card_name}/' 
        self.calendar_endpoint = '/test@scom.ca/calendar/'
        self.vcard_id_chars = string.ascii_letters + string.digits
        self.url= self.httplink + self.calendar_endpoint 
        

    
    def make_request(self, method, endpoint, data):
        url = self.httplink 
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "DavicalClient",
            'Depth' : '1'
        }
        
        response = requests.request( method, url, auth=(self.username, self.password), headers=headers )
        response.raise_for_status()
        return response
    

   
    def addcard(self, vcard): 
        '''
        * innitiate an object
        * serelialize  Vcard as a string 
        * send a put request to save the Vcard to the davical server
        '''
        vcard_id = self.generate_vcard_id()
        v = vobject.readOne(vcard)
        vcard_str = v.serialize()
        url = self.httplink + self.card_endpoint + vcard_id + ".vcf"
        result = requests.put(url, auth=(self.username, self.password), data = vcard_str, headers={'Content-Type': 'text/vcard'})
        if result.status_code in [200, 201]:   
            return result.status_code
        else:
            raise Exception('Woops, something\'s gone wrong! The CardDAV server returned the HTTP status code ' + str(result.status_code) + '.')

        
    def generate_vcard_id(self):
        vcard_id = ''.join(random.choice(self.vcard_id_chars) for _ in range(26))
        vcard_id = '-'.join([vcard_id[i:i+4] for i in range(0, len(vcard_id), 4)])
        
        try:
            carddav = self.make_request("PROPFIND", self.httplink + vcard_id + '.vcf', vcard)

            if carddav is None:
                vcard_id = self.generate_vcard_id()
            return vcard_id
        except requests.exceptions.RequestException as e:
            print(f"Connection error occurred: {str(e)}")   



    def addcalendar(self, event_data):
        '''
         Extract the start date from the event data
         Convert event start date to datetime object
         Compare the event start date with the current date and time
         put event data to the server
        
        '''
        start_date_index = event_data.find("DTSTART:") + len("DTSTART:")
        end_date_index = event_data.find("Z", start_date_index)
        event_start_date = event_data[start_date_index:end_date_index]
        event_start_datetime = datetime.strptime(event_start_date, "%Y%m%dT%H%M%S")
        # Find the start index and end index of the SUMMARY property
        summary_start = event_data.find("SUMMARY:") + len("SUMMARY:")
        summary_end = event_data.find("\n", summary_start)

        # Extract the SUMMARY value
        summary = event_data[summary_start:summary_end].strip()

        # # Generate the filename based on the SUMMARY value
        # filename = f"event_{urllib.parse.quote(summary)}.ics"

        # # Generate the filename based on the SUMMARY value
        # filename = f"event_{summary.strip()}.ics"
        # Join the summary words using a separator (e.g., underscore)
        separator = "_"
        summary_words = summary.split()  # Split the summary into words
        joined_summary = separator.join(summary_words)
        event_url = self.url + joined_summary + '.ics'
       
        current_datetime = datetime.utcnow()
    
        if event_start_datetime >= current_datetime:  
            result = requests.put(event_url, auth=(self.username, self.password), data = event_data, headers={'Content-Type': 'text/calendar'})
            if result.status_code in [200, 201, 203, 204, 205, 206, 207, 208, 226] :   
                return result.status_code
            else:
                raise Exception('Woops, something\'s gone wrong! The CalDAV server returned the HTTP status code ' + str(result.status_code) + '.')
    
        else:
            return "Event schedule time should not be in the past "


    def searchcalendar(self, calendar_name):
        # Specify the desired calendar name
        calendar_name = 'Scom test Account calendar'    
        # Connect to the CalDAV server
        client = DAVClient(url=self.httplink, username=self.username, password=self.password)

        # Get a list of available calendars
        principal = client.principal()
        calendars = principal.calendars()
        calendar = None
        for cal in calendars:
            if cal.name == calendar_name:
                calendar = cal
                break

        if calendar is None:
            print("Calendar not found.")
            exit()
        # Fetch events from the calendar using calendar.search
        events = calendar.search()
        # Process the iCal event data
        calendar_events = []
        for event in events:
            event_data = event.data
            calendar_events.append(event_data)
            # Process the iCal data as needed
        return calendar_events

    def searchcard(self, card_name):
        endpoint = '/{username}/{card_name}/' +'.vcf'
        endpoint = endpoint.format(username=self.username, card_name=card_name)
        url = self.httplink + endpoint
        payload = {
        'prop': 'getetag,address-data',
        'filter': 'FN={card_name}'.format(card_name=urllib.parse.quote(card_name))
    }
    
        # URL-encode the payload data
        encoded_payload = urllib.parse.urlencode(payload)
        response = self.make_request('PROPFIND', endpoint, data = encoded_payload)
        return response.text


    def delcard(self, calendar_name, card_name):
        endpoint = "/{username}/{calendar_name}/{card_name}.vcf"
        endpoint = endpoint.format(username=self.username, calendar_name=calendar_name, card_name = card_name)
        self.make_request("DELETE", endpoint)



    def delcal(self, calendar_name):
        endpoint = "/{username}/{calendar_name}/"
        endpoint = endpoint.format(username=self.username, calendar_name=calendar_name)
        self.make_request("DELETE", endpoint)
        return 


        
davclient = DavicalClient('https://davical.scom.ca', 'test@scom.ca', 'Testing123' )

try:
    print(davclient.searchcard('addresses'))
except requests.exceptions.RequestException as e:
    print("Connection Error:", e)






        
  
