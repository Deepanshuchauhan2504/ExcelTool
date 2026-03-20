import streamlit as st
import polars as pl
import io

def get_columns(uploaded_file) -> list[str]:
    """
    Efficiently extracts column names from an uploaded file (CSV or Excel)
    without fully parsing the data into memory where possible.
    """
    try:
        if uploaded_file is None:
            return []
            
        # Reset file pointer to the beginning of the stream
        uploaded_file.seek(0)
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.csv'):
            # For Big Data CSVs, we use n_rows=0 to parse only the schema/headers.
            # This is blazing fast and completely avoids loading the data into RAM.
            df_schema = pl.read_csv(uploaded_file, n_rows=0)
            return df_schema.columns
            
        elif file_name.endswith(('.xlsx', '.xls')):
            # For Excel files, reading headers without loading the file is trickier in Polars
            # depending on the engine. We read the bytes into memory (already uploaded via Streamlit anyway),
            # and let Polars extract the schema.
            file_bytes = uploaded_file.read()
            df_excel = pl.read_excel(file_bytes)
            
            # Reset the pointer again for the actual dataset read later
            uploaded_file.seek(0)
            return df_excel.columns
            
        else:
            st.error(f"Unsupported file format: {file_name}. Please upload CSV or Excel files.")
            return []
            
    except Exception as e:
        st.error(f"Error reading file headers for {uploaded_file.name}: {e}")
        return []

def render_merge_ui():
    st.title("🔗 Data Merge & Cross-Reference")
    st.markdown("Upload a **Target** file and a **Source** file, then select matching columns to merge data.")

    # 1. Initialize session states safely
    if "target_match_col" not in st.session_state:
        st.session_state.target_match_col = None
    if "source_match_col" not in st.session_state:
        st.session_state.source_match_col = None
    if "source_extract_cols" not in st.session_state:
        st.session_state.source_extract_cols = []

    col1, col2 = st.columns(2)

    target_cols = []
    source_cols = []

    # --- Target UI ---
    with col1:
        st.header("🎯 Target File")
        target_file = st.file_uploader("Upload Target Excel/CSV", type=["xlsx", "xls", "csv"], key="target_file")
        
        if target_file:
            st.success(f"Loaded: {target_file.name}")
            # Extract headers efficiently and display selectbox
            target_cols = get_columns(target_file)
            
            if target_cols:
                target_match = st.selectbox(
                    "Select Match Column in Target:", 
                    options=target_cols,
                    key="ui_target_match",
                    help="This column will be used to look up matching values."
                )
                st.session_state.target_match_col = target_match
            
    # --- Source UI ---
    with col2:
        st.header("🗂️ Source File")
        source_file = st.file_uploader("Upload Source Excel/CSV", type=["xlsx", "xls", "csv"], key="source_file")
        
        if source_file:
            st.success(f"Loaded: {source_file.name}")
            # Extract headers efficiently and display selectbox
            source_cols = get_columns(source_file)
            
            if source_cols:
                source_match = st.selectbox(
                    "Select Match Column in Source:", 
                    options=source_cols,
                    key="ui_source_match",
                    help="This column must correspond to the Match Column in the Target file."
                )
                st.session_state.source_match_col = source_match
            
    st.divider()
    
    # --- Columns to Extract (Mapping) UI ---
    if target_file and source_file and target_cols and source_cols:
        st.subheader("⚙️ Merge Settings")
        
        # We generally don't want to bring over the MATCH column again, so we filter it out of the options
        extract_options = [col for col in source_cols if col != st.session_state.source_match_col]
        
        source_extract = st.multiselect(
            "Select columns to bring over from Source to Target:",
            options=extract_options,
            key="ui_source_extract",
            help="These selected columns will be appended to your Target file data."
        )
        st.session_state.source_extract_cols = source_extract
        
        # --- Execution UI ---
        if st.button("🚀 Run Merge", type="primary"):
            # Validation Step
            if not st.session_state.target_match_col or not st.session_state.source_match_col:
                st.error("❌ Please select a Match Column for both Target and Source files.")
            elif not st.session_state.source_extract_cols:
                st.warning("⚠️ Please select at least one column to bring over from the Source file.")
            else:
                with st.spinner("Merging large datasets... Please wait"):
                    try:
                        # 1. Read Target File completely
                        target_file.seek(0)
                        if target_file.name.lower().endswith('.csv'):
                            df_target = pl.read_csv(target_file)
                        else:
                            df_target = pl.read_excel(target_file.read())
                        
                        # 2. Read Source File (Memory Optimized Select)
                        source_file.seek(0)
                        cols_to_read = [st.session_state.source_match_col] + st.session_state.source_extract_cols
                        
                        if source_file.name.lower().endswith('.csv'):
                            df_source = pl.read_csv(source_file, columns=cols_to_read)
                        else:
                            # Read excel normally, but select only required columns immediately
                            df_source = pl.read_excel(source_file.read()).select(cols_to_read)
                            
                        # 3. Perform Left Join
                        # Cast both matching columns to String (Utf8) to avoid data type mismatches
                        df_target = df_target.with_columns(pl.col(st.session_state.target_match_col).cast(pl.Utf8))
                        df_source = df_source.with_columns(pl.col(st.session_state.source_match_col).cast(pl.Utf8))
                        
                        df_final = df_target.join(
                            df_source,
                            left_on=st.session_state.target_match_col,
                            right_on=st.session_state.source_match_col,
                            how="left"
                        )
                        
                        # 4. In-Memory Export
                        output_buffer = io.BytesIO()
                        df_final.write_excel(output_buffer)
                        
                        # Save the generated bytes to session state so download button persists
                        st.session_state.merged_result = output_buffer.getvalue()
                        st.success("✅ Merge completed successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ An error occurred during the merge process:\n{str(e)}")
                        
        # 5. Download Button
        if "merged_result" in st.session_state:
            st.download_button(
                label="📥 Download Merged Result",
                data=st.session_state.merged_result,
                file_name="merged_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
