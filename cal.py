from caldav.elements import dav, cdav
from caldav.lib.url import URL
from caldav.davclient import DAVClient
from datetime import datetime, timedelta
import logging
import requests

# Set up connection parameters
url = 'https://davical.scom.ca/test@scom.ca/addresses'
username = 'test@scom.ca'
password = 'Testing123'


# # Set the XML body for the PROPFIND request
# xml_body = '''<?xml version="1.0" encoding="UTF-8"?>
# <D:propfind xmlns:D="DAV:">
#   <D:prop>
#     <D:resourcetype/>
#     <D:displayname/>
#   </D:prop>
# </D:propfind>'''

# # Set the headers for the request
# headers = {
#     'Content-Type': 'application/xml',
#     'Depth': '1'
# }

# # Send the PROPFIND request
# response = requests.request('PROPFIND', url, data=xml_body, headers=headers, auth=(username, password))

# # Check the response status code
# if response.status_code == 207:
#     # Parse the XML response to extract the address book URLs
#     address_books = []
#     xml_data = response.content
#     # Use your preferred XML parsing method here to extract the URLs
#     # For example, you can use the ElementTree library:
#     import xml.etree.ElementTree as ET
#     root = ET.fromstring(xml_data)
#     for response in root.findall('{DAV:}response'):
#         href = response.find('{DAV:}href').text
#         address_books.append(href)
    
#     # Print the list of address book URLs
#     for address_book in address_books:
#         print(address_book)
# else:
#     print('Error:', response.status_code)


import requests
from vobject import readOne

# Set the XML body for the PROPFIND request
xml_body = '''<?xml version="1.0" encoding="UTF-8"?>
<D:propfind xmlns:D="DAV:">
  <D:prop>
    <D:resourcetype/>
    <D:displayname/>
  </D:prop>
</D:propfind>'''

# Set the headers for the request
headers = {
    'Content-Type': 'application/xml',
    'Depth': '1'
}

# Send the PROPFIND request
response = requests.request('PROPFIND', url, data=xml_body, headers=headers, auth=(username, password))

# Check the response status code
if response.status_code == 207:
    # Parse the XML response to extract the address book URLs
    address_books = []
    xml_data = response.content
    # Use your preferred XML parsing method here to extract the URLs
    # For example, you can use the ElementTree library:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_data)
    for response in root.findall('{DAV:}response'):
        href = response.find('{DAV:}href').text
        address_book_url = 'https://davical.scom.ca' + href
        
        # Send a request to retrieve the address book data
        address_book_response = requests.get(address_book_url, auth=(username, password))
        if address_book_response.status_code == 200:
            # Parse the VCF file using the vobject library
            vcard = readOne(address_book_response.text)
            # Extract the relevant information from the vCard object
            # Modify the code here to extract the required fields from the vCard
            # You can access properties like vcard.n, vcard.email, etc.
            # For example:
            name = vcard.n.value
            email = vcard.email.value
            # Once you have the required data, you can create a dictionary or data structure
            # to store and manipulate the address book details
            
            # Add the address book details to the address_books list
            address_books.append({'name': name, 'email': email})
        else:
            print(f"Failed to retrieve address book data at URL: {address_book_url}")
else:
    print('Error:', response.status_code)
# Enable debugging for the CalDAV library
logging.basicConfig(level=logging.DEBUG)
# Print the address book data
for address_book in address_books:
    print(address_book)
