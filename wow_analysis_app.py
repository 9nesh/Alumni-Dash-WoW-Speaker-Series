import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from io import BytesIO
import base64
from datetime import datetime
import re
from pathlib import Path

# Import local modules
from attendance_analysis import run_attendance_analysis
from giving_analysis import run_giving_analysis
from targeting_analysis import run_targeting_analysis
from utils import clean_data, create_download_link

# Set page config
st.set_page_config(
    page_title="WOW Speaker Series Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #2563EB;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.3rem;
        color: #3B82F6;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .insight-box {
        background-color: #000;
        border-left: 5px solid #3B82F6;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #4B5563;
    }
</style>
""", unsafe_allow_html=True)

def load_default_data():
    """Load the default WOW Speaker Series data"""
    try:
        # Assuming the Excel file is in the same directory as the script
        file_path = Path(__file__).parent / "WOW Speaker Series data by session.XLS"
        
        # Read all sheets into a dictionary using xlrd engine for .xls files
        all_sheets = pd.read_excel(
            file_path,
            sheet_name=None,  # None means read all sheets
            engine='xlrd'
        )
        
        # Remove empty Sheet7 if it exists
        if 'Sheet7' in all_sheets:
            del all_sheets['Sheet7']
            
        return all_sheets
    except Exception as e:
        st.error(f"Error loading default data: {str(e)}")
        return None

def main():
    st.title("WOW Speaker Series Analysis Dashboard")
    
    # Load default data
    all_sheets = load_default_data()
    
    if all_sheets is None:
        # Fallback to file upload if default data loading fails
        uploaded_file = st.file_uploader(
            "Upload WOW Speaker Series Excel file",
            type=["xls", "xlsx"]
        )
        
        if uploaded_file is not None:
            all_sheets = pd.read_excel(uploaded_file, sheet_name=None)
            if 'Sheet7' in all_sheets:
                del all_sheets['Sheet7']
    
    if all_sheets:
        # Create tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs([
            "Overview",
            "Attendance Analysis",
            "Giving Analysis",
            "Targeting & Outreach"
        ])
        
        with tab1:
            display_overview(all_sheets)
        
        with tab2:
            run_attendance_analysis(all_sheets)
        
        with tab3:
            run_giving_analysis(all_sheets)
        
        with tab4:
            run_targeting_analysis(all_sheets)

def display_overview(all_sheets):
    """Displays an overview of all sheets and some summary statistics"""
    st.markdown("<h2 class='sub-header'>WOW Speaker Series Data Overview</h2>", unsafe_allow_html=True)
    
    # Summary statistics for sheets
    st.markdown("<h3 class='section-header'>Session Summary</h3>", unsafe_allow_html=True)
    
    # Create summary dataframe
    summary_data = []
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':  # Skip empty sheet
            summary_data.append({
                "Session Name": sheet_name,
                "Attendees": len(df),
                "Unique Email Addresses": df['Email'].nunique() if 'Email' in df.columns else 0,
                "Columns": len(df.columns),
                "Alumni Count": df[df['Constituency Code'] == 'Alumni - Undergraduate'].shape[0] 
                                if 'Constituency Code' in df.columns else 0,
                "Faculty/Staff Count": df[df['Constituency Code'] == 'Faculty/Staff'].shape[0] 
                                      if 'Constituency Code' in df.columns else 0
            })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Create metrics cards for total unique attendees
    total_attendees = sum(summary_df['Attendees'])
    
    # Find unique attendees across all sessions
    all_attendees = set()
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':  # Skip empty sheet
            all_attendees.update(df['ID'].astype(str).tolist())
    
    unique_attendees = len(all_attendees)
    
    # Calculate repeat attendance rate
    repeat_rate = (total_attendees - unique_attendees) / unique_attendees * 100 if unique_attendees > 0 else 0
    
    # Create layout of metric cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_attendees}</div>
            <div class='metric-label'>Total Session Attendees</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{unique_attendees}</div>
            <div class='metric-label'>Unique Individuals</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{repeat_rate:.1f}%</div>
            <div class='metric-label'>Repeat Attendance Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display the summary table
    st.dataframe(summary_df.sort_values(by='Attendees', ascending=False))
    
    # Visualization: Attendees by session
    st.markdown("<h3 class='section-header'>Attendance by Session</h3>", unsafe_allow_html=True)
    
    fig = px.bar(
        summary_df.sort_values('Attendees', ascending=False),
        x='Session Name',
        y='Attendees',
        color='Attendees',
        color_continuous_scale='blues',
        labels={'Attendees': 'Number of Attendees', 'Session Name': 'Session'},
        title='Attendance Count by Session'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display insights box
    st.markdown("""
    <div class='insight-box'>
        <h4>Key Insights:</h4>
        <ul>
            <li>The <b>Wendie Malik</b> session had the highest attendance.</li>
            <li>There's a significant number of repeat attendees, suggesting strong engagement with the series.</li>
            <li>Specific constituency engagement varies by session, which can inform future targeting strategies.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick overview of available analyses
    st.markdown("<h3 class='section-header'>Available Analysis Types</h3>", unsafe_allow_html=True)
    
    analysis_types = {
        "Attendance & Engagement Analysis": [
            "Cross-Session Attendance Patterns",
            "Attendance by Constituency",
            "Greek Affiliation Analysis",
            "Attendance by Graduation Decade",
            "Engagement Score vs. Attendance",
            "Geographic Distribution",
            "Major Field of Study Correlation"
        ],
        "Giving Analysis": [
            "Session Attendance and Giving Correlation",
            "Pre/Post Attendance Giving Analysis",
            "Wealth Range Distribution by Session",
            "Session-Specific ROI",
            "First-Time Donor Acquisition",
            "Annual Fund vs. Designated Giving Preferences",
            "Class Year Giving Patterns"
        ],
        "Targeting & Outreach Opportunities": [
            "\"Never Attended\" High-Capacity Prospects",
            "Spousal Engagement Analysis",
            "Ask Amount Optimization",
            "Professional Affiliation Clusters",
            "Non-Donor Attendee Analysis",
            "Email Engagement Segments",
            "Attendance Frequency Prediction"
        ],
        "Session-Specific Insights": [
            "Wendie Malik Session Analysis",
            "Karlyn Crowley Impact Assessment",
            "2024 Women in Politics Audience",
            "Small Session Value",
            "Session Name Analysis"
        ],
        "Multi-Year Trend Analysis": [
            "Fiscal Year Giving Patterns",
            "Lifetime Giving Trajectory",
            "Session Interest Evolution"
        ]
    }
    
    for category, analyses in analysis_types.items():
        with st.expander(f"{category} ({len(analyses)} analyses)"):
            for analysis in analyses:
                st.markdown(f"- {analysis}")

if __name__ == "__main__":
    main() 