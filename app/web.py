from . import create_app

def main():
    import os
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=os.getenv("FLASK_DEBUG", "0") == "1")

if __name__ == "__main__":
    main()
