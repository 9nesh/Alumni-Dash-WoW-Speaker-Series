import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import generate_insights, create_download_link

def run_targeting_analysis(all_sheets):
    """Run all targeting and outreach analyses"""
    st.markdown("<h2 class='sub-header'>Targeting & Outreach Analysis</h2>", unsafe_allow_html=True)
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "High-Capacity Prospects", "Spousal Engagement",
        "Ask Amount Optimization", "Professional Clusters",
        "Non-Donor Analysis", "Email Segments", 
        "Attendance Prediction"
    ])
    
    with tab1:
        high_capacity_prospects(all_sheets)
    
    with tab2:
        spousal_engagement(all_sheets)
    
    with tab3:
        ask_amount_optimization(all_sheets)
    
    with tab4:
        professional_clusters(all_sheets)
    
    with tab5:
        non_donor_analysis(all_sheets)
    
    with tab6:
        email_segments(all_sheets)
    
    with tab7:
        attendance_prediction(all_sheets)

def high_capacity_prospects(all_sheets):
    """Identify high-capacity donors/prospects who haven't attended sessions"""
    st.markdown("<h3>High-Capacity Prospect Analysis</h3>", unsafe_allow_html=True)
    
    # Function to standardize wealth ranges (using the logic from wealth_range_distribution)
    def standardize_wealth_range(we_range):
        if pd.isna(we_range):
            return "Unknown"
        
        we_range = str(we_range).strip().upper()
        we_range = we_range.replace('\n', '').replace('−', '-')
        
        # Map to standardized ranges
        if "5,000,000+" in we_range or "5M+" in we_range:
            return "Over $5M"
        elif "1,000,000-4,999,999" in we_range or "1M-5M" in we_range:
            return "$1M-$5M"
        elif "500,000-999,999" in we_range or "500K-1M" in we_range:
            return "$500K-$1M"
        elif "250,000-499,999" in we_range or "250K-500K" in we_range:
            return "$250K-$500K"
        elif "100,000-249,999" in we_range or "100K-250K" in we_range:
            return "$100K-$250K"
        elif "50,000-99,999" in we_range or "50K-100K" in we_range:
            return "$50K-$100K"
        else:
            return "Under $50K"

    # Process all sheets
    wealth_data = []
    top_prospects = []
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':
            df_copy = df.copy()
            df_copy['Standardized_WE_Range'] = df_copy['WE Range'].apply(standardize_wealth_range)
            df_copy['Session'] = sheet_name
            
            # Collect wealth distribution data
            wealth_data.append(df_copy)
            
            # Identify top prospects (Over $5M and $1M-$5M)
            high_capacity_mask = df_copy['Standardized_WE_Range'].isin(['Over $5M', '$1M-$5M'])
            if high_capacity_mask.any():
                prospects = df_copy[high_capacity_mask].copy()
                top_prospects.append(prospects)

    if wealth_data:
        combined_data = pd.concat(wealth_data)
        
        # ------------------- Wealth Range Distribution -------------------
        st.subheader("Wealth Range Distribution")
        
        # Create wealth distribution chart
        wealth_dist = combined_data['Standardized_WE_Range'].value_counts()
        
        fig = px.pie(
            values=wealth_dist.values,
            names=wealth_dist.index,
            title="Overall Wealth Range Distribution",
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig)
        
        # Show distribution by session
        session_wealth = pd.crosstab(
            combined_data['Session'], 
            combined_data['Standardized_WE_Range'],
            normalize='index'
        ) * 100
        
        fig2 = px.bar(
            session_wealth,
            title="Wealth Range Distribution by Session",
            labels={'value': 'Percentage', 'Session': 'Session Name'},
            barmode='stack'
        )
        fig2.update_layout(height=500)
        st.plotly_chart(fig2)
        
        # ------------------- Top Prospects -------------------
        if top_prospects:
            combined_prospects = pd.concat(top_prospects)
            st.subheader("High-Capacity Individuals")
            
            # Create metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Total High-Capacity Individuals",
                    len(combined_prospects)
                )
            with col2:
                over_5m = len(combined_prospects[
                    combined_prospects['Standardized_WE_Range'] == 'Over $5M'
                ])
                st.metric(
                    "Individuals Over $5M",
                    over_5m
                )
            
            # Display detailed prospect information
            st.markdown("### Detailed Prospect Information")
            prospect_display = combined_prospects[[
                'Name', 'Standardized_WE_Range', 'Session', 
                'Constituency Code', 'Eng Score', 'Email'
            ]].sort_values('Standardized_WE_Range', ascending=False)
            
            st.dataframe(prospect_display)
            
            # Add download button
            csv = prospect_display.to_csv(index=False)
            st.download_button(
                "Download High-Capacity Prospects",
                csv,
                "high_capacity_prospects.csv",
                "text/csv"
            )
            
            # Show engagement levels of high-capacity individuals
            st.subheader("High-Capacity Engagement Analysis")
            fig3 = px.box(
                combined_prospects,
                x='Standardized_WE_Range',
                y='Eng Score',
                title="Engagement Scores by Wealth Range"
            )
            st.plotly_chart(fig3)
        else:
            st.warning("No high-capacity individuals ($1M+) found in the data.")
    else:
        st.error("No wealth range data available for analysis.")

