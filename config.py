import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8028105170

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
PARTICIPANTS_FILE = os.path.join(STORAGE_DIR, "participants.xlsx")

TEMPLATE_FILES = {
    "32-8": os.path.join(TEMPLATES_DIR, "32-8.xlsx"),
    "32-16": os.path.join(TEMPLATES_DIR, "32-16.xlsx"),
    "64-16": os.path.join(TEMPLATES_DIR, "64-16.xlsx"),
    "64-32": os.path.join(TEMPLATES_DIR, "64-32.xlsx"),
    "128-32": os.path.join(TEMPLATES_DIR, "128-32.xlsx"),
    "128-64": os.path.join(TEMPLATES_DIR, "128-64.xlsx"),
    "256-64": os.path.join(TEMPLATES_DIR, "256-64.xlsx"),
    "256-128": os.path.join(TEMPLATES_DIR, "256-128.xlsx"),
}