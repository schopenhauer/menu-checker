#!/usr/bin/env python3
"""
Menu Checker for Paiper Lek
Checks if there's a new menu available for SEA Gonderange/Bourglinster
and sends the PDF by email if found.
"""

import os
import re
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib

class MenuChecker:
    def __init__(self, config_file='config.json'):
        self.url = 'https://paiperlek.lu/kantin/'
        self.section = 'SEA Gonderange/ Bourglinster'
        self.state_file = 'state.json'
        self.download_dir = Path('menus')
        self.download_dir.mkdir(exist_ok=True)
        
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
    
    def get_page_content(self):
        """Fetch the webpage content."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        return response.text
    
    def find_menu_pdf(self, html_content):
        """Find the PDF link for the specified section."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        pdf_url = None
        
        # Strategy 1: Find the exact heading "SEA Gonderange/ Bourglinster" and look for PDF link after it
        for element in soup.find_all(['h2', 'h3', 'h4']):
            text = element.get_text(strip=True)
            if 'SEA Gonderange' in text and 'Bourglinster' in text:
                # Found the heading, now look for the next PDF link after this element
                # Check the immediate parent div and its children
                parent = element.parent
                if parent:
                    # Look for PDF links only in this specific section (not in previous siblings)
                    links = parent.find_all('a', href=re.compile(r'\.pdf$', re.I))
                    for link in links:
                        href = link.get('href', '').lower()
                        # Make sure it's the Gonderange PDF, not Junglinster
                        if 'gonderange' in href and 'jgl' not in href.upper():
                            pdf_url = link.get('href')
                            break
                        # Also accept if the filename contains 'gonderange'
                        if 'gonderange' in href:
                            pdf_url = link.get('href')
                            break
                
                if pdf_url:
                    break
        
        # Strategy 2: Look for PDF links with 'gonderange' in the filename
        if not pdf_url:
            for link in soup.find_all('a', href=re.compile(r'\.pdf$', re.I)):
                href = link.get('href', '').lower()
                # Check if the URL contains 'gonderange' and exclude Junglinster PDFs
                if 'gonderange' in href and 'jgl' not in href.upper():
                    pdf_url = link.get('href')
                    break
        
        # Strategy 3: Fallback - look for any PDF with Gonderange/Bourglinster keywords
        if not pdf_url:
            for link in soup.find_all('a', href=re.compile(r'\.pdf$', re.I)):
                link_text = link.get_text(strip=True).lower()
                href = link.get('href', '').lower()
                # Make sure we're not picking up the Junglinster menu
                if ('gonderange' in href or 'bourglinster' in href) and 'junglinster' not in href:
                    pdf_url = link.get('href')
                    break
        
        if pdf_url:
            # Make absolute URL if relative
            if not pdf_url.startswith('http'):
                base_url = 'https://paiperlek.lu'
                pdf_url = base_url + pdf_url if pdf_url.startswith('/') else base_url + '/' + pdf_url
        
        return pdf_url
    
    def download_pdf(self, pdf_url):
        """Download the PDF file."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(pdf_url, headers=headers)
        response.raise_for_status()
        
        # Delete all previous menu files
        for old_file in self.download_dir.glob('menu_*.pdf'):
            old_file.unlink()
            print(f"Deleted old file: {old_file.name}")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.download_dir / f'menu_{timestamp}.pdf'
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        return filename, response.content
    
    def get_pdf_hash(self, content):
        """Calculate hash of PDF content."""
        return hashlib.sha256(content).hexdigest()
    
    def load_state(self):
        """Load the previous state."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_state(self, state):
        """Save the current state."""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def send_email(self, pdf_path, pdf_url):
        """Send email with PDF attachment."""
        msg = MIMEMultipart()
        msg['From'] = self.config['email']['from']
        msg['To'] = self.config['email']['to']
        msg['Subject'] = f'New Menu Available - SEA Gonderange/Bourglinster - {datetime.now().strftime("%Y-%m-%d")}'
        
        # Email body
        body = f"""
Hello,

A new menu is available for SEA Gonderange/Bourglinster.

Menu URL: {pdf_url}
Downloaded: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please find the PDF attached.

Gudden Appetit!
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', 
                                     filename=pdf_path.name)
            msg.attach(pdf_attachment)
        
        # Send email
        with smtplib.SMTP(self.config['email']['smtp_server'], 
                         self.config['email']['smtp_port']) as server:
            server.starttls()
            server.login(self.config['email']['username'], 
                        self.config['email']['password'])
            server.send_message(msg)
        
        print(f"✓ Email sent to {self.config['email']['to']}")
    
    def check_and_notify(self):
        """Main method to check for new menu and notify."""
        print(f"Checking menu at {self.url}")
        print(f"Looking for section: {self.section}")
        
        # Get page content
        html_content = self.get_page_content()
        
        # Find PDF link
        pdf_url = self.find_menu_pdf(html_content)
        
        if not pdf_url:
            print("✗ Could not find PDF for the specified section")
            return False
        
        print(f"Found PDF: {pdf_url}")
        
        # Download PDF
        pdf_path, pdf_content = self.download_pdf(pdf_url)
        pdf_hash = self.get_pdf_hash(pdf_content)
        
        # Load previous state
        state = self.load_state()
        previous_hash = state.get('last_pdf_hash')
        
        # Check if this is a new menu
        if pdf_hash != previous_hash:
            print("✓ New menu detected!")
            
            # Send email
            self.send_email(pdf_path, pdf_url)
            
            # Update state
            state['last_pdf_hash'] = pdf_hash
            state['last_pdf_url'] = pdf_url
            state['last_check'] = datetime.now().isoformat()
            state['last_pdf_path'] = str(pdf_path)
            self.save_state(state)
            
            print("✓ State updated")
            return True
        else:
            print("- No new menu (same as previous)")
            # Update last check time
            state['last_check'] = datetime.now().isoformat()
            self.save_state(state)
            return False


def main():
    """Main entry point."""
    checker = MenuChecker()
    try:
        checker.check_and_notify()
    except Exception as e:
        print(f"✗ Error: {e}")
        raise


if __name__ == '__main__':
    main()
