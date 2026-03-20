
# Delhi Property Scraper

A full-stack web application that automatically scrapes **Delhi property registration records** from the Delhi Government website and stores them in a **MySQL database**.

The system uses **FastAPI + Selenium + EasyOCR + React** to automate scraping and display results through a web interface.

---

# Features

• Automatic scraping of Delhi property records
• OCR based captcha solving using EasyOCR
• Manual captcha entry if OCR fails
• Data stored in MySQL database
• Resume scraping if backend stops
• WebSocket live scraper status updates
• React UI with filters for searching records

---

# Tech Stack

## Backend

* FastAPI
* Selenium
* EasyOCR
* MySQL
* OpenCV
* NumPy

## Frontend

* React
* Axios

---

# Project Structure

```
project/

backend/
│
├── main.py
├── scraper.py
├── requirements.txt
├── .env
└── chromedriver.exe

frontend/
│
├── src/
│   ├── App.js
│   ├── App.css
│
├── package.json
```

---

# Start (Need Python , SQL and Node.js in system )

# System Requirements

Before running the project install:

• Python **3.13+**
• Node.js **18+**
• MySQL Server
• Google Chrome + chromedriver.exe


Install Node.js
👉 Download from official site:
🔗 https://nodejs.org/
choose: Download LTS (Recommended) version

After install, verify:
node -v
npm -v


Install Python (3.10+)
👉 Download from official site:
🔗 https://www.python.org/downloads/

⚠️IMPORTANT during install:
✔ Tick this option:
Add Python to PATH

After install, verify:
python --version


Install MySQL Server
👉 Download from official site:
🔗 https://dev.mysql.com/downloads/mysql/
choose: MySQL Installer for Windows (recommended)

👉 Download workbench from official site:
🔗 https://dev.mysql.com/downloads/workbench/


# SETUP STEPS

STEP 1. Install Chrome + Install chromedriver (IMPORTANT)

👉 Since your project uses Selenium:
Install Google Chrome ( IF ALREADY HAVE THEN ) Download matching ChromeDriver OR use webdriver-manager


i. Methond to check Chrome version :-
Go to chrome -> Setting -> About Chrome 

ii. Download matching ChromeDriver version :-
https://googlechromelabs.github.io/chrome-for-testing/

iii. Extract chromedriver.zip, then inside you will see chromedriver.exe

Then delete chromedriver.exe from Project(Yuktic_DORIS) and past your downloaded chromedriver.exe in same place (Copy chromedriver.exe and Put it inside project: backend/chromedriver.exe)




STEP 2. MySQL Workbench

i. Create Database:-

CREATE DATABASE delhi_property_scraper;
USE delhi_property_scraper;

ii. Create Table

CREATE TABLE property_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reg_no VARCHAR(50),
    reg_date DATE,
    first_party TEXT,
    second_party TEXT,
    property_address TEXT,
    area VARCHAR(100),
    deed_type TEXT,
    property_type VARCHAR(50),
    sro_name VARCHAR(150),
    locality_name VARCHAR(150),
    scrape_status ENUM('IN_PROGRESS','COMPLETED'),
    UNIQUE (reg_no, sro_name, locality_name)
);


iii. Change .env.example name to .env and then change its details, then place it inside backend




STEP 3.  Go to backend folder

i. RUN in PowerShell: python -m venv venv
ii. Then Run Windows: venv\Scripts\activate
    Mac/Linux: source venv/bin/activate
iii. pip install -r requirements.txt
iv. uvicorn main:app --reload





STEP 4. Run backend :-
uvicorn main:app --reload

Backend runs on:
http://localhost:8000




STEP 5. Go to frontend folder

i. RUN in PowerShell: npm install
ii. npm start

Frontend runs on:
http://localhost:3000



STEP 6. Connect Backend & DB

In your backend Folder change env, ensure DB config:

host="localhost"
user="root"
password="your_password"
database="delhi_property_scraper"
---



# How to Use

1. Open the frontend UI
2. Select **SRO**
3. Select **Locality**
4. Click **Fetch Records**

If records are not present in the database, the scraper will automatically start.

---

# API Endpoints

| Endpoint          | Description            |
| ----------------- | ---------------------- |
| `/sro`            | Get list of SRO        |
| `/localities`     | Get list of localities |
| `/records`        | Fetch records          |
| `/start-scraper`  | Start scraper          |
| `/stop-scraper`   | Stop scraper           |
| `/captcha`        | Get captcha image      |
| `/submit-captcha` | Submit captcha         |

---

# Notes

• Chrome browser must be installed for Selenium to work.
• ChromeDriver is automatically installed using `webdriver-manager`.
• Do not upload `.env` to GitHub.

---

=======
# Yuktic_DORIS
Delhi Property Scraper using FastAPI, Selenium, EasyOCR, React

