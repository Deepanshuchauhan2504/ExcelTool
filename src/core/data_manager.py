import polars as pl
import os
import json
import shutil
from datetime import datetime

class DataManager:
    """Manages data loading, filtering, and persistent file history using Polars."""
    
    DATA_DIR = "data"
    HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
    MAX_HISTORY = 5

    def __init__(self):
        self.df = None
        self.current_file_path = None
        self._ensure_data_dir()
        self.history = self._load_history()

    def _ensure_data_dir(self):
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR)
        if not os.path.exists(self.HISTORY_FILE):
            with open(self.HISTORY_FILE, "w") as f:
                json.dump([], f)

    def _load_history(self):
        try:
            with open(self.HISTORY_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_history(self):
        with open(self.HISTORY_FILE, "w") as f:
            json.dump(self.history, f, indent=4)

    def save_and_load(self, uploaded_file):
        """Saves the uploaded file to the data directory and loads it."""
        file_path = os.path.join(self.DATA_DIR, uploaded_file.name)
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return self.load_from_path(file_path)

    def load_from_path(self, file_path):
        """Loads a file from a given path and updates history."""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                self.df = pl.read_excel(file_path)
            elif file_path.endswith('.csv'):
                self.df = pl.read_csv(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            self.current_file_path = file_path
            self._update_history(file_path)
            return True, "File loaded successfully"
        except Exception as e:
            return False, f"Error loading file: {str(e)}"

    def _update_history(self, file_path):
        filename = os.path.basename(file_path)
        # Remove if already exists to move to top
        self.history = [h for h in self.history if h['path'] != file_path]
        
        # Add to top
        self.history.insert(0, {
            "name": filename,
            "path": file_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Trim history and delete physically removed files
        if len(self.history) > self.MAX_HISTORY:
            removed = self.history.pop()
            # Optional: Clean up disk if file is not in history? 
            # For now, we'll keep the files but we could delete them here.
            
        self._save_history()

    def remove_from_history(self, file_path):
        """Removes a file from history and optionally deletes it from disk."""
        self.history = [h for h in self.history if h['path'] != file_path]
        self._save_history()

    def get_history(self):
        return self.history

    def get_column_metadata(self):
        """Returns metadata for each column to build UI filters."""
        if self.df is None:
            return {}
        
        metadata = {}
        # Check if first column is "Sr. No" or similar to exclude it
        skip_first_col = False
        if self.df.columns and self.df.columns[0].lower().replace(".", "").strip() in ["sr no", "sno", "serial no"]:
            skip_first_col = True

        for idx, col in enumerate(self.df.columns):
            if idx == 0 and skip_first_col:
                continue

            dtype = self.df.schema[col]
            # Handle categorical and string-like types
            if dtype in [pl.Utf8, pl.Categorical, pl.Boolean, pl.Enum]:
                unique_vals = self.df[col].unique().to_list()
                metadata[col] = {
                    "type": "categorical",
                    "options": sorted([str(v) for v in unique_vals if v is not None])
                }
            # Handle numeric types (integers and floats)
            elif dtype.is_numeric():
                min_val = self.df[col].min()
                max_val = self.df[col].max()
                if min_val is not None and max_val is not None:
                    metadata[col] = {
                        "type": "numeric",
                        "min": float(min_val),
                        "max": float(max_val)
                    }
            # Handle date and datetime
            elif dtype in [pl.Date, pl.Datetime]:
                min_date = self.df[col].min()
                max_date = self.df[col].max()
                if min_date is not None and max_date is not None:
                    metadata[col] = {
                        "type": "date",
                        "min": min_date,
                        "max": max_date
                    }
        return metadata

    def apply_filters(self, filter_values):
        """
        Applies a dictionary of filters to the dataframe.
        filter_values: { col_name: value }
        """
        if self.df is None:
            return None

        filtered_df = self.df
        for col, val in filter_values.items():
            if val is None or val == []:
                continue
            
            dtype = self.df.schema[col]
            if isinstance(val, list) and len(val) > 0:
                # Categorical filter
                filtered_df = filtered_df.filter(pl.col(col).cast(pl.Utf8).is_in(val))
            elif isinstance(val, tuple) and len(val) == 2:
                # Numeric or Date range filter
                filtered_df = filtered_df.filter(
                    (pl.col(col) >= val[0]) & (pl.col(col) <= val[1])
                )
        
        return filtered_df
