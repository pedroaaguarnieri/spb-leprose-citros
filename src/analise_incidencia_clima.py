# -*- coding: utf-8 -*-
"""
Leprosis incidence x thermal regime/season analysis — Brevipalpus yothersi.
UNIFATECIE — Undergraduate thesis (TCC) | Author: Pedro Augusto de Andrade Guarniéri

An honest, defensible analysis of the field data: instead of treating the
"phase agreement" percentage as accuracy (which does not hold, given
overlapping generations), this looks at the relationship between monthly
leprosis incidence and the thermal/rainfall regime. Generates a figure and
prints the correlations.

NOTE (expected): instantaneous incidence does NOT correlate strongly with
the month's temperature, because the observed population reflects heat
accumulated over weeks, already filtered by rain, natural enemies and
sprays. This reinforces the case for a mechanistic (degree-day) model
instead of reactive scouting.
"""
import os
import argparse
import numpy as np
import pandas as pd
import requests
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TB = 10.12  # base temperature (Chiavegato, 1986)


def main(data_path, lat, lon, out_dir):
    df = pd.read_excel(data_path)
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df = df.dropna(subset=['DATE'])
    df['PERCENTAGE'] = pd.to_numeric(df['PERCENTAGE'], errors='coerce').fillna(0)
    df = df[(df['DATE'] >= '2024-01-01') & (df['DATE'] <= '2026-05-31')]
    df['ym'] = df['DATE'].dt.to_period('M')

    n_tot = len(df); n_pos = int((df['PERCENTAGE'] > 0).sum())
    print(f"Inspections: {n_tot} | positive for leprosis: {n_pos}")

    url = ('https://archive-api.open-meteo.com/v1/archive'
           f'?latitude={lat}&longitude={lon}&start_date=2024-01-01&end_date=2026-05-31'
           '&daily=temperature_2m_max,temperature_2m_min,precipitation_sum'
           '&timezone=America%2FSao_Paulo')
    dj = requests.get(url, timeout=60).json()['daily']
    cl = pd.DataFrame({'DATE': pd.to_datetime(dj['time']),
                       'Tmax': dj['temperature_2m_max'], 'Tmin': dj['temperature_2m_min'],
                       'Prec': dj['precipitation_sum']})
    cl['Tmean'] = (cl['Tmax'] + cl['Tmin']) / 2
    cl['DD'] = (cl['Tmean'] - TB).clip(lower=0)
    cl['ym'] = cl['DATE'].dt.to_period('M')

    insp = df.groupby('ym').agg(n=('PERCENTAGE', 'size'),
                                pos=('PERCENTAGE', lambda x: (x > 0).sum())).reset_index()
    insp['rate'] = 100 * insp['pos'] / insp['n']
    clm = cl.groupby('ym').agg(Tmean=('Tmean', 'mean'), DD=('DD', 'sum'), Prec=('Prec', 'sum')).reset_index()
    m = insp.merge(clm, on='ym')
    m = m[m['n'] >= 5]

    print(f"\nCorrelations (n={len(m)} months):")
    for xv, xl in [('Tmean', 'Mean temp.'), ('DD', 'Degree-days'), ('Prec', 'Precipitation')]:
        r, p = stats.pearsonr(m[xv], m['rate'])
        print(f"  positive rate x {xl:14s}: r = {r:+.2f} (p = {p:.3f})")

    # Figure: seasonality (calendar month) + temperature
    df['month'] = df['DATE'].dt.month
    seas = df.groupby('month').agg(n=('PERCENTAGE', 'size'),
                                pos=('PERCENTAGE', lambda x: (x > 0).sum())).reset_index()
    seas['rate'] = 100 * seas['pos'] / seas['n']
    cl['month'] = cl['DATE'].dt.month
    seas = seas.merge(cl.groupby('month')['Tmean'].mean().reset_index(), on='month')
    full = pd.DataFrame({'month': range(1, 13)}).merge(seas, on='month', how='left')
    lbl = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    os.makedirs(out_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(full['month'], full['rate'], color='#2e8b57', alpha=0.85, label='Positive inspections for leprosis (%)')
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(lbl)
    ax.set_ylabel('Positive inspections for leprosis (%)', color='#2e8b57'); ax.set_xlabel('Month')
    ax2 = ax.twinx()
    ax2.plot(full['month'], full['Tmean'], color='#d9480f', marker='o', lw=2, label='Mean temperature (°C)')
    ax2.set_ylabel('Mean temperature (°C)', color='#d9480f')
    ax.set_title('Seasonality of leprosis incidence and temperature', fontsize=12.5)
    ax.grid(alpha=0.2, axis='y')
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc='upper right', fontsize=9.5)
    plt.tight_layout()
    out = os.path.join(out_dir, 'fig_incidencia_clima.png')
    plt.savefig(out, dpi=200)
    print(f"\nFigure saved: {out}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Leprosis incidence x weather analysis.')
    ap.add_argument('--input', default='../data/INSPECOES_CONSOLIDADAS.xlsx')
    ap.add_argument('--lat', type=float, default=-23.079, help='Latitude (default: Paranavaí, Brazil)')
    ap.add_argument('--lon', type=float, default=-52.465, help='Longitude (default: Paranavaí, Brazil)')
    ap.add_argument('--outdir', default='../results')
    a = ap.parse_args()
    main(a.input, a.lat, a.lon, a.outdir)
