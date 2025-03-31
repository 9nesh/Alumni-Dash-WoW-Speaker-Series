
# Implementation Plan for WOW Speaker Series Analysis

Based on the existing code in `wow_analysis_app.py` and `utils.py`, here's a structured approach to implement all 30 analyses from the ideas document:

## Project Structure

```
alumni-analysis/
├── wow_analysis_app.py        # Main Streamlit app (already created)
├── utils.py                   # Utility functions (already created)
├── attendance_analysis.py     # Attendance & Engagement Analysis (items 1-7)
├── giving_analysis.py         # Giving Analysis (items 8-15)
├── targeting_analysis.py      # Targeting & Outreach (items 16-22)
├── session_specific.py        # Session-Specific Insights (items 23-27)
├── trend_analysis.py          # Multi-Year Trend Analysis (items 28-30)
├── requirements.txt           # Dependencies
```

## Core Implementation Strategy

1. **Use Modular Design**: Each analysis category has its own module file
2. **Leverage Existing Functions**: The `utils.py` file has excellent data processing functions
3. **Consistent UI**: Maintain the same UI pattern of tabs, charts, and insights boxes

## Implementation Details by Category

### 1. Attendance & Engagement Analysis (attendance_analysis.py)

```python
def run_attendance_analysis(all_sheets):
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Cross-Session Attendance", "Attendance by Constituency", 
        "Greek Affiliation", "Graduation Decade", "Engagement Score",
        "Geographic Distribution", "Major Field Study"
    ])
    
    with tab1:
        # Analysis 1: Cross-Session Attendance Patterns
        # Use sets to find overlap between sessions
        # Create UpSet or Venn diagram using plotly
    
    with tab2:
        # Analysis 2: Attendance by Constituency
        # Group by constituency code per session
        # Use a stacked bar chart
    
    # ... continue for tabs 3-7
```

### 2. Giving Analysis (giving_analysis.py)

```python
def run_giving_analysis(all_sheets):
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Giving by Session", "Pre/Post Attendance", "Wealth Distribution",
        "Session ROI", "First-Time Donors", "Giving Methods",
        "AF vs DG Preferences", "Class Year Patterns"
    ])
    
    with tab1:
        # Analysis 8: Session Attendance and Giving Correlation
        # Calculate average giving metrics per session
        # Use bar charts or scatter plots
    
    # ... continue for tabs 2-8
```

### 3. Targeting & Outreach (targeting_analysis.py)

```python
def run_targeting_analysis(all_sheets):
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "High-Capacity Prospects", "Spousal Engagement",
        "Ask Amount Optimization", "Professional Clusters",
        "Non-Donor Analysis", "Email Segments", 
        "Attendance Prediction"
    ])
    
    with tab1:
        # Analysis 16: "Never Attended" High-Capacity Prospects
        # Find high-capacity donors based on WE Range
        # Create filterable table with download option
    
    # ... continue for tabs 2-7
```

### 4. Session-Specific Insights (session_specific.py)

```python
def run_session_specific(all_sheets):
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Wendie Malik Session", "Karlyn Crowley Impact",
        "Women in Politics Audience", "Small Session Value",
        "Session Name Analysis"
    ])
    
    with tab1:
        # Analysis 23: Wendie Malik Session Analysis
        # Compare characteristics of this audience to others
        # Create demographic profiles
    
    # ... continue for tabs 2-5
```

### 5. Multi-Year Trend Analysis (trend_analysis.py)

```python
def run_trend_analysis(all_sheets):
    # Create tabs for different analyses
    tab1, tab2, tab3 = st.tabs([
        "Fiscal Year Patterns", "Lifetime Giving Trajectory",
        "Session Interest Evolution"
    ])
    
    with tab1:
        # Analysis 28: Fiscal Year Giving Patterns
        # Analyze giving patterns across fiscal years
        # Use line charts to show trends
    
    # ... continue for tabs 2-3
```

## Key Functions to Leverage from Utils

- `clean_data()`: For preprocessing each sheet
- `extract_wealth_range_value()`: For wealth range sorting and categorization
- `get_decade_label()`: For graduation decade analysis
- `categorize_giving_level()`: For donation amount categorization
- `generate_insights()`: For creating consistent insight boxes

## Implementation Tips

1. **Incremental Development**: Implement one analysis at a time, test, then move to the next
2. **Data Transformation**: Make heavy use of pandas for data manipulation
3. **Consistent Visualization**: Use plotly for interactive visualizations
4. **Error Handling**: Implement `try/except` blocks for each analysis to prevent the entire app from crashing
5. **Caching**: Use `@st.cache_data` decorator for expensive computations
6. **Download Options**: Add download links for tables using `create_download_link()`

## Example Implementation (Cross-Session Attendance)

```python
# In attendance_analysis.py
def attendance_overlap_analysis(all_sheets):
    """Implement Cross-Session Attendance Patterns analysis"""
    
    # Create sets of attendees for each session
    attendee_sets = {}
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':  # Skip empty sheet
            attendee_sets[sheet_name] = set(df['ID'].astype(str))
    
    # Calculate overlap metrics
    total_unique = set().union(*attendee_sets.values())
    st.write(f"Total unique attendees across all sessions: {len(total_unique)}")
    
    # Create overlap matrix
    overlap_data = []
    for session1 in attendee_sets:
        row = []
        for session2 in attendee_sets:
            if session1 == session2:
                overlap = len(attendee_sets[session1])
            else:
                overlap = len(attendee_sets[session1].intersection(attendee_sets[session2]))
            row.append(overlap)
        overlap_data.append(row)
    
    # Create heatmap with plotly
    fig = px.imshow(
        overlap_data,
        x=list(attendee_sets.keys()),
        y=list(attendee_sets.keys()),
        color_continuous_scale='blues',
        labels=dict(x="Session", y="Session", color="Attendees"),
        title="Session Attendance Overlap"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Generate insights
    insights = {
        "Highest overlap": "Sessions X and Y share Z attendees",
        "Most loyal attendees": "N people attended all sessions",
        "Unique attendees": "N% only attended one session"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
```

By following this approach, you can implement all 30 analyses while maintaining a consistent user experience and code organization throughout the application.
