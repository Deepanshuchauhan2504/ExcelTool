import streamlit as st
import polars as pl
import math
import io
import zipfile

def render_splitter_ui():
    st.title("✂️ Large Text to Excel Splitter")
    st.markdown("Upload a massive `.txt` or `.csv` file, and we'll automatically chunk it into multiple safe `.xlsx` files based on Excel's row limits.")

    # File Uploader
    uploaded_file = st.file_uploader("Upload large TXT or CSV file", type=["txt", "csv"], key="splitter_file")
    
    # We clear the previous download buffer if heavily modified
    if 'last_uploaded_name' not in st.session_state or (uploaded_file and st.session_state.last_uploaded_name != uploaded_file.name):
        if 'split_zip_buffer' in st.session_state:
            del st.session_state.split_zip_buffer
        if uploaded_file:
            st.session_state.last_uploaded_name = uploaded_file.name
    
    if uploaded_file:
        try:
            # 1. Immediate Read for Total Rows
            uploaded_file.seek(0)
            
            with st.spinner("Analyzing dataset and counting rows..."):
                file_name = uploaded_file.name.lower()
                # Dynamically determine separator based on extension or peek
                sep = "," if file_name.endswith(".csv") else "\t" 
                
                # Eagerly load the dataset into a highly optimized Polars dataframe
                df = pl.read_csv(uploaded_file, ignore_errors=True, separator=sep)
                total_rows = df.height
                
            # 2. Display Metrics using Streamlit columns for a nice UI
            st.metric(label="Total Rows Found", value=f"{total_rows:,}")
            
            # 3. Smart Default Calculation
            MAX_ROWS_PER_FILE = 1000000
            
            # 4. User Control: Define how many rows per chunk
            st.subheader("⚙️ Split Settings")
            rows_per_file = st.number_input(
                "Rows per Excel File",
                min_value=1,
                max_value=1048500, # Safely below Excel's absolute hard limit of 1,048,576
                value=min(MAX_ROWS_PER_FILE, total_rows) if total_rows > 0 else MAX_ROWS_PER_FILE,
                step=100000,
                help="Excel natively supports exactly 1,048,576 rows per sheet. We recommend 1,000,000 to remain extremely safe."
            )
            
            # Calculate robust expectation for dynamic text
            expected_files = math.ceil(total_rows / rows_per_file) if rows_per_file > 0 else 0
            
            # 5. Dynamic Update Text below the slider/input
            st.info(f"💡 This will generate approximately **{expected_files}** Excel files inside the `.zip` folder.")
            
            # 6. Execution Loop (Chunking)
            st.divider()
            
            if expected_files > 0:
                if st.button("🚀 Execute Split & Download", type="primary"):
                    
                    # Wrap chunking and joining in a progress bar context
                    progress_bar = st.progress(0, text="Starting the chunking process...")
                    
                    try:
                        zip_buffer = io.BytesIO()
                        
                        # Open Memory ZIP Context
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for i in range(expected_files):
                                # Update progress bar dynamically
                                progress_text = f"Generating file {i+1} of {expected_files}..."
                                progress_bar.progress(i / expected_files, text=progress_text)
                                
                                start_idx = i * rows_per_file
                                # We utilize Polars' highly optimized slice operation
                                chunk_df = df.slice(start_idx, rows_per_file)
                                
                                # Write memory buffer directly
                                chunk_buffer = io.BytesIO()
                                chunk_df.write_excel(chunk_buffer)
                                
                                # Assemble accurate file name based on partition
                                base_name = file_name.rsplit(".", 1)[0]
                                excel_name = f"{base_name}_part_{i+1}.xlsx"
                                
                                # Flush bytes into the zipped file container
                                zip_file.writestr(excel_name, chunk_buffer.getvalue())
                                
                        # Finalize
                        progress_bar.progress(1.0, text="Compression complete!")
                        st.session_state.split_zip_buffer = zip_buffer.getvalue()
                        st.success(f"✅ Splitting complete! Successfully packaged {expected_files} files.")
                        
                    except Exception as inline_e:
                        st.error(f"Failed to generate chunk: {inline_e}")
                    
        except Exception as e:
            st.error(f"❌ Error processing file initial read: {e}")
            
    # Conditional Streamlit Download Widget
    if "split_zip_buffer" in st.session_state:
        st.download_button(
            label="📥 Download Split Files (.zip)",
            data=st.session_state.split_zip_buffer,
            file_name="split_excel_files.zip",
            mime="application/zip",
            type="primary"
        )
