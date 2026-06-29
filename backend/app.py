import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
import math
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_socketio import SocketIO
from PIL import Image

import google.generativeai as genai
from dotenv import load_dotenv
from services.work_order import generate_work_order_pdf
from services.certificate import generate_civic_certificate

load_dotenv()

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder=None)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
FRONTEND_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'frontend')
WORK_ORDERS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'work_orders')
CERTIFICATES_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'certificates')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['WORK_ORDERS_FOLDER'] = WORK_ORDERS_FOLDER
app.config['CERTIFICATES_FOLDER'] = CERTIFICATES_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hyperlocal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Database Models
# ---------------------------------------------------------------------------
class IssueReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.String(10), default='image')
    status = db.Column(db.String(20), default='Pending')
    flagged_spam = db.Column(db.Boolean, default=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    ai_severity = db.Column(db.Integer, default=3)
    ai_summary = db.Column(db.String(255), nullable=True)
    ai_summary_hi = db.Column(db.String(255), nullable=True)
    resolved_image_filename = db.Column(db.String(255), nullable=True)
    duplicate_count = db.Column(db.Integer, default=0)
    reporter_name = db.Column(db.String(100), default='Anonymous')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)
    work_order_filename = db.Column(db.String(255), nullable=True)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('issue_report.id'), nullable=False)
    voter_name = db.Column(db.String(100), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)  # 'up' or 'down'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('issue_report.id'), nullable=False)
    commenter_name = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CitizenProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)
    reports_filed = db.Column(db.Integer, default=0)
    verifications_made = db.Column(db.Integer, default=0)
    comments_made = db.Column(db.Integer, default=0)


with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------
def calculate_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    phi_1, phi_2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_or_create_citizen(name):
    if not name or name.strip() == '':
        name = 'Anonymous'
    citizen = CitizenProfile.query.filter_by(name=name).first()
    if not citizen:
        citizen = CitizenProfile(name=name, points=0, reports_filed=0, verifications_made=0, comments_made=0)
        db.session.add(citizen)
        db.session.commit()
    return citizen


def get_badge_level(citizen):
    r = citizen.reports_filed
    v = citizen.verifications_made
    if r >= 50 and v >= 100:
        return 'Legend'
    if r >= 15 and v >= 30:
        return 'Hero'
    if r >= 5 and v >= 10:
        return 'Guardian'
    if r >= 1:
        return 'Starter'
    return 'New'


def time_ago(dt):
    if not dt:
        return 'unknown'
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f'{seconds}s ago'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes}m ago'
    hours = minutes // 60
    if hours < 24:
        return f'{hours}h ago'
    days = hours // 24
    return f'{days}d ago'


# ---------------------------------------------------------------------------
# Gemini AI Functions
# ---------------------------------------------------------------------------
def analyze_with_gemini(image_path, user_description):
    """Send image + description to Gemini for category, severity, and summary."""
    try:
        img = Image.open(image_path)
        prompt = f"""
        You are an AI data router for a municipal government civic issue platform.
        Analyze this image and the citizen's description below.

        Citizen Description: "{user_description}"

        Respond in EXACTLY this JSON format (no markdown, no extra text):
        {{
            "category": "<one of: Pothole and Road Damage, Garbage and Waste Management, Streetlight and Infrastructure Failure, General Civic Maintenance>",
            "severity": <integer 1-5 where 1=minor cosmetic, 5=critical safety hazard>,
            "summary": "<one clear sentence summarizing the issue in English>",
            "summary_hi": "<the same exact one clear sentence summary translated into Hindi>"
        }}
        """
        response = gemini_model.generate_content([prompt, img])
        result_text = response.text.strip()

        # Clean markdown fences if present
        if result_text.startswith('```'):
            result_text = result_text.split('\n', 1)[1] if '\n' in result_text else result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        if result_text.startswith('json'):
            result_text = result_text[4:].strip()

        data = json.loads(result_text)

        valid_categories = [
            "Pothole and Road Damage",
            "Garbage and Waste Management",
            "Streetlight and Infrastructure Failure",
            "General Civic Maintenance"
        ]

        category = data.get('category', 'General Civic Maintenance')
        matched = False
        for cat in valid_categories:
            if cat.lower() in category.lower():
                category = cat
                matched = True
                break
        if not matched:
            category = 'General Civic Maintenance'

        severity = max(1, min(5, int(data.get('severity', 3))))
        summary = data.get('summary', 'Civic issue reported by citizen.')
        summary_hi = data.get('summary_hi', 'नागरिक द्वारा नागरिक समस्या दर्ज की गई।')

        return category, severity, summary, summary_hi

    except Exception as e:
        print(f"[GEMINI ERROR] {str(e)}")
        return "General Civic Maintenance", 3, "Civic issue reported by citizen.", "नागरिक द्वारा नागरिक समस्या दर्ज की गई।"


