from datetime import datetime, timedelta

class CardBuilder:
    def __init__(self):
        self.vcard = ""


    def generate_vcard(self):
        fn = input("Enter full name: ")
        email = input("Enter email address: ")
        vcard = f"BEGIN:VCARD\nVERSION:4.0\nPRODID:-//Thunderbird.net/NONSGML Thunderbird CardBook V86.0\n"
        vcard += f"FN:{fn}\nN:;{fn};;;\nEMAIL;PREF=1:{email}\nREV:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
        vcard += "END:VCARD"
        return vcard




                


