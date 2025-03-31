import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import generate_insights, get_session_colors, create_download_link

def run_giving_analysis(all_sheets):
    """Run all giving-related analyses"""
    st.markdown("<h2 class='sub-header'>Giving Analysis</h2>", unsafe_allow_html=True)
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Giving by Session", "Pre/Post Attendance", "Wealth Distribution",
        "Session ROI", "First-Time Donors", "AF vs DG Preferences",
        "Class Year Patterns"
    ])
    
    with tab1:
        session_giving_correlation(all_sheets)
    
    with tab2:
        pre_post_giving_analysis(all_sheets)
    
    with tab3:
        wealth_range_distribution(all_sheets)
    
    with tab4:
        session_roi_analysis(all_sheets)
    
    with tab5:
        first_time_donor_analysis(all_sheets)
    
    with tab6:
        af_dg_preferences(all_sheets)
    
    with tab7:
        class_year_giving_patterns(all_sheets)

def session_giving_correlation(all_sheets):
    """Compare giving patterns of attendees across different sessions"""
    st.markdown("<h3 class='section-header'>Session Attendance and Giving Correlation</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis compares giving patterns of attendees across different sessions to determine 
    which sessions attracted the most generous donors.
    """)
    
    # Check if giving data exists
    has_giving = all(
        'Total_All_Giving' in df.columns 
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_giving:
        st.error("Giving data not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Extract giving data from each session
    giving_data = {}
    session_totals = {}
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Store giving metrics and totals
        giving_data[sheet_name] = {
            'Total_Giving': df['Total_All_Giving'].sum(),
            'Average_Giving': df['Total_All_Giving'].mean(),
            'Median_Giving': df['Total_All_Giving'].median(),
            'Donors': len(df[df['Total_All_Giving'] > 0]),
            'Total_Attendees': len(df)
        }
        
        # Calculate donor percentage
        giving_data[sheet_name]['Donor_Percentage'] = (
            giving_data[sheet_name]['Donors'] / giving_data[sheet_name]['Total_Attendees'] * 100
            if giving_data[sheet_name]['Total_Attendees'] > 0 else 0
        )
    
    # ------------------- Giving Overview -------------------
    st.subheader("Giving Overview by Session")
    
    # Create metrics cards
    col1, col2, col3 = st.columns(3)
    
    # Calculate total giving across all sessions
    total_giving = sum(data['Total_Giving'] for data in giving_data.values())
    
    # Find session with highest average giving
    highest_avg = max(giving_data.items(), key=lambda x: x[1]['Average_Giving'])
    
    # Calculate overall donor percentage
    total_donors = sum(data['Donors'] for data in giving_data.values())
    total_attendees = sum(data['Total_Attendees'] for data in giving_data.values())
    overall_donor_pct = (total_donors / total_attendees * 100) if total_attendees > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>${total_giving:,.0f}</div>
            <div class='metric-label'>Total Giving</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>${highest_avg[1]['Average_Giving']:,.0f}</div>
            <div class='metric-label'>Highest Average Giving<br>({highest_avg[0]})</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{overall_donor_pct:.1f}%</div>
            <div class='metric-label'>Overall Donor Percentage</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- Giving Metrics by Session -------------------
    st.subheader("Giving Metrics by Session")
    
    # Create DataFrame for plotting
    plot_data = []
    for session, data in giving_data.items():
        plot_data.append({
            'Session': session,
            'Total Giving': data['Total_Giving'],
            'Average Giving': data['Average_Giving'],
            'Median Giving': data['Median_Giving'],
            'Donor Percentage': data['Donor_Percentage'],
            'Donors': data['Donors'],
            'Total Attendees': data['Total_Attendees']
        })
    
    plot_df = pd.DataFrame(plot_data)
    
    # Create giving metrics visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Total and Average Giving by Session', 'Donor Percentage by Session'),
        vertical_spacing=0.2,
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )
    
    # Add total giving bars
    fig.add_trace(
        go.Bar(
            name='Total Giving',
            x=plot_df['Session'],
            y=plot_df['Total Giving'],
            marker_color='rgb(55, 83, 109)'
        ),
        row=1, col=1
    )
    
    # Add average giving line
    fig.add_trace(
        go.Scatter(
            name='Average Giving',
            x=plot_df['Session'],
            y=plot_df['Average Giving'],
            mode='lines+markers',
            marker=dict(color='rgb(26, 118, 255)'),
            line=dict(color='rgb(26, 118, 255)')
        ),
        row=1, col=1,
        secondary_y=True
    )
    
    # Add donor percentage bars
    fig.add_trace(
        go.Bar(
            name='Donor Percentage',
            x=plot_df['Session'],
            y=plot_df['Donor Percentage'],
            marker_color='rgb(158, 202, 225)'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Giving Metrics by Session"
    )
    
    # Update axes
    fig.update_xaxes(tickangle=-45)
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Total Giving ($)", row=1, col=1)
    fig.update_yaxes(title_text="Average Giving ($)", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Donor Percentage (%)", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Giving Distribution -------------------
    st.subheader("Giving Distribution by Session")
    
    # Create box plot of giving distribution
    fig = px.box(
        pd.concat([
            pd.DataFrame({
                'Session': sheet_name,
                'Giving Amount': df['Total_All_Giving']
            }) for sheet_name, df in all_sheets.items() if sheet_name.lower() != 'sheet7'
        ]),
        x='Session',
        y='Giving Amount',
        title='Distribution of Giving Amounts by Session',
        points="all"  # Show all points
    )
    
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        yaxis_title='Giving Amount ($)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Giving Data Download -------------------
    st.subheader("Session Giving Data")
    
    # Display the DataFrame
    st.dataframe(plot_df)
    
    # Create download link
    st.markdown(
        create_download_link(plot_df, "session_giving_data.csv", "Download Session Giving Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find session with highest total giving
    highest_total = max(giving_data.items(), key=lambda x: x[1]['Total_Giving'])
    
    # Find session with highest donor percentage
    highest_donor_pct = max(giving_data.items(), key=lambda x: x[1]['Donor_Percentage'])
    
    # Calculate giving concentration (what percentage of total giving comes from top session)
    giving_concentration = (highest_total[1]['Total_Giving'] / total_giving * 100) if total_giving > 0 else 0
    
    # Generate insights
    insights = {
        "Highest giving session": f"{highest_total[0]} generated ${highest_total[1]['Total_Giving']:,.0f} in total giving",
        "Best donor conversion": f"{highest_donor_pct[0]} had the highest donor percentage at {highest_donor_pct[1]['Donor_Percentage']:.1f}%",
        "Giving concentration": f"The top session accounted for {giving_concentration:.1f}% of total giving"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Session Replication**: Analyze and replicate elements of sessions with high giving metrics.
    
    2. **Donor Cultivation**: Focus on converting attendees from high-giving sessions into regular donors.
    
    3. **Content Strategy**: Develop session topics that resonate with historically generous donor segments.
    
    4. **Follow-up Strategy**: Create targeted follow-up plans based on session-specific giving patterns.
    
    5. **Giving Diversification**: For sessions with low giving metrics, develop strategies to increase donor participation.
    """)

