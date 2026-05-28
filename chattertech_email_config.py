"""
ChatterTech.ai Email Integration
IMAP listener for incoming lead emails → autonomous task queue
"""

import imaplib
import email
from email.header import decode_header
import json
import re
from datetime import datetime

class ChatterTechEmailListener:
    def __init__(self):
        self.email = "inventor@aios.is"
        self.password = "F00lpr00f596!"
        self.imap_server = "mail.privatemail.com"
        self.imap_port = 993
        self.phone_number = "+14155940143"
        
    def connect(self):
        """Connect to IMAP server"""
        self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        self.mail.login(self.email, self.password)
        self.mail.select("inbox")
        print(f"✓ Connected to {self.email}")
        
    def fetch_unread(self):
        """Fetch unread emails and extract lead info"""
        status, messages = self.mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        
        leads = []
        for e_id in email_ids:
            status, msg_data = self.mail.fetch(e_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Extract subject and body
            subject = self._decode_header(msg["Subject"])
            from_addr = self._decode_header(msg["From"])
            date = msg["Date"]
            
            # Get body text
            body = self._get_email_body(msg)
            
            # Detect lead intent
            if self._is_lead_inquiry(subject, body):
                lead = self._extract_lead_info(subject, body, from_addr, date)
                leads.append(lead)
                print(f"🎯 New lead detected: {lead['business_type']} - {lead['name']}")
                
        return leads
    
    def _decode_header(self, header):
        """Decode email header"""
        if not header:
            return ""
        decoded = decode_header(header)
        return ''.join([part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part 
                       for part, encoding in decoded])
    
    def _get_email_body(self, msg):
        """Extract plain text body"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        return part.get_payload(decode=True).decode()
                    except:
                        pass
        else:
            try:
                return msg.get_payload(decode=True).decode()
            except:
                pass
        return ""
    
    def _is_lead_inquiry(self, subject, body):
        """Detect if email is a lead inquiry"""
        keywords = [
            "interested", "pricing", "demo", "trial", "quote", "cost",
            "virtual receptionist", "answering service", "call center",
            "after hours", "phone agent", "ai receptionist", "chattertech"
        ]
        text = (subject + " " + body).lower()
        return any(kw in text for kw in keywords)
    
    def _extract_lead_info(self, subject, body, from_addr, date):
        """Extract structured lead information"""
        # Detect business type
        business_types = {
            "medical": ["doctor", "clinic", "dental", "medical", "healthcare", "practice"],
            "home_services": ["hvac", "plumbing", "electrician", "roofing", "contractor", "repair"],
            "real_estate": ["real estate", "property", "realtor", "broker", "leasing", "apartment"],
            "legal": ["law", "attorney", "legal", "lawyer", "firm"],
            "ecommerce": ["store", "shop", "ecommerce", "retail", "online"]
        }
        
        text = (subject + " " + body).lower()
        detected_type = "general"
        for btype, keywords in business_types.items():
            if any(kw in text for kw in keywords):
                detected_type = btype
                break
        
        # Extract name from email
        name_match = re.search(r'([^<@]+)', from_addr)
        name = name_match.group(1).strip() if name_match else "Unknown"
        
        # Extract company if mentioned
        company_match = re.search(r'(?:company|business|called|name is)\s+["\']?([\w\s&]+)["\']?', text, re.IGNORECASE)
        company = company_match.group(1).strip() if company_match else "Not specified"
        
        # Determine recommended package
        packages = {
            "medical": {"name": "After-Hours Answering", "price": "$99/mo", "features": ["24/7 call coverage", "HIPAA-compliant", "Emergency routing"]},
            "home_services": {"name": "24/7 Virtual Receptionist", "price": "$199/mo", "features": ["Live transfer", "Appointment booking", "After-hours support"]},
            "real_estate": {"name": "Multi-Line Call Center", "price": "$399/mo", "features": ["Unlimited calls", "Property inquiries", "Showing scheduling"]},
            "legal": {"name": "Professional Receptionist", "price": "$299/mo", "features": ["Call screening", "Appointment setting", "Confidential handling"]},
            "ecommerce": {"name": "Customer Support Agent", "price": "$149/mo", "features": ["Order inquiries", "Return processing", "24/7 availability"]}
        }
        
        recommended = packages.get(detected_type, packages["home_services"])
        
        return {
            "id": f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": name,
            "email": from_addr.split('<')[-1].strip('>') if '<' in from_addr else from_addr,
            "company": company,
            "business_type": detected_type,
            "subject": subject,
            "inquiry_date": date,
            "recommended_package": recommended,
            "priority": "high" if detected_type in ["medical", "home_services"] else "medium",
            "source": "email",
            "status": "new"
        }
    
    def mark_as_read(self, email_ids):
        """Mark processed emails as read"""
        for e_id in email_ids:
            self.mail.store(e_id, '+FLAGS', '\\Seen')
    
    def close(self):
        """Close connection"""
        self.mail.close()
        self.mail.logout()

# Test the listener
if __name__ == "__main__":
    listener = ChatterTechEmailListener()
    try:
        listener.connect()
        leads = listener.fetch_unread()
        print(f"\nFound {len(leads)} new leads:")
        for lead in leads:
            print(f"  • {lead['name']} ({lead['business_type']}) → {lead['recommended_package']['name']}")
    finally:
        listener.close()