def spousal_engagement(all_sheets):
    """Analyze patterns of couples attending together vs individually"""
    st.markdown("<h3>Spousal Engagement Analysis</h3>", unsafe_allow_html=True)
    
    # Track couples' attendance patterns
    couples_data = []
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':
            # Find attendees with spouse information
            couples = df[df['SP ID'].notna()]
            couples_data.extend([{
                'Session': sheet_name,
                'ID': row['ID'],
                'Name': row['Name'],
                'SP_ID': row['SP ID'],
                'SP_Name': row['SP Name']
            } for _, row in couples.iterrows()])
    
    if couples_data:
        couples_df = pd.DataFrame(couples_data)
        
        # Analyze attendance patterns
        st.plotly_chart(
            px.bar(
                couples_df.groupby('Session').size().reset_index(),
                x='Session',
                y=0,
                title='Couples Attendance by Session'
            )
        )
    else:
        st.warning("No spousal data found in the sessions.")

def ask_amount_optimization(all_sheets):
    """Compare actual giving vs ask amounts for calibration"""
    st.markdown("<h3>Ask Amount Optimization Analysis</h3>", unsafe_allow_html=True)
    
    analysis_data = []
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':
            # Compare last gift amount with ask amounts
            comparison = df[['Last Gift Amount', 'Hi Ask', 'Med Ask', 'Low Ask']].copy()
            comparison['Session'] = sheet_name
            analysis_data.append(comparison)
    
    if analysis_data:
        combined_data = pd.concat(analysis_data)
        
        # Calculate alignment metrics
        combined_data['Above_High'] = combined_data['Last Gift Amount'] > combined_data['Hi Ask']
        combined_data['Within_Range'] = (combined_data['Last Gift Amount'] >= combined_data['Low Ask']) & \
                                      (combined_data['Last Gift Amount'] <= combined_data['Hi Ask'])
        combined_data['Below_Low'] = combined_data['Last Gift Amount'] < combined_data['Low Ask']
        
        # Create visualization
        fig = go.Figure()
        for session in combined_data['Session'].unique():
            session_data = combined_data[combined_data['Session'] == session]
            fig.add_box(
                y=session_data['Last Gift Amount'],
                name=session,
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8
            )
        
        fig.add_hline(y=combined_data['Hi Ask'].median(), line_dash="dash", 
                     annotation_text="Median High Ask")
        fig.add_hline(y=combined_data['Low Ask'].median(), line_dash="dash", 
                     annotation_text="Median Low Ask")
        
        fig.update_layout(
            title="Gift Amounts vs Ask Ranges by Session",
            yaxis_title="Amount ($)",
            showlegend=True
        )
        
        st.plotly_chart(fig)
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Above High Ask", 
                     f"{(combined_data['Above_High'].mean() * 100):.1f}%")
        with col2:
            st.metric("Within Ask Range", 
                     f"{(combined_data['Within_Range'].mean() * 100):.1f}%")
        with col3:
            st.metric("Below Low Ask", 
                     f"{(combined_data['Below_Low'].mean() * 100):.1f}%")