def pre_post_giving_analysis(all_sheets):
    """Analyze if giving increased after attending specific speaker series events"""
    st.markdown("<h3 class='section-header'>Pre/Post Attendance Giving Analysis</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis examines if giving increased after attending specific speaker series events,
    particularly for multi-year attendees.
    """)
    
    # Check if fiscal year giving data exists
    required_columns = [
        'AF19 - Gifts', 'AF18 - Gifts', 'AF17 - Gifts', 'AF16 - Gifts', 'AF15 - Gifts', 'AF14 - Gifts',
        'DG19 - Gifts', 'DG18 - Gifts', 'DG17 - Gifts', 'DG16 - Gifts'
    ]
    
    has_fiscal_data = all(
        all(col in df.columns for col in required_columns)
        for name, df in all_sheets.items()
        if name.lower() != 'sheet7'
    )
    
    if not has_fiscal_data:
        st.error("Fiscal year giving data not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Extract fiscal year giving data from each session
    giving_trends = {}
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Calculate total giving (AF + DG) for each fiscal year
        fiscal_years = {
            'FY19': df['AF19 - Gifts'].fillna(0) + df['DG19 - Gifts'].fillna(0),
            'FY18': df['AF18 - Gifts'].fillna(0) + df['DG18 - Gifts'].fillna(0),
            'FY17': df['AF17 - Gifts'].fillna(0) + df['DG17 - Gifts'].fillna(0),
            'FY16': df['AF16 - Gifts'].fillna(0) + df['DG16 - Gifts'].fillna(0),
            'FY15': df['AF15 - Gifts'].fillna(0),
            'FY14': df['AF14 - Gifts'].fillna(0)
        }
        
        # Store metrics for each fiscal year
        giving_trends[sheet_name] = {
            year: {
                'Total': values.sum(),
                'Average': values.mean(),
                'Donors': len(values[values > 0]),
                'Total_Attendees': len(values)
            }
            for year, values in fiscal_years.items()
        }
    
    # ------------------- Year-over-Year Trends -------------------
    st.subheader("Year-over-Year Giving Trends")
    
    # Create DataFrame for plotting
    trend_data = []
    for session, years in giving_trends.items():
        for year, metrics in years.items():
            trend_data.append({
                'Session': session,
                'Fiscal Year': year,
                'Total Giving': metrics['Total'],
                'Average Giving': metrics['Average'],
                'Donors': metrics['Donors'],
                'Donor Percentage': (metrics['Donors'] / metrics['Total_Attendees'] * 100) 
                                  if metrics['Total_Attendees'] > 0 else 0
            })
    
    trend_df = pd.DataFrame(trend_data)
    
    # Create giving trends visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Total Giving by Fiscal Year', 'Average Giving by Fiscal Year'),
        vertical_spacing=0.2
    )
    
    # Add total giving lines
    for session in giving_trends.keys():
        session_data = trend_df[trend_df['Session'] == session]
        
        # Total giving trend
        fig.add_trace(
            go.Scatter(
                name=f'{session} - Total',
                x=session_data['Fiscal Year'],
                y=session_data['Total Giving'],
                mode='lines+markers'
            ),
            row=1, col=1
        )
        
        # Average giving trend
        fig.add_trace(
            go.Scatter(
                name=f'{session} - Average',
                x=session_data['Fiscal Year'],
                y=session_data['Average Giving'],
                mode='lines+markers'
            ),
            row=2, col=1
        )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Giving Trends by Session"
    )
    
    # Update axes
    fig.update_xaxes(title_text="Fiscal Year", row=1, col=1)
    fig.update_xaxes(title_text="Fiscal Year", row=2, col=1)
    fig.update_yaxes(title_text="Total Giving ($)", row=1, col=1)
    fig.update_yaxes(title_text="Average Giving ($)", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Pre/Post Analysis -------------------
    st.subheader("Pre/Post Attendance Giving Analysis")
    
    # Calculate year-over-year changes
    yoy_changes = []
    for session, years in giving_trends.items():
        fiscal_years = list(years.keys())
        for i in range(len(fiscal_years)-1):
            current_year = fiscal_years[i]
            previous_year = fiscal_years[i+1]
            
            total_change = years[current_year]['Total'] - years[previous_year]['Total']
            total_change_pct = (
                (years[current_year]['Total'] / years[previous_year]['Total'] - 1) * 100
                if years[previous_year]['Total'] > 0 else 0
            )
            
            avg_change = years[current_year]['Average'] - years[previous_year]['Average']
            avg_change_pct = (
                (years[current_year]['Average'] / years[previous_year]['Average'] - 1) * 100
                if years[previous_year]['Average'] > 0 else 0
            )
            
            yoy_changes.append({
                'Session': session,
                'Year Comparison': f'{current_year} vs {previous_year}',
                'Total Giving Change': total_change,
                'Total Giving Change %': total_change_pct,
                'Average Giving Change': avg_change,
                'Average Giving Change %': avg_change_pct,
                'Donor Change': years[current_year]['Donors'] - years[previous_year]['Donors']
            })
    
    changes_df = pd.DataFrame(yoy_changes)
    
    # Create year-over-year changes visualization
    fig = px.bar(
        changes_df,
        x='Session',
        y='Total Giving Change %',
        color='Year Comparison',
        title='Year-over-Year Giving Changes by Session',
        barmode='group'
    )
    
    fig.update_layout(
        height=500,
        xaxis_tickangle=-45,
        yaxis_title='Change in Total Giving (%)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Data Download -------------------
    st.subheader("Pre/Post Giving Data")
    
    # Display the DataFrames
    st.write("Year-over-Year Giving Trends:")
    st.dataframe(trend_df)
    
    st.write("Year-over-Year Changes:")
    st.dataframe(changes_df)
    
    # Create download links
    st.markdown(
        create_download_link(trend_df, "giving_trends_data.csv", "Download Giving Trends Data"),
        unsafe_allow_html=True
    )
    
    st.markdown(
        create_download_link(changes_df, "giving_changes_data.csv", "Download Giving Changes Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find largest year-over-year increase
    largest_increase = changes_df.loc[changes_df['Total Giving Change %'].idxmax()]
    
    # Find most consistent growth
    avg_growth = changes_df.groupby('Session')['Total Giving Change %'].mean()
    most_consistent = avg_growth.idxmax()
    
    # Calculate overall trend
    total_trend = trend_df.groupby('Fiscal Year')['Total Giving'].sum()
    overall_change = ((total_trend.iloc[0] / total_trend.iloc[-1]) - 1) * 100 if total_trend.iloc[-1] > 0 else 0
    
    # Generate insights
    insights = {
        "Largest increase": f"{largest_increase['Session']} saw a {largest_increase['Total Giving Change %']:.1f}% increase in {largest_increase['Year Comparison']}",
        "Most consistent growth": f"{most_consistent} showed the most consistent giving growth, averaging {avg_growth[most_consistent]:.1f}% per year",
        "Overall trend": f"Total giving across all sessions has changed by {overall_change:.1f}% from FY14 to FY19"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Growth Replication**: Study and replicate engagement strategies from sessions showing consistent giving growth.
    
    2. **Timing Optimization**: Schedule future sessions during periods historically associated with increased giving.
    
    3. **Donor Retention**: Develop specific strategies to maintain giving momentum after successful sessions.
    
    4. **Impact Communication**: Share giving impact stories from sessions with strong post-attendance giving increases.
    
    5. **Multi-Year Engagement**: Create long-term engagement plans based on observed giving patterns.
    """)

