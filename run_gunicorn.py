# run_gunicorn.py
import os
import sys
from dotenv import load_dotenv
from subprocess import run

# Get environment from command line arguments
env_file = '.env.' + (sys.argv[1] if len(sys.argv) > 1 else 'production')

# Load environment variables from the specified .env file
load_dotenv(env_file)

# Run gunicorn
run(["gunicorn", "PoppinBackend.wsgi:application", "--bind", "0.0.0.0:8000"])
