
import requests
import vobject
import random
import string
from datetime import datetime
from caldav.davclient import DAVClient
import xml.etree.ElementTree as ET
from vobject import readOne


# Set the XML body for the PROPFIND request
xml_body = '''<?xml version="1.0" encoding="UTF-8"?>
<D:propfind xmlns:D="DAV:">
<D:prop>
    <D:resourcetype/>
    <D:displayname/>
</D:prop>
</D:propfind>'''




class DavicalClient:
    def __init__(self, httplink, username, password):
        self.httplink = httplink 
        self.username = username
        self.password = password
        self.vcard_id_chars = string.ascii_letters + string.digits
     
    
    def make_request(self, method, endpoint, data = None):
        url = self.httplink 
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "DavicalClient",
            'Depth' : '1'
        }
        
        response = requests.request( method, url, auth=(self.username, self.password), headers=headers )
        response.raise_for_status()
        return response
   
    def addcard(self, card_name, vcard): 
         
        '''
        * innitiate an object
        * serelialize  Vcard as a string 
        * send a put request to save the Vcard to the davical server
        '''

        endpoint = '/{username}/{card_name}/'
        endpoint = endpoint.format(username=self.username,card_name = card_name)
        vcard_id = self.generate_vcard_id()
        v = vobject.readOne(vcard)
        vcard_str = v.serialize()
        url = self.httplink + endpoint + vcard_id + ".vcf"
        
        result = requests.put(url, auth=(self.username, self.password), data = vcard_str, headers={'Content-Type': 'text/vcard'})
       
        if result.status_code in [200, 201]:   
            return result.status_code
        else:
            raise Exception('Woops, something\'s gone wrong! The CardDAV server returned the HTTP status code ' + str(result.status_code) + '.')

        
    def generate_vcard_id(self):
        vcard_id = ''.join(random.choice(self.vcard_id_chars) for _ in range(26))
        vcard_id = '-'.join([vcard_id[i:i+4] for i in range(0, len(vcard_id), 4)])
        
        try:
            carddav = self.make_request("PROPFIND", self.httplink + vcard_id + '.vcf' )

            if carddav is None:
                vcard_id = self.generate_vcard_id()
            return vcard_id
        except requests.exceptions.RequestException as e:
            print(f"Connection error occurred: {str(e)}")   


    def addcalendar(self, calendar_name, event_data):
        
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

        endpoint = '/{username}/{calendar_name}/'
        endpoint = endpoint.format(username=self.username,calendar_name = calendar_name)
        calendar_url = self.httplink + endpoint 
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
        event_url = calendar_url + joined_summary + '.ics'
        
        current_datetime = datetime.utcnow()
        if event_start_datetime >= current_datetime:  
            result = requests.put(event_url, auth=(self.username, self.password), data = event_data, headers={'Content-Type': 'text/calendar'})
            if result.status_code in [200, 201, 203, 204, 205, 206, 207, 208, 226] :   
                return result.status_code
            else:
                raise Exception('Woops, something\'s gone wrong! The CalDAV server returned the HTTP status code ' + str(result.status_code) + '.')
    
        else:
            return "Event schedule time should not be in the past "

    def retrieve_single_calendar_event(self,summary):
        separator = "_"
        summary_words = summary.split()  # Split the summary into words
        joined_summary = separator.join(summary_words)
        endpoint = f"/{self.username}/calendar/{joined_summary}"
        event_url = self.httplink + endpoint + '.ics'

        if event_url is not None:              
            response = requests.get(event_url, auth=(self.username,self.password))
            if response.status_code == 200:
                response = response.text
            else:
                print(f"Error: {response.status_code}")
        else:
             print('Card does not exist')
        return response

    def searchcalendar(self, calendar_name):
        '''
        Specify the desired calendar name
        Connect to the CalDAV server
        Get a list of available calendars
        Fetch events from the calendar using calendar.search
        Process the iCal event data
        Process the iCal data as needed

        '''
        calendar_name = 'Scom Test Account calendar' 
        url = self.httplink 
        client = DAVClient(url, username = self.username, password = self.password)
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
        events = calendar.events()
        return events
        calendar_events = []
        for event in events:
            event_data = event.text
            calendar_events.append(event_data)
        return event_data



    def searchcard(self, card_name):
        '''
        Set up connection parameters
        Send the PROPFIND request 
        Parse the XML response to extract the address book URLs
        Send a request to retrieve the address book data
        Parse the VCF file using the vobject library
        Extract fields from the vCard
        '''
        endpoint = '/{username}/{card_name}/'
        endpoint = endpoint.format(username=self.username,card_name = card_name)
        url = self.httplink  + endpoint
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



    def delcal(self, calendar_name, summary):
        separator = "_"
        summary_words = summary.split()  
        joined_summary = separator.join(summary_words)
        endpoint = '/{username}/{calendar_name}/'
        endpoint = endpoint.format(username=self.username,calendar_name = calendar_name) + joined_summary
        event_url = self.httplink  + endpoint + '.ics'
        if event_url is not None:              
            response = requests.delete(event_url, auth=(self.username,self.password))
            if response.status_code in (201, 204):
                print(f"Event'{summary}' has been deleted calendar.")
            else:
        
                print(f"Failed to delete event '{summary}' from calendar.")
                print(f"Error: {response.status_code}")
        else:
            return 'Card does not exist'
        
    
    def delcard(self, card_name, card_id):
        #https://davical.scom.ca/test@scom.ca/addresses/
        endpoint = "/{username}/{card_name}/{card_id}"
        endpoint = endpoint.format(username = self.username, card_name = card_name, card_id = card_id)+ '.vcf'
        address_book_url = self.httplink + endpoint
        if card_id is not None:
            try:         
                response = requests.delete(address_book_url, auth=(self.username,self.password))
                print(f"vCard '{card_id}' has been deleted from addresses books.")
            except requests.HTTPError as e:
                print(f"Failed to delete vCard '{card_id}' from calendar addresses books.")
                print(f"Error: {e}")
        else:
             print('Card does not exist')
        return response


    def update_calendar_event(self,summary, new_event_data):
        separator = "_"
        url = 'https://davical.scom.ca/'
        summary_words = summary.split()  # Split the summary into words
        joined_summary = separator.join(summary_words)
        endpoint = f"/{self.username}/calendar/{joined_summary}"
        event_url = self.httplink + endpoint + '.ics'

        if event_url is not None:
            response = requests.get(event_url, auth=(self.username, self.password))
            if response.status_code == 200:
                response_text = response.text
                updated_event = self.modify_event(response_text, new_event_data)
                update_response = requests.put(event_url, auth=(self.username, self.password), data=updated_event)
                
                if update_response.status_code == 204:
                    print(f"Event '{summary}' updated successfully.")
                else:
                    print(f"Failed to update event '{summary}' from calendar.")
                    print(f"Error: {update_response.status_code}")
            else:
                print(f"Failed to retrieve event '{summary}' from calendar.")
                print(f"Error: {response.status_code}")
        else:
            print('Card does not exist')

    def modify_event(self,event_data, new_event_data):
        modified_event = event_data

        for attribute, value in new_event_data.items():
            attribute_string = f"{attribute.upper()}:"
            if attribute_string in modified_event:
                start_index = modified_event.index(attribute_string) + len(attribute_string)
                end_index = modified_event.index("\n", start_index)
                existing_value = modified_event[start_index:end_index]
                modified_event = modified_event.replace(existing_value, value)

        return modified_event


    def retrieve_single_card(self, vcard_id, card_name):      
        endpoint = f"/{self.username}/{card_name}/"
        card_url = self.httplink + endpoint +vcard_id + ".vcf"
        if card_url is not None:              
            response = requests.get(card_url, auth=(self.username,self.password))
            if response.status_code == 200:
                response = response.text
            else:
                print(f"Error: {response.status_code}")
        else:
             print('Card does not exist')
        return response


    def update_card(self, vcard_id, new_card_data): 
        endpoint = f"/{self.username}/addresses/"
        card_url = self.httplink+ endpoint + vcard_id + ".vcf"

        if card_url is not None:
            response = requests.get(card_url, auth=(self.username, self.password))
            if response.status_code == 200:
                response_text = response.text
                updated_card = self.modify_card(response_text, new_card_data)
                update_response = requests.put(card_url, auth=(self.username, self.password), data=updated_card)
                
                if update_response.status_code == 204:
                    response = f"Event '{vcard_id}' updated successfully."
                else:
                    response = f"Error: {update_response.status_code}"
            else:
                response= f"Error: {response.status_code}"
        else:
            print('Card does not exist')
        return response


    def modify_card(self,card_data, new_card_data):
        modified_card = card_data

        for attribute, value in new_card_data.items():
            attribute_string = f"{attribute.upper()}:"
            if attribute_string in modified_card:
                start_index = modified_card.index(attribute_string) + len(attribute_string)
                end_index = modified_card.index("\n", start_index)
                existing_value = modified_card[start_index:end_index]
                modified_card = modified_card.replace(existing_value, value)

        return modified_card

            