def professional_clusters(all_sheets):
    """Identify professional affiliation clusters"""
    st.markdown("<h3>Professional Affiliation Analysis</h3>", unsafe_allow_html=True)
    
    # Combine professional data across sessions
    prof_data = []
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':
            prof_info = df[['ID', 'Name', 'CnPrBs_Org_Name', 'CnPrBs_Position', 
                           'Eng Score', 'LT Giving']].copy()
            prof_info['Session'] = sheet_name
            prof_data.append(prof_info)
    
    if prof_data:
        combined_prof = pd.concat(prof_data)
        
        # Group by organization and analyze
        org_summary = combined_prof.groupby('CnPrBs_Org_Name').agg({
            'ID': 'count',
            'Eng Score': 'mean',
            'LT Giving': 'sum'
        }).reset_index()
        
        # Filter for organizations with multiple attendees
        significant_orgs = org_summary[org_summary['ID'] > 1].sort_values('ID', ascending=False)
        
        if not significant_orgs.empty:
            st.subheader("Top Professional Clusters")
            
            # Create visualization
            fig = px.scatter(significant_orgs,
                           x='ID',
                           y='Eng Score',
                           size='LT Giving',
                           hover_data=['CnPrBs_Org_Name'],
                           title="Organization Engagement Analysis")
            
            st.plotly_chart(fig)
            
            # Display detailed table
            st.dataframe(significant_orgs.rename(columns={
                'ID': 'Number of Attendees',
                'Eng Score': 'Average Engagement',
                'LT Giving': 'Total Giving'
            }))
        else:
            st.warning("No significant professional clusters found in the data.")
    else:
        st.warning("No professional data available for analysis.")

def non_donor_analysis(all_sheets):
    """Analyze characteristics of non-donor attendees"""
    st.markdown("<h3>Non-Donor Attendee Analysis</h3>", unsafe_allow_html=True)
    
    # Identify non-donors across sessions
    non_donors = []
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':
            # Define non-donors as those with no giving history
            non_donor_mask = (
                (df['Last Gift Amount'].isna()) & 
                (df['LT Giving'].isna()) &
                (df['AF19 - Gifts'].isna())
            )
            non_donor_data = df[non_donor_mask].copy()
            non_donor_data['Session'] = sheet_name
            non_donors.append(non_donor_data)
    
    if non_donors:
        combined_non_donors = pd.concat(non_donors)
        
        # Analyze characteristics
        st.subheader("Non-Donor Profile Analysis")
        
        # Constituency breakdown
        constituency_dist = combined_non_donors['Constituency Code'].value_counts()
        fig_constituency = px.pie(values=constituency_dist.values,
                                names=constituency_dist.index,
                                title="Non-Donor Constituency Distribution")
        st.plotly_chart(fig_constituency)
        
        # Engagement analysis
        if 'Eng Score' in combined_non_donors.columns:
            fig_engagement = px.histogram(
                combined_non_donors,
                x='Eng Score',
                title="Non-Donor Engagement Score Distribution"
            )
            st.plotly_chart(fig_engagement)
        
        # Display actionable insights
        st.markdown("""
        ### Key Findings:
        1. Constituency Patterns
        2. Engagement Levels
        3. Potential Barriers to Giving
        """)

def email_segments(all_sheets):
    """Create email engagement segments"""
    pass  # Implement email segmentation

def attendance_prediction(all_sheets):
    """Build predictive model for attendance"""
    pass  # Implement attendance prediction