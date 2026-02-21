import PyInstaller.__main__
import os

def build():
    print("Starting build process...")
    
    args = [
        'scripts/run_loader.py',
        '--name=ExcelTool',
        '--onefile',
        '--clean',
        '--noconfirm',
        # Include source directory
        '--add-data=src;src',
        # Collect necessary packages
        '--collect-all=streamlit',
        '--collect-all=polars',
        '--collect-all=plotly',
        '--collect-all=xlsxwriter',
        '--collect-all=kaleido',
        '--collect-all=fastexcel',
        # Ensure hidden imports are found
        '--hidden-import=streamlit',
        '--hidden-import=polars',
        '--hidden-import=fastexcel',
        # Metadata
        '--icon=NONE', # Can add icon later if available
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    print("Build complete.")

if __name__ == "__main__":
    build()
