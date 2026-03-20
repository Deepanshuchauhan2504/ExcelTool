import streamlit as st
import polars as pl
from core.data_manager import DataManager

def main():
    st.set_page_config(page_title="Excel Analysis Tool", layout="wide", page_icon="📊")
    
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    dm = st.session_state.data_manager

    # --- Navigation ---
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Choose App Mode", ["Analysis", "Data Merge & Cross-Reference", "Large Text to Excel Splitter"])
    st.sidebar.divider()

    if app_mode == "Data Merge & Cross-Reference":
        from merge_ui import render_merge_ui
        render_merge_ui()
        return
        
    if app_mode == "Large Text to Excel Splitter":
        from splitter_ui import render_splitter_ui
        render_splitter_ui()
        return

    st.title("🚀 Excel Analysis & Reporting Tool")
    
    # Sidebar for Data Management
    with st.sidebar:
        st.header("📂 Data Source")
        
        # History Popover (Watch icon simulation)
        history = dm.get_history()
        with st.popover("🕒 Recent Files", use_container_width=True):
            if history:
                for item in history:
                    col_file, col_del = st.columns([0.8, 0.2])
                    with col_file:
                        if st.button(f"📄 {item['name']}", key=f"load_{item['path']}", use_container_width=True):
                            success, msg = dm.load_from_path(item['path'])
                            if success:
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_del:
                        if st.button("🗑️", key=f"del_{item['path']}", help="Remove from history"):
                            dm.remove_from_history(item['path'])
                            st.rerun()
            else:
                st.info("No recent files.")

        st.divider()

        # File Upload
        uploaded_file = st.file_uploader("Upload New Excel or CSV", type=["xlsx", "xls", "csv"])
        if uploaded_file:
            # Check if this file is already loaded to avoid infinite reruns
            is_new_file = True
            if dm.current_file_path:
                current_filename = os.path.basename(dm.current_file_path)
                if current_filename == uploaded_file.name:
                    is_new_file = False
            
            if is_new_file:
                success, msg = dm.save_and_load(uploaded_file)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        
        st.divider()

        # Data Preprocessing Section
        if dm.df is not None:
            st.header("🛠️ Data Preprocessing")
            handle_merged = st.toggle("🔄 Handle Merged Cells", help="Automatically fills empty cells that were part of a merged row in Excel.")
            
            if handle_merged:
                # Store columns to fill in session state to persist through reruns
                if 'ffill_cols' not in st.session_state:
                    st.session_state.ffill_cols = []
                
                selected_cols = st.multiselect(
                    "Select columns to fill:", 
                    dm.df.columns,
                    default=st.session_state.ffill_cols,
                    key="ffill_col_selector"
                )
                
                if st.button("Apply Fill", use_container_width=True):
                    dm.apply_forward_fill(selected_cols)
                    st.session_state.ffill_cols = selected_cols
                    st.success("Forward fill applied!")
                    st.rerun()

    # Main Content Area

    if dm.df is not None:
        from ui.filters import render_filters
        
        # UI Filters
        active_filters = render_filters(dm)
        
        # Apply Filters
        filtered_df = dm.apply_filters(active_filters)
        
        
        
        # Layout: Rows | Numeric Sum | Category Count
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        # 1. Row Counts
        total_rows = dm.df.height
        filtered_rows = filtered_df.height
        m_col1.metric("Rows (Filtered / Total)", f"{filtered_rows} / {total_rows}", 
                   delta=f"{filtered_rows - total_rows}" if filtered_rows != total_rows else None)
        
        # Metrics Capture (for Report)
        report_metrics = {
            "total_rows": total_rows,
            "filtered_rows": filtered_rows,
            "numeric_summaries": [],
            "category_counts": []
        }

        # 2. Numeric Sums (Multiple Selection)
        numeric_cols = [col for col, info in dm.get_column_metadata().items() if info["type"] == "numeric"]
        if numeric_cols:
            st.markdown("#### 🔢 Numeric Summaries")
            sum_cols = st.multiselect("Select columns for Sum:", numeric_cols, key="metric_sum_cols")
            
            if sum_cols:
                # Create a dynamic grid for results
                cols_per_row = 4
                sum_grid = st.columns(cols_per_row)
                
                for idx, col in enumerate(sum_cols):
                    curr_sum = filtered_df[col].sum()
                    tot_sum = dm.df[col].sum()
                    
                    # Distribute across grid
                    with sum_grid[idx % cols_per_row]:
                        st.metric(
                            label=f"Sum of {col}", 
                            value=f"{curr_sum:,.2f}", 
                            help=f"Total: {tot_sum:,.2f} | Unfiltered Sum"
                        )
                    
                    report_metrics["numeric_summaries"].append({
                        "column": col,
                        "value": curr_sum,
                        "total": tot_sum
                    })

        st.divider()

        # 3. Category Counts (Multiple Columns)
        categorical_cols = [col for col, info in dm.get_column_metadata().items() if info["type"] == "categorical"]
        if categorical_cols:
            st.markdown("#### 🔠 Category Counts")
            cat_target_cols = st.multiselect("Select columns to count values:", categorical_cols, key="metric_cat_cols")
            
            if cat_target_cols:
                for cat_col in cat_target_cols:
                    with st.expander(f"Counts for '{cat_col}'", expanded=True):
                        # Get unique values present in the FILTERED data
                        unique_vals = sorted([str(v) for v in filtered_df[cat_col].unique().to_list() if v is not None])
                        target_vals = st.multiselect(f"Select values in {cat_col}:", unique_vals, key=f"metric_cat_val_{cat_col}")
                        
                        if target_vals:
                            c_counts_data = []
                            for val in target_vals:
                                count = filtered_df.filter(pl.col(cat_col).cast(pl.Utf8) == val).height
                                c_counts_data.append({"Category": val, "Count": count})
                                # Add to report metrics
                                report_metrics["category_counts"].append({
                                    "column": cat_col,
                                    "category": val,
                                    "count": count
                                })
                            
                            st.dataframe(c_counts_data, use_container_width=True, hide_index=True)

        st.divider()
        
        # Data View (Compact 7 rows)
        st.subheader("📄 Data Preview")
        st.dataframe(filtered_df, height=300, use_container_width=True) # height=300 is roughly 7-8 rows usually
        
        st.divider()
        
        st.divider()
        
        # Visualizations
        from ui.charts import render_charts
        
        st.subheader("📈 Chart Management")
        
        # Initialize session state for charts
        if "active_charts" not in st.session_state:
            # Smart Defaults (Pie preferred as requested)
            default_charts = []
            col_meta = dm.get_column_metadata()
            
            # Suggest Pie if categorical data exists, else Line if Dates, else Bar
            has_cat = any(col_meta.get(col, {}).get("type") == "categorical" for col in active_filters)
            has_date = any(col_meta.get(col, {}).get("type") == "date" for col in dm.df.columns)
            
            # Requested: "for default use pie chart not line chart"
            if has_cat:
                default_charts.append({"type": "Pie Chart", "id": "default_pie"})
            elif has_date:
                default_charts.append({"type": "Pie Chart", "id": "default_pie_date"}) # Prefer Pie even if Date? "not line chart". Assuming user wants Pie as primary default.
            else:
                default_charts.append({"type": "Bar Chart", "id": "default_bar"})
                
            st.session_state.active_charts = default_charts

        # Add Chart Controls
        add_col1, add_col2 = st.columns([0.8, 0.2])
        new_chart_type = add_col1.selectbox("Select Chart Type to Add", ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart"], key="new_chart_selector")
        if add_col2.button("➕ Add", use_container_width=True):
            import uuid
            st.session_state.active_charts.append({"type": new_chart_type, "id": str(uuid.uuid4())})
            st.rerun()

        # Display Active Charts List for Removal
        if st.session_state.active_charts:
            with st.expander("Manage Active Charts", expanded=False):
                for i, chart in enumerate(st.session_state.active_charts):
                    c1, c2 = st.columns([0.85, 0.15])
                    c1.markdown(f"**{i+1}. {chart['type']}**")
                    if c2.button("🗑️", key=f"remove_chart_{chart['id']}"):
                        st.session_state.active_charts.pop(i)
                        st.rerun()
        
        # Render Charts
        figures = render_charts(dm, filtered_df, st.session_state.active_charts)
        
        # Report Generation
        st.divider()
        from core.report_engine import ReportEngine
        if 'report_engine' not in st.session_state:
            st.session_state.report_engine = ReportEngine()
            
        col_rep1, col_rep2 = st.columns([0.7, 0.3])
        with col_rep2:
            if st.button("📄 Generate HTML Report", use_container_width=True, type="primary"):
                report_html = st.session_state.report_engine.generate_report(
                    filtered_df, 
                    os.path.basename(dm.current_file_path),
                    figures,
                    report_metrics # Pass the captured metrics
                )
                st.download_button(
                    label="📥 Download Report",
                    data=report_html,
                    file_name=f"report_{os.path.basename(dm.current_file_path)}.html",
                    mime="text/html",
                    use_container_width=True
                )
    else:
        st.info("👋 Please upload a file or select from history to begin.")

if __name__ == "__main__":
    import os # Needed for os.path.basename in main
    main()
