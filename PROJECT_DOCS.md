# ExcelTool Architecture & UML Diagrams

This document provides a technical overview of the Excel Analysis Tool using UML diagrams. It covers the static structure (Class Diagram) and dynamic behavior (Sequence Diagrams).

## 1. Class Diagram

The Class Diagram illustrates the main components of the application and their relationships.

```mermaid
classDiagram
    direction TB

    class MainApp {
        +run()
        -session_state: dict
    }

    class DataManager {
        +df: Polars.DataFrame
        +history: List[dict]
        +current_file_path: str
        +DATA_DIR: str
        +HISTORY_FILE: str
        +save_and_load(file)
        +load_from_path(path)
        +apply_filters(filters)
        +get_column_metadata()
        +get_history()
        +remove_from_history(path)
        -_ensure_data_dir()
        -_load_history()
        -_save_history()
        -_update_history(path)
    }

    class ReportEngine {
        +generate_report(df, filename, figures, metrics)
        -TEMPLATE: str
    }

    class UiFilters {
        +render_filters(data_manager)
    }

    class UiCharts {
        +render_charts(data_manager, filtered_df, active_charts)
    }

    %% Relationships
    MainApp --> DataManager : Initializes & Uses
    MainApp --> ReportEngine : Initializes & Uses
    MainApp ..> UiFilters : Calls
    MainApp ..> UiCharts : Calls
    
    UiFilters ..> DataManager : Reads Metadata
    UiCharts ..> DataManager : Reads Metadata
    
    ReportEngine ..> DataManager : Uses DataFrame (passed indirectly)
```

### Component Description
- **MainApp (`main.py`)**: The entry point and controller. It manages the Streamlit session state and orchestrates the UI layout.
- **DataManager (`src/core/data_manager.py`)**: The core logic provider. It handles file I/O, manages the data using Polars, maintains file history, and provides filtering capabilities.
- **ReportEngine (`src/core/report_engine.py`)**: Responsible for generating the standalone HTML report. It takes the processed data and visualizations and renders them into a template.
- **UiFilters (`src/ui/filters.py`)**: A functional module that renders the sidebar filters based on the data columns.
- **UiCharts (`src/ui/charts.py`)**: A functional module that handles the creation and rendering of Plotly charts based on user selection.

---

## 2. Sequence Diagrams

### 2.1 File Loading Workflow
This diagram shows what happens when a user uploads a new file.

```mermaid
sequenceDiagram
    actor User
    participant Main as MainApp
    participant DM as DataManager
    participant FS as FileSystem

    User->>Main: Uploads Excel/CSV File
    Main->>DM: save_and_load(uploaded_file)
    activate DM
    DM->>FS: Write File to /data
    DM->>DM: load_from_path(file_path)
    activate DM
    DM->>FS: Read File (Polars)
    DM->>DM: _update_history(file_path)
    DM->>FS: Save History JSON
    deactivate DM
    DM-->>Main: Success, Message
    deactivate DM
    Main->>Main: st.rerun()
```

### 2.2 Filtering Data Workflow
How data is filtered and updated in the UI.

```mermaid
sequenceDiagram
    actor User
    participant Main as MainApp
    participant Filters as UiFilters
    participant DM as DataManager

    Main->>Filters: render_filters(dm)
    activate Filters
    Filters->>DM: get_column_metadata()
    DM-->>Filters: Column Types & Ranges
    Filters-->>User: Display Filter Widgets
    deactivate Filters
    
    User->>Main: Adjusts Filter (e.g., Select "NY")
    Main->>DM: apply_filters(active_filters)
    activate DM
    DM->>DM: Construct Polars Query
    DM-->>Main: Return Filtered DataFrame
    deactivate DM
    
    Main->>Main: Update Metrics & Charts
```

### 2.3 Report Generation Workflow
How the HTML report is created.

```mermaid
sequenceDiagram
    actor User
    participant Main as MainApp
    participant RE as ReportEngine
    participant Browser

    User->>Main: Click "Generate HTML Report"
    Main->>Main: Capture Metrics (Rows, Sums)
    Main->>Main: Capture Figures (Plotly)
    
    Main->>RE: generate_report(filtered_df, filename, figures, metrics)
    activate RE
    RE->>RE: Convert Charts to HTML
    RE->>RE: Generate Data Table HTML
    RE->>RE: Render Jinja2 Template
    RE-->>Main: Return HTML String
    deactivate RE
    
    Main->>Browser: Provide Download Button
    User->>Browser: Download .html File
```

---

## 3. High-Level System Flow

This flowchart represents the user journey and data processing loop within the application.

```mermaid
flowchart TD
    Start([Start Application]) --> CheckHistory{"History Exists?"}
    
    CheckHistory -- "Yes" --> ShowHistory["Show Recent Files"]
    CheckHistory -- "No" --> Upload["Wait for Upload"]
    
    ShowHistory --> |"Select File"| LoadData["Load Data (Polars)"]
    Upload --> |"File Uploaded"| SaveToDisk["Save to /data"]
    SaveToDisk --> LoadData
    
    LoadData --> RenderUI["Render UI & Sidebar"]
    
    RenderUI --> DefineFilters["User Applies Filters"]
    DefineFilters --> FilterData["Filter DataFrame"]
    
    FilterData --> DisplayMetrics["Show Rows & Metrics"]
    FilterData --> DisplayCharts["Render Plotly Charts"]
    
    DisplayMetrics --> Action{"User Action"}
    DisplayCharts --> Action
    
    Action -- "Add Chart" --> UpdateCharts["Update Session State"] --> DisplayCharts
    Action -- "Generate Report" --> GenReport["Generate HTML Report"] --> Download["Download Artifact"]
    Action -- "Change Filter" --> DefineFilters
    Action -- "Upload New" --> Upload
```
