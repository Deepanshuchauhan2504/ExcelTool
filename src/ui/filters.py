import streamlit as st

def render_filters(data_manager):
    """Renders the sidebar filters based on data and returns active filters."""
    if data_manager.df is None:
        return {}

    st.sidebar.header("🔍 Dynamic Filters")
    metadata = data_manager.get_column_metadata()
    active_filters = {}

    # 1. Select which columns to apply filters on
    # This prevents clogging the UI if there are 100+ columns
    available_cols = list(metadata.keys())
    
    selected_cols_to_filter = st.sidebar.multiselect(
        "Select Columns to Filter",
        options=available_cols,
        placeholder="Choose columns...",
        help="Search and select columns you want to filter by."
    )

    st.sidebar.divider()

    # 2. Render filters ONLY for selected columns
    for col in selected_cols_to_filter:
        info = metadata[col]

        with st.sidebar.expander(f"📌 {col}", expanded=True):
            if info["type"] == "categorical":
                selected = st.multiselect(
                    "Select values:",
                    options=info["options"],
                    key=f"filter_{col}",
                    label_visibility="collapsed"
                )
                if selected:
                    active_filters[col] = selected

            elif info["type"] == "numeric":
                min_val, max_val = info["min"], info["max"]
                if min_val == max_val:
                    st.info(f"Constant: {min_val}")
                    continue
                    
                selected_range = st.slider(
                    "Select range:",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                    key=f"filter_{col}",
                    label_visibility="collapsed"
                )
                if selected_range != (min_val, max_val):
                    active_filters[col] = selected_range

            elif info["type"] == "date":
                min_date, max_date = info["min"], info["max"]
                if min_date is not None and max_date is not None:
                    selected_dates = st.date_input(
                        "Select dates:",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key=f"filter_{col}",
                        label_visibility="collapsed"
                    )
                    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                        active_filters[col] = selected_dates

    st.sidebar.divider()
    if st.sidebar.button("🧹 Clear All Filters", use_container_width=True):
        for key in st.session_state.keys():
            if key.startswith("filter_"):
                del st.session_state[key]
        st.rerun()

    return active_filters
