"""
BuildTech Server Runner (Flask Development Server)
"""
from app.main import app

if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)
