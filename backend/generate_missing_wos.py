from app import app, db, IssueReport, WORK_ORDERS_FOLDER
from services.work_order import generate_work_order_pdf

def retro_generate():
    with app.app_context():
        issues = IssueReport.query.all()
        count = 0
        for issue in issues:
            if not issue.work_order_filename:
                pdf_filename = generate_work_order_pdf(issue, WORK_ORDERS_FOLDER)
                issue.work_order_filename = pdf_filename
                count += 1
        db.session.commit()
        print(f"Retroactively generated {count} Work Orders.")

if __name__ == '__main__':
    retro_generate()
