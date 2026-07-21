import os
import sys
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(WORKSPACE_DIR)

from backend.models.database import SessionLocal
from backend.services.reports import generate_excel_report

db = SessionLocal()
try:
    print("Testing Excel report generation for user_id = 1...")
    path = generate_excel_report(1, db)
    print("SUCCESS! Excel generated at:", path)
except Exception as e:
    import traceback
    traceback.print_exc()