def wealth_range_distribution(all_sheets):
    """Compare wealth estimate ranges of attendees across sessions"""
    st.markdown("<h3 class='section-header'>Wealth Range Distribution by Session</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis compares the wealth estimate ranges (WE Range) of attendees across different sessions
    to identify which sessions attracted the wealthiest constituents.
    """)
    
    # Check if wealth range data exists
    has_wealth = all(
        'WE Range' in df.columns 
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_wealth:
        st.error("Wealth Range (WE Range) data not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Function to standardize wealth ranges
    def standardize_wealth_range(we_range):
        if pd.isna(we_range):
            return "Unknown"
        
        we_range = str(we_range).strip().upper()
        
        # Common mappings
        if "UNDER" in we_range or "<" in we_range:
            return "Under $100K"
        elif "100K-250K" in we_range or "100-250" in we_range:
            return "$100K-$250K"
        elif "250K-500K" in we_range or "250-500" in we_range:
            return "$250K-$500K"
        elif "500K-1M" in we_range or "500-1000" in we_range:
            return "$500K-$1M"
        elif "1M-5M" in we_range or "1000-5000" in we_range:
            return "$1M-$5M"
        elif "5M+" in we_range or ">5M" in we_range or "OVER 5M" in we_range:
            return "Over $5M"
        else:
            return "Unknown"
    
    # Extract wealth range data from each session
    wealth_data = {}
    session_totals = {}
    all_ranges = set()
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Standardize wealth ranges
        df['Standardized WE Range'] = df['WE Range'].apply(standardize_wealth_range)
        
        # Count attendees by wealth range
        wealth_counts = df['Standardized WE Range'].value_counts()
        wealth_data[sheet_name] = wealth_counts
        session_totals[sheet_name] = len(df)
        all_ranges.update(wealth_counts.index)
    
    # Define wealth range order
    wealth_order = [
        "Under $100K", "$100K-$250K", "$250K-$500K", 
        "$500K-$1M", "$1M-$5M", "Over $5M", "Unknown"
    ]
    
    # ------------------- Wealth Range Overview -------------------
    st.subheader("Wealth Range Overview")
    
    # Create metrics cards
    col1, col2, col3 = st.columns(3)
    
    # Calculate total high-capacity attendees (>$1M)
    high_capacity_ranges = ["$1M-$5M", "Over $5M"]
    total_high_capacity = sum(
        sum(counts[range_name] for range_name in high_capacity_ranges if range_name in counts)
        for counts in wealth_data.values()
    )
    
    # Find most common wealth range
    all_wealth_counts = pd.Series(0, index=wealth_order)
    for counts in wealth_data.values():
        for range_name, count in counts.items():
            all_wealth_counts[range_name] += count
    
    most_common = all_wealth_counts.idxmax()
    most_common_pct = (all_wealth_counts[most_common] / all_wealth_counts.sum() * 100)
    
    # Calculate percentage of known wealth ranges
    total_attendees = all_wealth_counts.sum()
    known_wealth = total_attendees - all_wealth_counts['Unknown']
    known_percentage = (known_wealth / total_attendees * 100) if total_attendees > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_high_capacity}</div>
            <div class='metric-label'>High-Capacity Attendees<br>($1M+)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{most_common}</div>
            <div class='metric-label'>Most Common Range<br>({most_common_pct:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{known_percentage:.1f}%</div>
            <div class='metric-label'>Known Wealth Range Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- Wealth Distribution by Session -------------------
    st.subheader("Wealth Distribution by Session")
    
    # Create DataFrame for plotting
    plot_data = []
    for session, counts in wealth_data.items():
        total = session_totals[session]
        for range_name in wealth_order:
            count = counts.get(range_name, 0)
            percentage = (count / total * 100) if total > 0 else 0
            plot_data.append({
                'Session': session,
                'Wealth Range': range_name,
                'Count': count,
                'Percentage': percentage
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    # Create stacked bar chart
    fig = px.bar(
        plot_df,
        x='Session',
        y='Percentage',
        color='Wealth Range',
        title='Wealth Range Distribution by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        category_orders={"Wealth Range": wealth_order},
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Wealth Range'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- High-Capacity Analysis -------------------
    st.subheader("High-Capacity Attendee Analysis")
    
    # Calculate high-capacity metrics for each session
    high_capacity_data = []
    for session, counts in wealth_data.items():
        total = session_totals[session]
        high_cap_count = sum(counts.get(range_name, 0) for range_name in high_capacity_ranges)
        high_cap_pct = (high_cap_count / total * 100) if total > 0 else 0
        
        high_capacity_data.append({
            'Session': session,
            'High-Capacity Count': high_cap_count,
            'High-Capacity Percentage': high_cap_pct,
            'Total Attendees': total
        })
    
    high_cap_df = pd.DataFrame(high_capacity_data)
    
    # Create bar chart for high-capacity metrics
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            name='High-Capacity Count',
            x=high_cap_df['Session'],
            y=high_cap_df['High-Capacity Count'],
            marker_color='rgb(55, 83, 109)'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            name='High-Capacity Percentage',
            x=high_cap_df['Session'],
            y=high_cap_df['High-Capacity Percentage'],
            mode='lines+markers',
            marker=dict(color='rgb(26, 118, 255)'),
            line=dict(color='rgb(26, 118, 255)')
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title_text="High-Capacity Attendees by Session",
        height=500,
        xaxis_tickangle=-45,
        showlegend=True
    )
    
    fig.update_yaxes(title_text="Number of High-Capacity Attendees", secondary_y=False)
    fig.update_yaxes(title_text="Percentage of Attendees (%)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Wealth Data Download -------------------
    st.subheader("Wealth Range Data")
    
    # Display the DataFrame
    st.dataframe(plot_df)
    
    # Create download link
    st.markdown(
        create_download_link(plot_df, "wealth_range_data.csv", "Download Wealth Range Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find session with highest high-capacity percentage
    highest_high_cap = high_cap_df.loc[high_cap_df['High-Capacity Percentage'].idxmax()]
    
    # Calculate wealth diversity for each session
    wealth_diversity = {}
    for session, counts in wealth_data.items():
        # Calculate Shannon diversity index excluding Unknown category
        known_counts = {k: v for k, v in counts.items() if k != 'Unknown'}
        if known_counts:
            total = sum(known_counts.values())
            proportions = [count/total for count in known_counts.values()]
            diversity = -sum(p * np.log(p) for p in proportions if p > 0)
            wealth_diversity[session] = diversity
    
    most_diverse_session = max(wealth_diversity.items(), key=lambda x: x[1])[0] if wealth_diversity else "None"
    
    # Calculate concentration of wealth
    top_ranges = ["$1M-$5M", "Over $5M"]
    total_top = sum(all_wealth_counts[range_name] for range_name in top_ranges)
    wealth_concentration = (total_top / known_wealth * 100) if known_wealth > 0 else 0
    
    # Generate insights
    insights = {
        "High-capacity attraction": f"{highest_high_cap['Session']} had the highest percentage of high-capacity attendees at {highest_high_cap['High-Capacity Percentage']:.1f}%",
        "Wealth diversity": f"{most_diverse_session} showed the most diverse wealth range distribution",
        "Wealth concentration": f"High-capacity individuals ($1M+) represent {wealth_concentration:.1f}% of attendees with known wealth ranges"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **High-Capacity Engagement**: Develop specialized engagement strategies for sessions attracting high-capacity attendees.
    
    2. **Wealth Range Targeting**: Tailor session topics and marketing to specific wealth range segments.
    
    3. **Data Completion**: Implement strategies to increase the percentage of attendees with known wealth ranges.
    
    4. **Balanced Programming**: Create diverse programming that appeals to attendees across different wealth ranges.
    
    5. **Strategic Partnerships**: Leverage sessions with high concentrations of wealthy attendees for major gift opportunities.
    """)

def session_roi_analysis(all_sheets):
    """Calculate the return on investment for each session"""
    st.markdown("<h3 class='section-header'>Session-Specific ROI</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis calculates the "return on investment" for each session by measuring total giving
    from attendees compared to potential event costs.
    """)

def first_time_donor_analysis(all_sheets):
    """Identify which sessions were most effective at attracting first-time donors"""
    st.markdown("<h3 class='section-header'>First-Time Donor Acquisition</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis identifies which sessions were most effective at attracting first-time donors
    who hadn't given previously.
    """)

def af_dg_preferences(all_sheets):
    """Compare Annual Fund vs. Designated Giving preferences"""
    st.markdown("<h3 class='section-header'>Annual Fund vs. Designated Giving Preferences</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis compares the Annual Fund vs. Designated Giving ratios among attendees of different
    sessions to identify if certain topics inspire more restricted or unrestricted giving.
    """)

def class_year_giving_patterns(all_sheets):
    """Analyze if certain class years show stronger giving responses"""
    st.markdown("<h3 class='section-header'>Class Year Giving Patterns</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis examines if certain class years or decades show stronger giving responses to
    specific speaker topics.
    """) 