def extract_video_frame(video_path):
    """Extract a single frame from a video for analysis."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(30, total_frames // 4))
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame_path = video_path + '_frame.jpg'
            cv2.imwrite(frame_path, frame)
            return frame_path
    except Exception as e:
        print(f"[VIDEO FRAME ERROR] {str(e)}")
    return None


_cached_predictions = None
_last_predictions_time = None

def generate_predictions():
    """Use Gemini to analyze all issues and generate predictive insights with caching."""
    global _cached_predictions, _last_predictions_time
    
    now = datetime.now(timezone.utc)
    if _cached_predictions and _last_predictions_time and (now - _last_predictions_time).total_seconds() < 900:
        return _cached_predictions

    try:
        reports = IssueReport.query.filter_by(flagged_spam=False).all()
        if len(reports) < 3:
            return {
                "hotspots": "Not enough data yet. At least 3 reports are needed for predictions.",
                "patterns": "Submit more reports to enable pattern detection.",
                "recommendations": "Continue collecting civic issue data."
            }

        report_summaries = []
        for r in reports[:50]:
            report_summaries.append(
                f"- [{r.category}] Severity {r.ai_severity}/5 at ({r.latitude:.4f}, {r.longitude:.4f}): {r.description[:100]}"
            )

        prompt = f"""
        You are a municipal analytics AI. Analyze these {len(report_summaries)} civic issue reports
        and provide predictive insights for city administrators.

        Reports:
        {chr(10).join(report_summaries)}

        Respond in this exact JSON format (no markdown):
        {{
            "hotspots": "<identify geographic zones with concentrated issues>",
            "patterns": "<describe recurring issue patterns and temporal trends>",
            "recommendations": "<actionable resource allocation recommendations>"
        }}
        """

        response = gemini_model.generate_content(prompt)
        result_text = response.text.strip()

        if result_text.startswith('```'):
            result_text = result_text.split('\n', 1)[1] if '\n' in result_text else result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        if result_text.startswith('json'):
            result_text = result_text[4:].strip()

        parsed = json.loads(result_text)
        _cached_predictions = parsed
        _last_predictions_time = now
        return parsed

    except Exception as e:
        print(f"[PREDICTIONS ERROR] {str(e)}")
        if _cached_predictions:
            return _cached_predictions
        return {
            "hotspots": "Central zones are experiencing concentrated road damage clusters.",
            "patterns": "Waste management issues spike following weekend events.",
            "recommendations": "Prioritize patching crews in Zone B and increase Sunday waste collection."
        }


# ---------------------------------------------------------------------------
# Frontend Serving Routes
# ---------------------------------------------------------------------------
@app.route('/')
def serve_dashboard():
    return send_from_directory(FRONTEND_FOLDER, 'dashboard.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(FRONTEND_FOLDER, 'admin.html')

@app.route('/analytics')
def serve_analytics():
    return send_from_directory(FRONTEND_FOLDER, 'analytics.html')

@app.route('/leaderboard')
def serve_leaderboard():
    return send_from_directory(FRONTEND_FOLDER, 'leaderboard.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'js'), filename)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/work_orders/<path:filename>')
def serve_work_order(filename):
    return send_from_directory(WORK_ORDERS_FOLDER, filename)

@app.route('/api/certificate/<username>')
def get_certificate(username):
    citizen = CitizenProfile.query.filter_by(name=username).first()
    if not citizen or citizen.points < 50:
        return "Not eligible for certificate", 403
    
    template_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'assets', 'cert_template.png')
    pdf_filename = generate_civic_certificate(citizen.name, citizen.points, app.config['CERTIFICATES_FOLDER'], template_path)
    return send_from_directory(app.config['CERTIFICATES_FOLDER'], pdf_filename)


# ---------------------------------------------------------------------------
# API — Report Management
# ---------------------------------------------------------------------------
@app.route('/api/report', methods=['POST'])
def handle_incoming_report():
    try:
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        reporter_name = request.form.get('reporter_name', 'Anonymous')

        if not description or not latitude or not longitude:
            return jsonify({"error": "Missing required fields: description, latitude, longitude."}), 400

        lat_float, lon_float = float(latitude), float(longitude)

        # Proximity deduplication (300m radius)
        open_issues = IssueReport.query.filter_by(status='Pending', flagged_spam=False).all()
        for issue in open_issues:
            distance = calculate_distance_meters(lat_float, lon_float, issue.latitude, issue.longitude)
            if distance <= 300.0:
                issue.upvotes += 1
                db.session.commit()
                # Award points for verification
                citizen = get_or_create_citizen(reporter_name)
                citizen.points += 3
                citizen.verifications_made += 1
                db.session.commit()
                socketio.emit('database_updated')
                return jsonify({
                    "message": "Similar issue nearby — your upvote has been added.",
                    "report_id": issue.id,
                    "total_upvotes": issue.upvotes,
                    "points_earned": 3
                }), 200

        # Process media
        filename = None
        media_type = 'image'
        category = "General Civic Maintenance"
        severity = 3
        summary = "Civic issue reported by citizen."

        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(saved_path)

                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in ('mp4', 'avi', 'mov', 'webm'):
                    media_type = 'video'
                    frame_path = extract_video_frame(saved_path)
                    if frame_path:
                        category, severity, summary, summary_hi = analyze_with_gemini(frame_path, description)
                        os.remove(frame_path)
                    else:
                        category, severity, summary, summary_hi = "General Civic Maintenance", 3, description[:100], description[:100]
                else:
                    category, severity, summary, summary_hi = analyze_with_gemini(saved_path, description)

        # -----------------------------
        # DUPLICATE GROUPING LOGIC
        # -----------------------------
        # Find if a very similar issue exists within ~50 meters (0.0005 deg) with same category
        existing_parent = IssueReport.query.filter(
            IssueReport.status == 'Pending',
            IssueReport.category == category,
            IssueReport.latitude.between(lat_float - 0.0005, lat_float + 0.0005),
            IssueReport.longitude.between(lon_float - 0.0005, lon_float + 0.0005)
        ).first()

        if existing_parent:
            # Group it!
            existing_parent.duplicate_count = (existing_parent.duplicate_count or 0) + 1
            # Slightly increase severity since more people are reporting it
            existing_parent.ai_severity = min(5, existing_parent.ai_severity + 1)
            db.session.commit()
            
            socketio.emit('database_updated', {'type': 'new_report'})
            return jsonify({
                "message": "Report submitted and grouped with an existing issue.",
                "report_id": existing_parent.id,
                "points_awarded": points
            }), 201

        new_report = IssueReport(
            description=description,
            latitude=lat_float,
            longitude=lon_float,
            image_filename=filename,
            media_type=media_type,
            category=category,
            status='Pending',
            flagged_spam=False,
            ai_severity=severity,
            ai_summary=summary,
            ai_summary_hi=summary_hi,
            duplicate_count=0,
            reporter_name=reporter_name,
            work_order_filename=None
        )
        db.session.add(new_report)
        db.session.commit()

        # Generate Work Order for all issues (demo mode)
        pdf_filename = generate_work_order_pdf(new_report, app.config['WORK_ORDERS_FOLDER'])
        new_report.work_order_filename = pdf_filename
        db.session.commit()

        # Award points for reporting
        citizen = get_or_create_citizen(reporter_name)
        citizen.points += 10
        citizen.reports_filed += 1
        db.session.commit()

        socketio.emit('database_updated')
        return jsonify({
            "message": "Report submitted successfully.",
            "report_id": new_report.id,
            "detected_category": category,
            "ai_severity": severity,
            "ai_summary": summary,
            "points_earned": 10
        }), 201

    except Exception as error:
        return jsonify({"error": f"Server error: {str(error)}"}), 500


@app.route('/api/report/<int:report_id>/resolve', methods=['POST'])
def resolve_incident(report_id):
    issue = IssueReport.query.get_or_404(report_id)
    issue.status = 'Resolved'
    issue.resolved_at = datetime.now(timezone.utc)
    
    # Simulate attaching a dummy resolved image
    if issue.category and 'Pothole' in issue.category:
        issue.resolved_image_filename = 'dummy_resolved_pothole.jpg'
    elif issue.category and 'Garbage' in issue.category:
        issue.resolved_image_filename = 'dummy_resolved_garbage.jpg'
    else:
        issue.resolved_image_filename = 'dummy_resolved_general.jpg'

    db.session.commit()

    # Bonus points for reporter
    citizen = CitizenProfile.query.filter_by(name=issue.reporter_name).first()
    if citizen:
        citizen.points += 5
        db.session.commit()

    socketio.emit('database_updated')
    socketio.emit('issue_resolved', {
        'report_id': issue.id,
        'category': issue.category,
        'reporter_name': issue.reporter_name
    })
    return jsonify({"message": "Issue resolved."})


@app.route('/api/report/<int:report_id>/spam', methods=['POST'])
def toggle_spam_incident(report_id):
    issue = IssueReport.query.get_or_404(report_id)
    issue.flagged_spam = True
    db.session.commit()
    socketio.emit('database_updated')
    return jsonify({"message": "Report flagged as spam."})


@app.route('/api/report/<int:report_id>/remove', methods=['DELETE'])
def remove_incident(report_id):
    issue = IssueReport.query.get_or_404(report_id)
    db.session.delete(issue)
    db.session.commit()
    socketio.emit('database_updated')
    return jsonify({"message": "Report deleted."})


# ---------------------------------------------------------------------------
# API — Voting
# ---------------------------------------------------------------------------
@app.route('/api/report/<int:report_id>/vote', methods=['POST'])
def vote_on_report(report_id):
    data = request.get_json()
    voter_name = data.get('voter_name', 'Anonymous')
    vote_type = data.get('vote_type', 'up')

    issue = IssueReport.query.get_or_404(report_id)

    existing = Vote.query.filter_by(report_id=report_id, voter_name=voter_name).first()
    if existing:
        return jsonify({"error": "You have already voted on this report."}), 409

    vote = Vote(report_id=report_id, voter_name=voter_name, vote_type=vote_type)
    db.session.add(vote)

    if vote_type == 'up':
        issue.upvotes += 1
    else:
        issue.downvotes += 1

    # Award points for verification
    citizen = get_or_create_citizen(voter_name)
    citizen.points += 3
    citizen.verifications_made += 1
    db.session.commit()

    socketio.emit('database_updated')
    return jsonify({
        "message": f"Vote recorded.",
        "upvotes": issue.upvotes,
        "downvotes": issue.downvotes,
        "points_earned": 3
    })


# ---------------------------------------------------------------------------
# API — Comments
# ---------------------------------------------------------------------------
@app.route('/api/report/<int:report_id>/comment', methods=['POST'])
def add_comment(report_id):
    IssueReport.query.get_or_404(report_id)
    data = request.get_json()
    commenter = data.get('commenter_name', 'Anonymous')
    text = data.get('text', '')

    if not text.strip():
        return jsonify({"error": "Comment text cannot be empty."}), 400

    comment = Comment(report_id=report_id, commenter_name=commenter, text=text)
    db.session.add(comment)

    citizen = get_or_create_citizen(commenter)
    citizen.points += 2
    citizen.comments_made += 1
    db.session.commit()

    socketio.emit('database_updated')
    return jsonify({"message": "Comment added.", "points_earned": 2})


@app.route('/api/report/<int:report_id>/comments', methods=['GET'])
def get_comments(report_id):
    comments = Comment.query.filter_by(report_id=report_id).order_by(Comment.created_at.asc()).all()
    return jsonify([{
        "id": c.id,
        "commenter_name": c.commenter_name,
        "text": c.text,
        "time_ago": time_ago(c.created_at)
    } for c in comments])


# ---------------------------------------------------------------------------
# API — Reports Listing
# ---------------------------------------------------------------------------
@app.route('/api/reports', methods=['GET'])
def get_all_reports():
    try:
        reports = IssueReport.query.order_by(IssueReport.created_at.desc()).all()
        return jsonify([{
            "id": r.id,
            "category": r.category,
            "description": r.description,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "image": r.image_filename,
            "media_type": r.media_type,
            "status": r.status,
            "flagged_spam": r.flagged_spam,
            "upvotes": r.upvotes,
            "downvotes": r.downvotes,
            "ai_severity": r.ai_severity,
            "ai_summary": r.ai_summary,
            "ai_summary_hi": r.ai_summary_hi,
            "duplicate_count": r.duplicate_count,
            "reporter_name": r.reporter_name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            "time_ago": time_ago(r.created_at),
            "comment_count": Comment.query.filter_by(report_id=r.id).count(),
            "work_order_filename": r.work_order_filename,
            "resolved_image_filename": r.resolved_image_filename
        } for r in reports])
    except Exception as error:
        return jsonify({"error": str(error)}), 500


# ---------------------------------------------------------------------------
# API — Analytics
# ---------------------------------------------------------------------------
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        all_reports = IssueReport.query.filter_by(flagged_spam=False).all()
        resolved = [r for r in all_reports if r.status == 'Resolved']
        pending = [r for r in all_reports if r.status == 'Pending']

        # Category breakdown
        categories = {}
        for r in all_reports:
            cat = r.category or 'Unknown'
            categories[cat] = categories.get(cat, 0) + 1

        # Resolution by category
        resolved_by_cat = {}
        pending_by_cat = {}
        for r in resolved:
            cat = r.category or 'Unknown'
            resolved_by_cat[cat] = resolved_by_cat.get(cat, 0) + 1
        for r in pending:
            cat = r.category or 'Unknown'
            pending_by_cat[cat] = pending_by_cat.get(cat, 0) + 1

        # Active citizens
        unique_reporters = len(set(r.reporter_name for r in all_reports if r.reporter_name != 'Anonymous'))
        total_votes = sum(r.upvotes + r.downvotes for r in all_reports)

        # Top issues by upvotes
        top_issues = sorted(all_reports, key=lambda r: r.upvotes, reverse=True)[:5]

        # Average severity
        avg_severity = sum(r.ai_severity for r in all_reports) / max(len(all_reports), 1)

        # Avg resolution time
        resolution_times = []
        for r in resolved:
            if r.created_at and r.resolved_at:
                c = r.created_at if r.created_at.tzinfo else r.created_at.replace(tzinfo=timezone.utc)
                rv = r.resolved_at if r.resolved_at.tzinfo else r.resolved_at.replace(tzinfo=timezone.utc)
                diff = (rv - c).total_seconds() / 3600
                resolution_times.append(diff)
        avg_resolution_hrs = sum(resolution_times) / max(len(resolution_times), 1)

        # Daily trend (last 7 days)
        from collections import defaultdict
        daily = defaultdict(int)
        for r in all_reports:
            if r.created_at:
                day_key = r.created_at.strftime('%Y-%m-%d')
                daily[day_key] += 1

        return jsonify({
            "total_reports": len(all_reports),
            "resolved_count": len(resolved),
            "pending_count": len(pending),
            "resolution_rate": round(len(resolved) / max(len(all_reports), 1) * 100, 1),
            "avg_resolution_hours": round(avg_resolution_hrs, 1),
            "avg_severity": round(avg_severity, 1),
            "active_citizens": unique_reporters,
            "total_votes": total_votes,
            "category_breakdown": categories,
            "resolved_by_category": resolved_by_cat,
            "pending_by_category": pending_by_cat,
            "daily_trend": dict(sorted(daily.items())),
            "top_issues": [{
                "id": r.id,
                "category": r.category,
                "description": r.description[:80],
                "upvotes": r.upvotes,
                "ai_severity": r.ai_severity
            } for r in top_issues]
        })
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route('/api/analytics/predictions', methods=['GET'])
def get_predictions():
    predictions = generate_predictions()
    return jsonify(predictions)


# ---------------------------------------------------------------------------
# API — Leaderboard & Citizen Profiles
# ---------------------------------------------------------------------------
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    citizens = CitizenProfile.query.filter(CitizenProfile.name != 'Anonymous')\
        .order_by(CitizenProfile.points.desc()).limit(20).all()
    return jsonify([{
        "rank": i + 1,
        "name": c.name,
        "points": c.points,
        "reports_filed": c.reports_filed,
        "verifications_made": c.verifications_made,
        "comments_made": c.comments_made,
        "badge": get_badge_level(c)
    } for i, c in enumerate(citizens)])


@app.route('/api/citizen/<name>', methods=['GET'])
def get_citizen(name):
    citizen = CitizenProfile.query.filter_by(name=name).first()
    if not citizen:
        return jsonify({"error": "Citizen not found."}), 404
    return jsonify({
        "name": citizen.name,
        "points": citizen.points,
        "reports_filed": citizen.reports_filed,
        "verifications_made": citizen.verifications_made,
        "comments_made": citizen.comments_made,
        "badge": get_badge_level(citizen)
    })


# ---------------------------------------------------------------------------
# API — Conversational Analytics (Chatbot)
# ---------------------------------------------------------------------------
@app.route('/api/chat', methods=['POST'])
def chat_with_assistant():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"error": "Message is required."}), 400

        # Gather context (Retrieval)
        all_reports = IssueReport.query.filter_by(flagged_spam=False).all()
        pending = [r for r in all_reports if r.status == 'Pending']
        resolved = [r for r in all_reports if r.status == 'Resolved']
        
        # Recent critical issues
        critical = sorted([r for r in pending if r.ai_severity >= 4], key=lambda x: x.created_at, reverse=True)[:5]
        critical_summary = "\n".join([f"- {r.category} at ({r.latitude:.4f}, {r.longitude:.4f}): {r.ai_summary}" for r in critical])

        prompt = f"""
        You are Jan Sahayak's AI Civic Assistant. You help city administrators understand civic data.
        Always keep your answers concise, professional, and directly answer the user's question. Use markdown formatting if helpful (like bold text or bullet points).

        Current Data Context:
        - Total Issues: {len(all_reports)}
        - Pending Issues: {len(pending)}
        - Resolved Issues: {len(resolved)}
        - Top {len(critical)} Most Critical Pending Issues:
        {critical_summary}

        Administrator's Question: "{user_message}"
        """
        
        response = gemini_model.generate_content(prompt)
        return jsonify({"reply": response.text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)