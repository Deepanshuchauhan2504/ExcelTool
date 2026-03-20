---
title: Excel Analysis & Data Merge Tool
emoji: 📊
colorFrom: blue
colorTo: green
sdk: streamlit
app_file: src/main.py
pinned: false
---

# 🚀 Excel Analysis & Reporting Tool

A fast, interactive web application built with Streamlit and Polars for lightning-fast Excel and CSV data analysis, visualization, and automated reporting.

## ✨ Features

- **⚡ Blazing Fast Data Processing**: Powered by `Polars` for handling large datasets efficiently.
- **📂 Easy Data Management**: 
  - Drag-and-drop file uploads (XLSX, XLS, CSV).
  - Recent file history for quick access.
- **🔍 Advanced Filtering**: Dynamic UI filters that update your metrics and charts in real-time.
- **📊 Interactive Visualizations**:
  - Customizable Pie Charts, Bar Charts, Line Charts, and Scatter Plots using `Plotly`.
  - Smart defaults (prefers Pie charts for categorical data).
- **🔢 Automated Summaries**:
  - Real-time row counts (total vs. filtered).
  - Numeric columns summation.
  - Categorical value counting.
- **📄 Professional Reporting**: Generate and download comprehensive HTML reports including your current metrics and charts.
- **📦 Standalone Executable**: Can be bundled into a single `.exe` file for sharing without requiring Python.

## 🛠️ Tech Stack

- **Frontend/UI**: [Streamlit](https://streamlit.io/)
- **Data Engine**: [Polars](https://pola.rs/)
- **Charts**: [Plotly](https://plotly.com/python/)
- **Reporting**: [Jinja2](https://jinja.palletsprojects.com/)
- **Bundling**: [PyInstaller](https://pyinstaller.org/)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ExcelTool.git
   cd ExcelTool
   ```
2. Create or activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
```bash
streamlit run src/main.py
```

## 📦 Building Standalone Executable
To create a portable `.exe` for Windows:
1. Run the build script:
   ```bash
   python build.py
   ```
2. Find your executable in the `dist/` folder.

## 🤝 Contributing
Feel free to open issues or submit pull requests to improve the tool!

---
Made with ❤️ for data analysts.
