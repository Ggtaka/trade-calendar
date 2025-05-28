import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import calendar
import matplotlib.patches as mpatches
from db import init_db, insert_trade, get_all_trades, get_trades_by_date, delete_all_trades

conn = init_db()
st.set_page_config("Trade Calendar", layout="wide")

# 📐 Custom CSS for larger fonts
st.markdown("""
    <style>
    .stTitle { font-size: 32px !important; }
    .stMarkdown h2 { font-size: 28px !important; }
    .stMarkdown p { font-size: 18px !important; }
    .element-container { font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Trade Calendar with SQLite (Tradovate Format)")

# Sidebar: Upload and Delete
with st.sidebar:
    st.header("📁 Upload Tradovate CSV")
    csv_file = st.file_uploader("Upload Tradovate File", type="csv")

    if st.button("🗑 Delete All Trades"):
        delete_all_trades(conn)
        st.warning("All trades deleted.")

# Upload handler
if csv_file:
    df = pd.read_csv(csv_file)
    df['pnl'] = df['pnl'].replace('[\$,()]', '', regex=True).astype(float) * df['pnl'].str.contains('\(').apply(lambda x: -1 if x else 1)
    df['boughtTimestamp'] = pd.to_datetime(df['boughtTimestamp'], errors='coerce')
    df['date'] = df['boughtTimestamp'].dt.date
    df['timestamp'] = df['boughtTimestamp'].astype(str)

    for _, row in df.iterrows():
        insert_trade(conn, (
            str(row['date']),
            row['symbol'],
            int(row['qty']),
            row['pnl'],
            row['timestamp']
        ))

# Load trades from database
trades = pd.DataFrame(get_all_trades(conn), columns=["ID", "Date", "Symbol", "Qty", "PnL", "Timestamp"])
trades["Date"] = pd.to_datetime(trades["Date"])
summary = trades.groupby(trades["Date"].dt.date).agg(PnL=('PnL', 'sum'), Trades=('ID', 'count')).reset_index()
summary["Date"] = pd.to_datetime(summary["Date"])

# Calendar view
if not summary.empty:
    year = summary["Date"].dt.year.max()
    month = summary["Date"].dt.month.max()

    st.subheader(f"{calendar.month_name[month]} {year} Trade Calendar")

    cal = calendar.Calendar()
    weeks = list(cal.monthdayscalendar(year, month))
    pnl_map = summary.set_index(summary["Date"].dt.day)["PnL"].to_dict()
    trade_map = summary.set_index(summary["Date"].dt.day)["Trades"].to_dict()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_axis_off()

    for row, week in enumerate(weeks):
        for col, day in enumerate(week):
            if day == 0:
                continue
            pnl = pnl_map.get(day, 0)
            trades_count = trade_map.get(day, 0)
            color = "#d4f4dd" if pnl > 0 else "#f4d4d4" if pnl < 0 else "#e0e0e0"
            ax.add_patch(plt.Rectangle((col, -row), 1, 1, color=color, edgecolor='gray'))
            ax.text(col + 0.05, -row + 0.8, f"{day}", ha='left', va='top', fontsize=8, weight='bold')
            ax.text(col + 0.5, -row + 0.5, f"${pnl:.2f}", ha='center', va='center', fontsize=8)
            ax.text(col + 0.5, -row + 0.2, f"{trades_count} trades", ha='center', va='center', fontsize=7)

    ax.set_title(f"{calendar.month_name[month]} {year} Trade Calendar", fontsize=14, weight='bold')
    legend_items = [
        mpatches.Patch(color="#d4f4dd", label='Profit Day'),
        mpatches.Patch(color="#f4d4d4", label='Loss Day'),
        mpatches.Patch(color="#e0e0e0", label='No Trades'),
    ]
    ax.legend(handles=legend_items, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3)
    st.pyplot(fig)

    # Trade detail view
    st.subheader("📋 View Trade Details")
    selected_date = st.date_input("Select a date to view trades")
    trades_for_day = trades[trades["Date"].dt.date == selected_date]
    if not trades_for_day.empty:
        st.markdown(f"### Trades for {selected_date}")
        st.dataframe(trades_for_day)
    else:
        st.info("No trades for this date.")
else:
    st.info("Upload a Tradovate CSV to begin.")
