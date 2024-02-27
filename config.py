import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

DB_USER = os.getenv('DB_USER')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

SQLALCHEMY_DATABASE_URI = 'postgresql://{0}@{1}:5432/{2}'.format(DB_USER, DB_HOST, DB_NAME)
