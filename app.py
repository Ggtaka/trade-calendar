# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import calendar
import matplotlib.patches as mpatches
from db import init_db, insert_trade, get_all_trades, get_trades_by_date

conn = init_db()
st.set_page_config("Trade Calendar", layout="wide")

st.title("📊 Trade Calendar with SQLite")

# Add a trade form
with st.sidebar:
    st.header("➕ Add Trade")
    with st.form("new_trade"):
        date = st.date_input("Trade Date")
        symbol = st.text_input("Symbol")
        qty = st.number_input("Quantity", step=1, value=1)
        buy_price = st.number_input("Buy Price")
        sell_price = st.number_input("Sell Price")
        pnl = (sell_price - buy_price) * qty
        timestamp = st.text_input("Timestamp", value=str(pd.Timestamp.now()))
        submitted = st.form_submit_button("Add")
        if submitted:
            insert_trade(conn, (str(date), symbol, qty, buy_price, sell_price, pnl, timestamp))
            st.success("Trade added.")

# Load trades
trades = pd.DataFrame(get_all_trades(conn), columns=["ID", "Date", "Symbol", "Qty", "Buy", "Sell", "PnL", "Timestamp"])
trades["Date"] = pd.to_datetime(trades["Date"])
summary = trades.groupby(trades["Date"].dt.date).agg(PnL=('PnL', 'sum'), Trades=('ID', 'count')).reset_index()
summary["Date"] = pd.to_datetime(summary["Date"])

# Calendar View
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
        ax.text(col + 0.5, -row + 0.4, f"${pnl:.2f}", ha='center', va='center', fontsize=7)
        ax.text(col + 0.5, -row + 0.15, f"{trades_count} trades", ha='center', va='center', fontsize=6)

ax.set_title(f"{calendar.month_name[month]} {year} Trade Calendar", fontsize=14, weight='bold')
st.pyplot(fig)

# Click-to-view details
selected_date = st.date_input("Select a date to view trades")
selected_trades = pd.DataFrame(get_trades_by_date(conn, str(selected_date)),
                               columns=["ID", "Date", "Symbol", "Qty", "Buy", "Sell", "PnL", "Timestamp"])
if not selected_trades.empty:
    st.subheader(f"Trades on {selected_date}")
    st.dataframe(selected_trades)
