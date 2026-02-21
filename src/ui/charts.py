import streamlit as st
import plotly.express as px
import polars as pl

def render_charts(data_manager, filtered_df, active_charts):
    """Renders the charts based on user selection (list of instances). Returns a dict of figures."""
    if filtered_df is None or filtered_df.height == 0:
        st.warning("No data available for charts.")
        return {}

    if not active_charts:
        st.info("Add charts above to visualize data.")
        return {}

    st.header("📈 Visualizations")
    
    metadata = data_manager.get_column_metadata()
    numeric_cols = [col for col, info in metadata.items() if info["type"] == "numeric"]
    categorical_cols = [col for col, info in metadata.items() if info["type"] == "categorical"]
    all_cols = list(metadata.keys())

    if not numeric_cols:
        st.info("No numeric columns found for charting.")
        return {}

    figures = {}

    # Iterate through active charts
    for i, chart in enumerate(active_charts):
        chart_type = chart['type']
        chart_id = chart['id']
        unique_key = f"{chart_type}_{chart_id}" # Base key for this chart instance

        if chart_type == "Bar Chart":
            with st.expander(f"📊 Bar Chart ({i+1})", expanded=True):
                c_col1, c_col2, c_col3 = st.columns(3)
                # Reordered: Aggregation first to determine Y-Axis options
                agg_func = c_col1.selectbox("Aggregation", ["Sum", "Mean", "Count"], key=f"bar_agg_{unique_key}")
                x_axis = c_col2.selectbox("X-Axis (Categorical)", categorical_cols + numeric_cols, key=f"bar_x_{unique_key}")
                
                # If Count, can count any column. If Sum/Mean, need numeric.
                if agg_func == "Count":
                    y_options = categorical_cols + numeric_cols
                else:
                    y_options = numeric_cols
                
                y_axis = c_col3.selectbox("Y-Axis (Value)", y_options, key=f"bar_y_{unique_key}")
                
                # Aggregate data
                if agg_func == "Sum":
                    plot_df = filtered_df.group_by(x_axis).agg(pl.col(y_axis).sum().alias("px_sum")).to_pandas()
                    y_col = "px_sum"
                elif agg_func == "Mean":
                    plot_df = filtered_df.group_by(x_axis).agg(pl.col(y_axis).mean().alias("px_mean")).to_pandas()
                    y_col = "px_mean"
                else:
                    plot_df = filtered_df.group_by(x_axis).agg(pl.col(y_axis).count().alias("px_count")).to_pandas()
                    y_col = "px_count"
                    
                fig_bar = px.bar(plot_df, x=x_axis, y=y_col, title=f"{agg_func} of {y_axis} by {x_axis}", 
                                template="plotly_dark", color=y_col, color_continuous_scale="Viridis")
                fig_bar.update_layout(height=500)
                st.plotly_chart(fig_bar, use_container_width=True)
                figures[f"Bar Chart {i+1}"] = fig_bar

        elif chart_type == "Line Chart":
            with st.expander(f"📈 Line Chart ({i+1})", expanded=True):
                l_col1, l_col2 = st.columns(2)
                x_line = l_col1.selectbox("X-Axis", all_cols, key=f"line_x_{unique_key}")
                y_line = l_col2.selectbox("Y-Axis", numeric_cols, key=f"line_y_{unique_key}")
                
                fig_line = px.line(filtered_df.to_pandas().sort_values(x_line), x=x_line, y=y_line, 
                                  title=f"{y_line} Over {x_line}", template="plotly_dark")
                fig_line.update_layout(height=500)
                st.plotly_chart(fig_line, use_container_width=True)
                figures[f"Line Chart {i+1}"] = fig_line

        elif chart_type == "Scatter Plot":
            with st.expander(f"⚪ Scatter Plot ({i+1})", expanded=True):
                s_col1, s_col2, s_col3 = st.columns(3)
                # Allow categorical on X-axis for Scatter
                x_scat = s_col1.selectbox("X-Axis", numeric_cols + categorical_cols, key=f"scat_x_{unique_key}")
                y_scat = s_col2.selectbox("Y-Axis", numeric_cols, key=f"scat_y_{unique_key}")
                color_scat = s_col3.selectbox("Color By", [None] + categorical_cols, key=f"scat_color_{unique_key}")
                
                fig_scat = px.scatter(filtered_df.to_pandas(), x=x_scat, y=y_scat, color=color_scat,
                                     title=f"{y_scat} vs {x_scat}", template="plotly_dark")
                fig_scat.update_layout(height=500)
                st.plotly_chart(fig_scat, use_container_width=True)
                figures[f"Scatter Plot {i+1}"] = fig_scat

        elif chart_type == "Pie Chart":
            with st.expander(f"🍕 Pie Chart ({i+1})", expanded=True):
                p_col1, p_col2, p_col3 = st.columns(3)
                pie_agg = p_col1.selectbox("Metric", ["Sum", "Count"], key=f"pie_agg_{unique_key}")
                names_pie = p_col2.selectbox("Labels", categorical_cols, key=f"pie_names_{unique_key}")
                
                if pie_agg == "Count":
                    val_options = categorical_cols + numeric_cols
                else:
                    val_options = numeric_cols
                    
                values_pie = p_col3.selectbox("Values", val_options, key=f"pie_vals_{unique_key}")
                
                if pie_agg == "Sum":
                    plot_pie = filtered_df.group_by(names_pie).agg(pl.col(values_pie).sum().alias("px_val")).to_pandas()
                    title_text = f"Sum of {values_pie} by {names_pie}"
                else:
                    plot_pie = filtered_df.group_by(names_pie).agg(pl.col(values_pie).count().alias("px_val")).to_pandas()
                    title_text = f"Count of {values_pie} by {names_pie}"

                fig_pie = px.pie(plot_pie, names=names_pie, values="px_val", 
                                title=title_text, template="plotly_dark")
                fig_pie.update_layout(height=500)
                st.plotly_chart(fig_pie, use_container_width=True)
                figures[f"Pie Chart {i+1}"] = fig_pie

    return figures
