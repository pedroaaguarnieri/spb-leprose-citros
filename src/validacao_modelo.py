"""
UNIFATECIE - Undergraduate Thesis (TCC)
Author: Pedro Augusto de Andrade Guarniéri
Project: Degree-Day Model for Brevipalpus yothersi (formerly B. phoenicis; citrus leprosis mite)
File: validacao_modelo.py

Description:
Cross-references the anonymized field inspections with the weather history
(Open-Meteo API) and computes degree-day accumulation. Uses the thermal
parameters derived from Chiavegato (1986) by linear regression (Tb=10.12 C;
K=331 DD), matching those determined for B. yothersi by Castro-Reséndiz et
al. (2021) (Tb=10.2 C; K=331.7 DD).

NOTE: the "phase agreement" percentage printed at the end is EXPLORATORY.
Since generations overlap in mature orchards and the data comes from
routine commercial scouting (no phenological protocol), it does NOT
represent the model's statistical accuracy. The model's validation rests on
its physiological basis (see README).
"""

import pandas as pd
import requests
import datetime
import math
import os
import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import warnings
import os
import argparse

warnings.filterwarnings('ignore')

def fetch_weather_data(lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches weather data from the Open-Meteo API for a given coordinate and period.
    Returns a DataFrame with Date, Tmax and Tmin.
    """
    print(f"[1/4] Fetching weather data (Lat: {lat}, Lon: {lon})...")
    url_archive = f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min&timezone=America%2FSao_Paulo'
    url_forecast = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&past_days=92&forecast_days=0&daily=temperature_2m_max,temperature_2m_min&timezone=America%2FSao_Paulo'

    try:
        res = requests.get(url_archive).json()
        weather_hist = pd.DataFrame({
            'Date': pd.to_datetime(res['daily']['time']),
            'Tmax': res['daily']['temperature_2m_max'],
            'Tmin': res['daily']['temperature_2m_min']
        })

        res_f = requests.get(url_forecast).json()
        weather_recent = pd.DataFrame({
            'Date': pd.to_datetime(res_f['daily']['time']),
            'Tmax': res_f['daily']['temperature_2m_max'],
            'Tmin': res_f['daily']['temperature_2m_min']
        })

        weather = pd.concat([weather_hist, weather_recent]).drop_duplicates(subset=['Date']).sort_values('Date').reset_index(drop=True)
        print("      [OK] Weather data imported successfully.")
        return weather
    except Exception as e:
        print(f"      [ERROR] Failed to fetch weather data: {e}")
        exit(1)

def calc_degree_days(weather: pd.DataFrame, Tb: float) -> pd.DataFrame:
    """
    Computes the daily accumulated thermal energy using the simple-average method.
    """
    print("[2/4] Processing the biological model and accumulating thermal energy (degree-days)...")
    weather['Tmean'] = (weather['Tmax'] + weather['Tmin']) / 2
    weather['DD_Daily'] = weather['Tmean'].apply(lambda t: max(0, t - Tb) if pd.notnull(t) else 0)
    return weather

def load_and_cross_data(weather: pd.DataFrame, file_path: str, target_farm: str, K: int) -> tuple:
    """
    Reads the consolidated spreadsheet, filters the farm of interest and
    simulates the mite's biological cycles.
    """
    print(f"[3/4] Analyzing sampling records for farm '{target_farm}'...")
    if not os.path.exists(file_path):
        print(f"      [ERROR] Spreadsheet '{file_path}' not found.")
        exit(1)

    # Read the spreadsheet and safely filter by farm
    df = pd.read_excel(file_path)
    if df.shape[1] > 1:
        df = df[df.iloc[:, 1].astype(str).str.upper() == target_farm.upper()]
    else:
        print("      [ERROR] Unrecognized consolidated-spreadsheet format.")
        exit(1)

    # Map columns by index
    # [3]: PLOT, [5]: INCIDENCE, [6]: PERCENTAGE, [4]: DATE, [7]: OBSERVATION
    data = df.iloc[:, [3, 5, 6, 4, 7]].copy()
    data.columns = ['Plot', 'Incidence', 'Percentage', 'Date', 'Obs']
    data = data.dropna(subset=['Date'])
    data['Date'] = pd.to_datetime(data['Date'])
    data['Percentage'] = pd.to_numeric(data['Percentage'], errors='coerce').fillna(0)

    positives = data[data['Percentage'] > 0].copy()
    results = []

    print("\n--- DATA CROSS-CHECK: OBSERVATIONS VS. MATHEMATICAL FORECAST ---\n")
    for plot, samples in positives.groupby('Plot'):
        samples = samples.sort_values('Date')
        if len(samples) <= 1:
            continue

        biofix = samples['Date'].min()
        weather_plot = weather[weather['Date'] >= biofix].copy()
        weather_plot['Accumulated'] = weather_plot['DD_Daily'].cumsum()

        print(f"PLOT: {plot} | BIOFIX: {biofix.strftime('%d/%m/%Y')}")

        for i, row in samples.iloc[1:].iterrows():
            obs_date = row['Date']
            obs_text = str(row['Obs'])[:60].replace('\n', '') + '...'

            dd_now_arr = weather_plot[weather_plot['Date'] == obs_date]['Accumulated'].values
            if len(dd_now_arr) > 0:
                dd_now = dd_now_arr[0]
                cycle_pct = (dd_now / K) * 100
                current_gen = int(dd_now // K)

                # Exploratory heuristic: near the end/start of the cycle (>=80% or <=20%) -> adult-hatch peak
                stage = "Adult Emergence" if (cycle_pct % 100) >= 80 or (cycle_pct % 100) <= 20 else "Nymph/Incubation"

                print(f"  -> Inspection: {obs_date.strftime('%d/%m/%Y')} -> Accumulated: {dd_now:.1f} DD")
                print(f"    - Mathematical phase: {cycle_pct:.1f}% of the cycle (Generation {current_gen})")
                print(f"    - Theory indicates presence of: {stage}")

                results.append({
                    'Plot': plot,
                    'Inspection_Date': obs_date,
                    'Accumulated_DD': round(dd_now, 1),
                    'Cycle_Percentage': round(cycle_pct, 1),
                    'Theoretical_Stage': stage,
                    'Actual_Note': row['Obs']
                })

    return positives, results

def plot_and_export(positives: pd.DataFrame, results: list, weather: pd.DataFrame, K: int, out_dir: str):
    """
    Generates the thermal-evidence chart for a representative plot and exports
    the mathematical evidence table (raw validation data).
    """
    print("\n[4/4] Generating the scientific-evidence chart and exporting data...")
    os.makedirs(out_dir, exist_ok=True)

    # Draw the chart for the plot with the most samples
    if positives.empty:
        print("No positive observation was found to generate the chart.")
        return

    sample_plot = positives['Plot'].value_counts().idxmax()
    plot_samples = positives[positives['Plot'] == sample_plot].sort_values('Date')

    if not plot_samples.empty:
        biofix_ex = plot_samples['Date'].min()
        weather_ex = weather[weather['Date'] >= biofix_ex].copy()
        weather_ex['Accumulated'] = weather_ex['DD_Daily'].cumsum()

        plt.figure(figsize=(12, 6))
        plt.plot(weather_ex['Date'], weather_ex['Accumulated'], label='Accumulated Degree-Days', color='#2dd4a0', linewidth=2.5)

        max_dd = weather_ex['Accumulated'].max()
        generations = int(max_dd // K)
        for g in range(1, generations + 2):
            plt.axhline(y=g*K, color='#f05252', linestyle='--', alpha=0.5, label=f'Theoretical Hatch' if g==1 else "")

        for _, row in plot_samples.iterrows():
            dd_val_arr = weather_ex[weather_ex['Date'] == row['Date']]['Accumulated'].values
            if len(dd_val_arr) > 0:
                plt.scatter(row['Date'], dd_val_arr[0], color='#4d9ef7', s=100, zorder=5, edgecolors='black')
                plt.annotate('Inspection', (row['Date'], dd_val_arr[0]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)

        plt.title(f"Bioclimatic Evidence - Plot {sample_plot}", fontsize=14)
        plt.ylabel("Accumulated Thermal Energy (DD)", fontsize=11)
        plt.xlabel("Date", fontsize=11)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        fig_path = os.path.join(out_dir, 'grafico_validacao.png')
        plt.savefig(fig_path, dpi=300)
        print(f"      [OK] Chart saved to: {fig_path}")

    # Export the table
    df_proof = pd.DataFrame(results)
    if not df_proof.empty:
        table_path = os.path.join(out_dir, 'tabela_prova.xlsx')
        df_proof.to_excel(table_path, index=False)
        print(f"      [OK] Evidence table saved to: {table_path}")

        # --- AGREEMENT RATE (SMART NLP FILTERING OUT OTHER PESTS) ---
        import re
        total = len(df_proof)
        hits = 0
        misses = 0

        def is_leprosis(text, stage_regex):
            text = text.lower()
            parts = re.split(r'[,.;]', text)
            for part in parts:
                if re.search(stage_regex, part):
                    if re.search(r'(mexicano|falsa|ferrugem|purpureu|branco|verde|texano)', part):
                        if 'lepros' not in part and 'brevip' not in part:
                            continue
                    return True
            return False

        for _, r in df_proof.iterrows():
            theory = str(r['Theoretical_Stage']).lower()
            actual = str(r['Actual_Note']).lower()

            has_adult = is_leprosis(actual, r'\badult[oa]s?\b')
            has_nymph = is_leprosis(actual, r'\bninfas?\b')
            has_egg = is_leprosis(actual, r'\bovos?\b')

            match = False
            if 'emergence' in theory:
                if has_adult: match = True
                elif not has_adult and (has_nymph or has_egg): match = False
                else: match = True
            else:
                if has_nymph or has_egg: match = True
                elif has_adult and not has_nymph and not has_egg: match = False
                else: match = True

            if match: hits += 1
            else: misses += 1

        print("\n--- PHASE AGREEMENT (EXPLORATORY — NOT STATISTICAL ACCURACY) ---")
        print(f"Samples evaluated: {total}")
        print(f"Agreements: {hits} | Disagreements: {misses}")
        print(f"Raw agreement: {(hits/total)*100:.1f}%")
        print("Note: overlapping generations and routine data (no phenological protocol)")
        print("limit how this number should be read; the model's validation is physiological (see README).\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Validation of the leprosis-mite biological model")
    parser.add_argument('--lat', type=float, default=0.0, help='Farm latitude')
    parser.add_argument('--lon', type=float, default=0.0, help='Farm longitude')
    parser.add_argument('--start', type=str, default='2024-01-01', help='Weather start date (YYYY-MM-DD)')
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    parser.add_argument('--end', type=str, default=today_str, help='Weather end date (YYYY-MM-DD)')
    parser.add_argument('--input', type=str, default='../data/INSPECOES_CONSOLIDADAS.xlsx', help='Path to the input spreadsheet')
    parser.add_argument('--outdir', type=str, default='../results', help='Directory to save the chart and table')
    parser.add_argument('--farm', type=str, default='COMMERCIAL', help='Name of the target farm to process')

    args = parser.parse_args()

    print("="*80)
    print(" DEGREE-DAY MODEL (Brevipalpus yothersi - citrus leprosis mite)")
    print("="*80)

    Tb = 10.12 # Base temperature — regression on Chiavegato (1986); cf. 10.2 C in Castro-Reséndiz et al. (2021)
    K = 331    # Egg-to-adult thermal constant (DD); cf. 331.7 DD in Castro-Reséndiz et al. (2021)

    weather_df = fetch_weather_data(args.lat, args.lon, args.start, args.end)
    weather_df = calc_degree_days(weather_df, Tb)
    positives_df, validation_results = load_and_cross_data(weather_df, args.input, args.farm, K)
    plot_and_export(positives_df, validation_results, weather_df, K, args.outdir)

    print("="*80)
    print(" PROCESS COMPLETE. RESULTS AVAILABLE IN THE OUTPUT FOLDER.")
    print("="*80)
