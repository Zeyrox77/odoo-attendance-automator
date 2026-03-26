\# 🕐 Odoo Attendance Script



A lightweight Python script to log your daily attendance in Odoo directly from the command line — no browser needed. Supports full days, half days, and custom time entries.



\---



\## ✨ Features



\- \*\*Preset time slots\*\* – full day, morning half-day, afternoon half-day

\- \*\*Manual entry\*\* – define custom start/end times for morning and/or afternoon

\- \*\*Secure credential storage\*\* – credentials are saved in your OS keyring (Windows Credential Manager, macOS Keychain, or Linux Secret Service); your password is never stored in plain text

\- \*\*Automatic timezone conversion\*\* – local times are converted to UTC before being sent to the Odoo server

\- \*\*One-time setup\*\* – credentials are saved after the first run and reused automatically



\---



\## 📋 Requirements



\- Python \*\*3.9\*\* or newer (uses the built-in `zoneinfo` module)

\- An active Odoo account with access to the HR Attendance module



\---



\## 🚀 Installation



\*\*1. Clone or download the repository\*\*



```bash

git clone https://github.com/your-username/odoo-attendance-script.git

cd odoo-attendance-script

```



\*\*2. Install dependencies\*\*



\#### 🪟 Windows

No virtual environment needed. Just run:



```cmd

pip install -r requirements.txt

```



\#### 🐧 Linux

Modern Linux distributions (Ubuntu 23.04+, Debian 12+, etc.) block system-wide pip installs by default (PEP 668). You need to use a virtual environment:



```bash

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

```



To run the script later, always activate the virtual environment first:



```bash

source venv/bin/activate

python odoo\_attendance.py

```



`requirements.txt` contains:

```

requests

beautifulsoup4

keyring

```



\---



\## ⚙️ Configuration



Open `odoo\_attendance.py` and adjust the two constants at the top of the file:



```python

\# Your company's Odoo instance URL

ODOO\_URL = "https://your-odoo-instance.com"



\# Your local timezone (IANA format)

TIMEZONE = "Europe/Zurich"

```



Common timezone examples:



| Location | Timezone string |

|---|---|

| Zurich / Bern | `Europe/Zurich` |

| Berlin / Vienna | `Europe/Berlin` |

| London | `Europe/London` |

| New York | `America/New\_York` |

| Los Angeles | `America/Los\_Angeles` |



A full list of valid timezone strings can be found at \[Wikipedia – List of tz database time zones](https://en.wikipedia.org/wiki/List\_of\_tz\_database\_time\_zones).



\---



\## ▶️ Usage



Run the script from your terminal:



```bash

python odoo\_attendance.py

```



\### First run



You will be prompted once to enter your Odoo email address and password. These are then stored securely in your OS keyring and will be reused on every subsequent run.



\### Time slot selection



```

Which times would you like to record?

&#x20; \[1] Standard full day (08:00 - 12:00 \& 13:00 - 17:00)

&#x20; \[2] Half day morning (08:00 - 12:00)

&#x20; \[3] Half day afternoon (13:00 - 17:00)

&#x20; \[4] Manual (define custom times)

```



For option \*\*4 – Manual\*\*, you will be asked whether you want to enter times for the morning (`m`), afternoon (`a`), or both (`b`), and then provide start and end times in `HH:MM` format.



\---



\## 📁 File Overview



```

odoo-attendance-script/

├── odoo\_attendance.py   # Main script

├── requirements.txt     # Python dependencies

└── README.md            # This file

```



The script also creates a small config file at `\~/odoo\_config.json` to store your username between runs (the password itself is kept only in the OS keyring).



\---



\## 🔒 Security Notes



\- Your \*\*password is never stored on disk\*\*. It is saved exclusively in your operating system's secure credential store via the `keyring` library.

\- The script disables SSL certificate verification (`session.verify = False`) to support self-signed certificates common in internal/on-premise Odoo installations. If your instance uses a trusted certificate, you can remove those two lines for stricter security.

\- To reset your saved credentials, delete `\~/odoo\_config.json` and remove the entry named `odoo-attendance-script` from your OS keyring. The script will prompt you to re-enter your credentials on the next run.



\---



\## 🛠️ Troubleshooting



| Problem | Solution |

|---|---|

| `Login failed` | Double-check your Odoo URL, email, and password. Reset credentials by deleting `\~/odoo\_config.json`. |

| `Could not find CSRF token` | The login page structure may differ. Verify the `ODOO\_URL` has no trailing slash. |

| `Could not find Employee ID` | Your Odoo user account may not be linked to an employee record. Ask your Odoo administrator. |

| `zoneinfo` module not found | Upgrade to Python 3.9+, or install `backports.zoneinfo` for older versions. |

| Keyring errors on Linux | Install a backend: `sudo apt install gnome-keyring` or `pip install secretstorage`. |



\---



\## 📄 License



MIT License – feel free to use, modify, and distribute this script.

