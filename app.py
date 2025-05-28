import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import calendar
import matplotlib.patches as mpatches

st.set_page_config(page_title="Trade Calendar Dashboard", layout="centered")

st.title("📊 Trade Calendar Dashboard")

uploaded_file = st.file_uploader("Upload your Tradovate CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Clean and convert PnL values
    df['pnl'] = df['pnl'].replace('[\\$,()]', '', regex=True).astype(float) * df['pnl'].str.contains('\\(').apply(lambda x: -1 if x else 1)
    
    # Convert timestamps
    df['boughtTimestamp'] = pd.to_datetime(df['boughtTimestamp'], errors='coerce')
    df['date'] = df['boughtTimestamp'].dt.date

    # Aggregate daily PnL and trade count
    daily_summary = df.groupby('date').agg(PnL=('pnl', 'sum'), Trades=('pnl', 'count')).reset_index()
    daily_summary['Date'] = pd.to_datetime(daily_summary['date'])

    if not daily_summary.empty:
        st.subheader("📆 Calendar View")

        year = daily_summary['Date'].dt.year.iloc[0]
        month = daily_summary['Date'].dt.month.iloc[0]

        cal = calendar.Calendar(firstweekday=0)
        days = list(cal.itermonthdays(year, month))
        weeks = [days[i:i+7] for i in range(0, len(days), 7)]

        pnl_map = daily_summary.set_index(daily_summary['Date'].dt.day)['PnL'].to_dict()
        trade_map = daily_summary.set_index(daily_summary['Date'].dt.day)['Trades'].to_dict()

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_axis_off()

        for row, week in enumerate(weeks):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                pnl = pnl_map.get(day, 0)
                trades = trade_map.get(day, 0)
                color = "#d4f4dd" if pnl > 0 else "#f4d4d4" if pnl < 0 else "#e0e0e0"
                ax.add_patch(plt.Rectangle((col, -row), 1, 1, color=color, edgecolor='gray'))
                ax.text(col + 0.05, -row + 0.8, f"{day}", ha='left', va='top', fontsize=8, weight='bold')
                ax.text(col + 0.5, -row + 0.4, f"${pnl:.2f}", ha='center', va='center', fontsize=7)
                ax.text(col + 0.5, -row + 0.15, f"{trades} trades", ha='center', va='center', fontsize=6)

        ax.set_title(f"{calendar.month_name[month]} {year} Trade Calendar", fontsize=14, weight='bold')
        legend_items = [
            mpatches.Patch(color="#d4f4dd", label='Profit Day'),
            mpatches.Patch(color="#f4d4d4", label='Loss Day'),
            mpatches.Patch(color="#e0e0e0", label='No Trades'),
        ]
        ax.legend(handles=legend_items, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3)
        st.pyplot(fig)
