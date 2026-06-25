Jan Sahayak
Intelligent Civic Reporting and Predictive Urban Analytics

Overview
Jan Sahayak is a data-driven civic issue reporting platform built to bridge the gap between citizens and municipal administrators. Rather than simply functioning as a digital complaint box, Jan Sahayak acts as an intelligent data layer. It captures localized reports, utilizes artificial intelligence to triage and categorize them based on severity, and aggregates this data into actionable, predictive insights for city resource allocation.

Core Concept
Modern municipalities suffer from reactive maintenance. Citizens report potholes, broken streetlights, or waste accumulation, and authorities dispatch resources inefficiently. Jan Sahayak shifts this paradigm from reactive to proactive. By analyzing community-sourced data patterns, it allows city administrators to identify geographic hotspots and recurring infrastructure failures before they escalate.

Key Features
1. Artificial Intelligence Triage: User uploads (including video formats, which are automatically parsed into frames) are analyzed by a custom Google Gemini pipeline. The system automatically categorizes the issue and assigns a 1-5 severity rating.
2. Proximity Deduplication: If a citizen reports an issue within 300 meters of an active report, the system intelligently merges them, converting the new report into an "upvote" for the existing one.
3. Community Gamification: A robust reputation system awards points for civic engagement. Citizens earn points by filing reports, verifying others' reports, and contributing to discussions.
4. Administrative Command Center: A dedicated portal for city officials to filter issues by severity, track resolution metrics, and flag spam.
5. Predictive Impact Analytics: A localized intelligence dashboard that analyzes historical data to generate resource allocation recommendations.

System Architecture

The architecture is divided into four main layers:

Client Application Layer
The user-facing interface, built with HTML5, CSS3, and Vanilla JavaScript. It serves the Citizen Portal for data input, the Admin Command Center for moderation, and the Impact Analytics dashboard for data visualization.

Backend Services Layer
A Python Flask server acts as the central router. It handles RESTful API requests, WebSocket connections for real-time updates, and processes media. OpenCV Headless is utilized to extract key frames from citizen video uploads before AI processing.

Intelligence Layer
Google Generative AI (Gemini Flash) powers the core logic. When an issue is uploaded, the AI parses the visual and textual data to determine the specific category, assign a severity score, and generate a concise summary. It also analyzes aggregated historical data to predict geographic hotspots.

Persistence Layer
A relational SQLite database managed via SQLAlchemy. It maintains the state of all issue reports, tracks gamification points for citizen profiles, and logs all community upvotes and verification data.

Technology Stack
Frontend: HTML5, CSS3, Vanilla JavaScript, Chart.js, GSAP
Backend: Python, Flask, SQLAlchemy, Flask-SocketIO
Artificial Intelligence: Google Generative AI (Gemini Flash)
Geospatial: Leaflet, CartoDB Maps
Media Processing: OpenCV Headless

Local Deployment
1. Clone the repository.
2. Navigate to the backend directory.
3. Install dependencies via pip install -r requirements.txt.
4. Create a .env file in the backend directory containing your GEMINI_API_KEY.
5. Execute python app.py.
6. Access the application locally on port 5000.

The Future of Urban Maintenance
Jan Sahayak does not just repair the city; it understands it. By turning scattered civic complaints into a unified intelligence grid, it empowers communities to build smarter, more responsive environments.
