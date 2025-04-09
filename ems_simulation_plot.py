import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("EMS Simulation: Solar + Greenhouse + Battery")

# パラメータ入力
n_days = st.sidebar.slider("Number of days to simulate", 1, 30, 14)
battery_capacity = st.sidebar.number_input("Battery capacity (kWh)", min_value=1, max_value=20, value=5)

# データ生成
steps_per_day = 48
total_steps = n_days * steps_per_day
time_index = pd.date_range(start='2025-04-01', periods=total_steps, freq='30min')

daily_temp_shift = np.repeat(np.random.normal(0, 1.5, n_days), steps_per_day)
daily_solar_scale = np.repeat(np.random.uniform(0.8, 1.2, n_days), steps_per_day)

hour_fraction = time_index.hour + time_index.minute / 60
temperature = 10 + 8 * np.sin((hour_fraction - 6) * np.pi / 12) + daily_temp_shift
solar_generation = daily_solar_scale * np.clip(5 * np.sin((hour_fraction - 6) * np.pi / 12), 0, None)
demand = 3 + np.clip(15 - temperature, 0, None) * 0.3

battery_level = [10]
grid_power = []

for i in range(total_steps):
    delta = solar_generation[i] - demand[i]
    current_level = battery_level[-1]

    if delta > 0:
        charge = min(delta, battery_capacity - current_level)
        battery_level.append(current_level + charge)
        grid_power.append(delta - charge)
    else:
        discharge = min(-delta, current_level)
        battery_level.append(current_level - discharge)
        grid_power.append(delta + discharge)

df = pd.DataFrame({
    "Time": time_index,
    "Temperature (°C)": temperature,
    "Solar Gen (kWh)": solar_generation,
    "Demand (kWh)": demand,
    "Battery Level (kWh)": battery_level[1:],
    "Grid Power (kWh)": grid_power
})

# 表示範囲
zoom_days = st.slider("Zoom: how many days to display?", 1, n_days, 3)
zoom_df = df.iloc[:zoom_days * steps_per_day]

# 合計
total_purchase = sum(p for p in df["Grid Power (kWh)"] if p > 0)
total_sell = sum(-p for p in df["Grid Power (kWh)"] if p < 0)

# グラフ描画
fig, axs = plt.subplots(4, 1, figsize=(14, 18), sharex=True)

axs[0].plot(zoom_df["Time"], zoom_df["Temperature (°C)"], color='orange')
axs[0].set_ylabel("Temperature (°C)")
axs[0].grid(True)

axs[1].plot(zoom_df["Time"], zoom_df["Solar Gen (kWh)"], label="Solar Gen", color='green')
axs[1].plot(zoom_df["Time"], zoom_df["Demand (kWh)"], label="Demand", color='red')
axs[1].legend()
axs[1].set_ylabel("Energy (kWh)")
axs[1].grid(True)

axs[2].plot(zoom_df["Time"], zoom_df["Battery Level (kWh)"], color='blue')
axs[2].set_ylabel("Battery Level (kWh)")
axs[2].grid(True)

axs[3].bar(zoom_df["Time"], zoom_df["Grid Power (kWh)"], color='purple')
axs[3].set_ylabel("Grid Power (kWh)")
axs[3].set_xlabel("Time")
axs[3].grid(True)

st.pyplot(fig)

st.markdown(f"**Total purchase over {n_days} days:** `{total_purchase:.2f} kWh`")
st.markdown(f"**Total sell over {n_days} days:** `{total_sell:.2f} kWh`")

