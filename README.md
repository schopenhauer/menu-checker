# Menu Checker for Paiper Lek

Automatically checks for new menus on https://paiperlek.lu/kantin/ for SEA Gonderange/Bourglinster and sends the PDF by email when a new menu is available.

## Setup

1. **Create virtual environment** (if not already done):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure email settings**:
   ```bash
   cp config.json.example config.json
   ```
   
   Edit `config.json` with your email settings:
   - **For Gmail**: Use an App Password (not your regular password)
     - Go to Google Account → Security → 2-Step Verification → App passwords
     - Generate a new app password for this application
   - **For other providers**: Update the SMTP server and port accordingly

   Example for Gmail:
   ```json
   {
     "email": {
       "from": "your-email@gmail.com",
       "to": "len@rengaw.lu",
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587,
       "username": "your-email@gmail.com",
       "password": "your-16-char-app-password"
     }
   }
   ```

## Usage

### Manual Check

Run the script manually:
```bash
python menu_checker.py
```

### Automated Checks with Cron

To check automatically every day at 8 AM, add this to your crontab:

```bash
crontab -e
```

Add this line:
```
0 8 * * * cd /home/soda/code/menu && /home/soda/code/menu/venv/bin/python /home/soda/code/menu/menu_checker.py >> /home/soda/code/menu/menu_checker.log 2>&1
```

Or check every weekday (Monday-Friday) at 8 AM:
```
0 8 * * 1-5 cd /home/soda/code/menu && /home/soda/code/menu/venv/bin/python /home/soda/code/menu/menu_checker.py >> /home/soda/code/menu/menu_checker.log 2>&1
```

## How It Works

1. **Scrapes the website** to find the PDF link for SEA Gonderange/Bourglinster
2. **Downloads the PDF** and calculates its hash
3. **Compares** with the previously downloaded menu (stored in `menu_state.json`)
4. **Sends an email** with the PDF attachment if a new menu is detected
5. **Stores the state** to avoid sending duplicate notifications

## Files

- `menu_checker.py` - Main script
- `config.json` - Email configuration (not in git)
- `menu_state.json` - Tracks the last menu (auto-generated)
- `menus/` - Downloaded PDFs (auto-created)
- `requirements.txt` - Python dependencies

## Troubleshooting

### Email not sending
- Check your SMTP credentials in `config.json`
- For Gmail, ensure you're using an App Password
- Check if your email provider requires SSL instead of TLS

### PDF not found
- The website structure may have changed
- Check the script output for error messages
- You may need to adjust the HTML parsing logic

### Permission denied
- Make the script executable: `chmod +x menu_checker.py`
- Check file permissions for the directory
