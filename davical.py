
import requests
import vobject
import random
import string
from datetime import datetime
from caldav.davclient import DAVClient
import xml.etree.ElementTree as ET
from vobject import readOne


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
DTSTART:20230710T200000Z
DTEND:20230710T210000Z
LOCATION:Example Location
DESCRIPTION:This is an update of the existing card.
END:VEVENT
END:VCALENDAR"""


# Set the XML body for the PROPFIND request
xml_body = '''<?xml version="1.0" encoding="UTF-8"?>
<D:propfind xmlns:D="DAV:">
<D:prop>
    <D:resourcetype/>
    <D:displayname/>
</D:prop>
</D:propfind>'''


class DavicalClient:
    def __init__(self, httplink, username, password ):
        self.httplink = httplink 
        self.username = username
        self.password = password
        self.card_endpoint = '/test@scom.ca/addresses/' 
        self.calendar_endpoint = '/test@scom.ca/calendar/'
        self.vcard_id_chars = string.ascii_letters + string.digits
        self.calendar_url = self.httplink + self.calendar_endpoint 
        self.card_url = self.httplink + self.card_endpoint
    
    
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
         Find the start index and end index of the SUMMARY property
         Extract the SUMMARY value
         Split the summary into words
         generate filename 
        '''
        start_date_index = event_data.find("DTSTART:") + len("DTSTART:")
        end_date_index = event_data.find("Z", start_date_index)
        event_start_date = event_data[start_date_index:end_date_index]
        event_start_datetime = datetime.strptime(event_start_date, "%Y%m%dT%H%M%S")
        
        summary_start = event_data.find("SUMMARY:") + len("SUMMARY:")
        summary_end = event_data.find("\n", summary_start)
        summary = event_data[summary_start:summary_end].strip()
        separator = "_"
        summary_words = summary.split()  
        joined_summary = separator.join(summary_words)
        event_url = self.calendar_url + joined_summary + '.ics'
       
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
        '''
        Specify the desired calendar name
        Connect to the CalDAV server
        Get a list of available calendars
        Fetch events from the calendar using calendar.search
        Process the iCal event data
        Process the iCal data as needed

        '''
        calendar_name = 'Scom test Account calendar'    
        client = DAVClient(url=self.httplink, username=self.username, password=self.password)
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
        events = calendar.search()
        calendar_events = []
        for event in events:
            event_data = event.data
            calendar_events.append(event_data)
        return calendar_events


    def searchcard(self):
        '''
        Set up connection parameters
        Send the PROPFIND request 
        Parse the XML response to extract the address book URLs
        Send a request to retrieve the address book data
        Parse the VCF file using the vobject library
        Extract fields from the vCard
        '''
        
        url = self.httplink  + self.card_endpoint
        headers = {
            'Content-Type': 'application/xml',
            'Depth': '1'
        }
        address_books_list = []
        url_list = []
        address_books = []
        response = requests.request('PROPFIND', url, data=xml_body, headers=headers, auth=(self.username, self.password))
        if response.status_code == 207:   
            xml_data = response.content
            root = ET.fromstring(xml_data)
            for response in root.findall('{DAV:}response'):
                href = response.find('{DAV:}href').text
                address_book_url = self.httplink + href
                url_list.append(address_book_url)
                if not address_book_url.endswith('.vcf'):
                    continue
                address_book_response = requests.get(address_book_url, auth=(self.username, self.password))
                if  address_book_response.status_code == 200: 
                    vcard = readOne(address_book_response.text)
                    name = vcard.n.value
                    email = vcard.email.value
                    address_books.append({'name': name, 'email': email})
                else:
                    print(f"Failed to retrieve address book data at URL: {address_book_url}")
        else:
            print('Error:', response.status_code)
        for address_book in address_books:
            address_books_list.append(address_book)
        return address_books_list



    def delcal(self, summary):
        separator = "_"
        summary_words = summary.split()  
        joined_summary = separator.join(summary_words)
        username = 'test@scom.ca'
        password = 'Testing123'
        endpoint = f"/{username}/calendar/{joined_summary}"
        event_url = self.httplink  +endpoint + '.ics'

        if event_url is not None:              
            response = requests.delete(event_url, auth=(username,password))
            if response.status_code == 201:
                print(f"Event'{summary}' has been deleted calendar.")
            else:
        
                print(f"Failed to delete event '{summary}' from calendar.")
                print(f"Error: {response.status_code}")
        else:
            print('Card does not exist')
        
    
    def delcard(self, calendar_name, card_name):
        endpoint = "/{username}/{calendar_name}/{card_name}.vcf"
        endpoint = endpoint.format(username=self.username, calendar_name=calendar_name, card_name = card_name)
        self.make_request("DELETE", endpoint)

        
davclient = DavicalClient('https://davical.scom.ca', 'test@scom.ca', 'Testing123' )

try:
    # events = davclient.searchcalendar('calendar')
    # for event in events:
    #     print(event)
    # print(davclient.addcalendar(event_data))
    print (davclient.delcal('new event 2'))
    # print (davclient.addcard('addresses'))
except requests.exceptions.RequestException as e:
    print("Connection Error:", e)



