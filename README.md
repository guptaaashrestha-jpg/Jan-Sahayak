<div align="center">

# Jan Sahayak
**Intelligent Civic Reporting and Predictive Urban Analytics**

[![Python Version](https://img.shields.io/badge/Python-3.14-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![AI](https://img.shields.io/badge/AI-Google_Gemini-orange.svg)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Bridging the gap between citizens and municipal administrators through data-driven intelligence.*

</div>

---

## 📌 Overview

Jan Sahayak is a state-of-the-art civic issue reporting platform. Rather than functioning as a traditional digital complaint box, it acts as an intelligent data layer for modern municipalities. It captures localized reports, utilizes artificial intelligence to triage them based on severity, and aggregates this data into actionable, predictive insights for city resource allocation.

Modern municipalities suffer from reactive maintenance. Citizens report potholes, broken streetlights, or waste accumulation, and authorities dispatch resources inefficiently. **Jan Sahayak shifts this paradigm from reactive to proactive.** By analyzing community-sourced data patterns, it allows city administrators to identify geographic hotspots and recurring infrastructure failures before they escalate.

---

## ✨ Key Features

* **Artificial Intelligence Triage:**
  User uploads (including video formats) are analyzed by a custom Google Gemini pipeline. The system automatically categorizes the issue and assigns a 1-5 severity rating.
  
* **Multilingual & Inclusive Design:**
  Built-in support for multiple languages (e.g., Hindi translations via Gemini) to ensure accessibility for all demographics within the municipality.

* **Proximity Deduplication & Grouping:**
  If a citizen reports an issue within a 50-meter radius of an active report, the system intelligently merges them, converting the new report into a "+1 Grouped" badge and dynamically adjusting the severity scale.
  
* **Community Gamification & Civic Certificates:**
  A robust reputation system awards points for civic engagement. Upon reaching milestones (e.g., 50 points), citizens unlock downloadable, dynamically generated **Civic Certificates** recognizing their contributions.

* **Interactive "Before & After" Resolution Sliders:**
  When an admin resolves an issue, citizens can view a sleek, interactive slider comparing the original hazard with the finalized repair, highlighting the impact of city initiatives.

* **Administrative Command Center & Work Orders:**
  A dedicated portal for city officials to filter issues, track resolution metrics, and automatically generate **PDF Work Orders** for maintenance crews with a single click.
  
* **Predictive Impact Analytics:**
  A localized intelligence dashboard that analyzes historical data to generate resource allocation recommendations and predict infrastructure failure hotspots.

---

## 🏗️ System Architecture

The architecture is divided into four highly decoupled layers:

1. **Client Application Layer:**
   The user-facing interface, built with HTML5, CSS3, and Vanilla JavaScript. It serves the Citizen Portal for data input, the Admin Command Center for moderation, and the Impact Analytics dashboard for data visualization.

2. **Backend Services Layer:**
   A Python Flask server acts as the central router. It handles RESTful API requests, WebSocket connections for real-time updates, and processes media. OpenCV Headless is utilized to extract key frames from citizen video uploads before AI processing.

3. **Intelligence Layer:**
   Google Generative AI (Gemini Flash) powers the core logic. When an issue is uploaded, the AI parses the visual and textual data to determine the specific category, assign a severity score, and generate a concise summary.

4. **Persistence Layer:**
   A relational SQLite database managed via SQLAlchemy. It maintains the state of all issue reports, tracks gamification points for citizen profiles, and logs all community upvotes and verification data.

---

## 💻 Technology Stack

**Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js, GSAP  
**Backend:** Python, Flask, SQLAlchemy, Flask-SocketIO  
**Artificial Intelligence:** Google Generative AI (Gemini Flash)  
**Media Processing:** OpenCV Headless  

---

## 🚀 Local Deployment

Follow these steps to deploy the application in your local environment.

```bash
# 1. Clone the repository
git clone https://github.com/guptaaashrestha-jpg/Jan-Sahayak.git

# 2. Navigate to the backend directory
cd Jan-Sahayak/backend

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure Environment
# Create a .env file and add your Google Gemini API Key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 5. Execute the server
python app.py
```

Access the application locally at `http://127.0.0.1:5000/`.

---

<div align="center">
  <b>The Future of Urban Maintenance</b><br>
  <i>Jan Sahayak does not just repair the city, it understands it.</i>
</div>
