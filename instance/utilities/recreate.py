import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from application import create_app, db
from application.models import setup_models

app = create_app()

with app.app_context():
    # We call setup_models here to ensure every class is registered
    # to the 'db' metadata before create_all is triggered.
    setup_models()

    print("Dropping all tables...")
    db.drop_all()

    print("Creating all tables...")
    db.create_all()
    print("Database recreated successfully!")