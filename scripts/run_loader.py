import os
import sys
from streamlit.web import cli as stcli

def main():
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        # sys._MEIPASS is the temp directory where PyInstaller bundles files
        base_path = sys._MEIPASS
        app_path = os.path.join(base_path, "src", "main.py")
    else:
        # Running from source
        app_path = os.path.join(os.getcwd(), "src", "main.py")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=false",
    ]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
