"""
Module to process and consolidate pest-inspection scouting spreadsheets.
UNIFATECIE - Undergraduate Thesis (TCC)
Author: Pedro Augusto de Andrade Guarniéri
Project: Degree-Day Model for Brevipalpus yothersi (formerly B. phoenicis; citrus leprosis mite)
File: processar_planilhas.py

Description:
ETL (Extract, Transform, Load) and NLP script that converts raw scouting
spreadsheets into a structured, anonymized dataset.
"""

import os
import pandas as pd
import glob
import re
import argparse

def process_files(input_dir: str, output_name: str) -> None:
    """
    Scans a directory for 'INSPEÇÃO DE PRAGAS*.xlsx' spreadsheets, reads each
    sheet, identifies the columns of interest from the (merged) header row,
    and compiles everything into a single consolidated DataFrame.
    """
    print(f"Searching for raw spreadsheets in: {os.path.abspath(input_dir)}")
    files = glob.glob(os.path.join(input_dir, "INSPEÇÃO DE PRAGAS *.xlsx"))

    if not files:
        print("No raw spreadsheet found. Skipping the processing step.")
        return

    all_data = []

    for file in files:
        # Extract the season from the file name (e.g. "INSPEÇÃO DE PRAGAS 2026.xlsx" -> 2026)
        match = re.search(r"(\d{4})", os.path.basename(file))
        season = match.group(1) if match else "Unknown"

        xl = pd.ExcelFile(file)

        for sheet in xl.sheet_names:
            if sheet.upper() == 'TODAS':
                continue

            df = pd.read_excel(xl, sheet_name=sheet, header=None)

            # Initialize column mappers
            col_farm, col_plot, col_date, col_obs, col_leprosis = -1, -1, -1, -1, -1

            # Look for the columns in the first 6 rows (handles merged headers)
            for i in range(6):
                if i >= len(df):
                    break
                row_values = df.iloc[i].tolist()
                for j, val in enumerate(row_values):
                    val_str = str(val).upper().strip()
                    if val_str == "FAZENDA": col_farm = j
                    if "QUAD" in val_str: col_plot = j
                    if "DATA DA INSPE" in val_str: col_date = j
                    if "OBSERVA" in val_str: col_obs = j
                    if val_str == "LEPROSE": col_leprosis = j

            # Fallback in case the header could not be read (default indices)
            if col_farm == -1: col_farm = 0
            if col_plot == -1: col_plot = 3
            if col_date == -1: col_date = 66
            if col_obs == -1: col_obs = 67
            if col_leprosis == -1: col_leprosis = 11

            # Trim the data, skipping the header (starting from row 6)
            data_rows = df.iloc[5:].copy()

            cols_to_extract = {
                col_farm: 'FARM',
                col_plot: 'PLOT',
                col_date: 'DATE',
                col_obs: 'OBSERVATION',
                col_leprosis: 'INCIDENCE',
                col_leprosis + 1: 'PERCENTAGE'
            }

            cols_to_extract_safe = {k: v for k, v in cols_to_extract.items() if k in data_rows.columns}
            extracted = data_rows[list(cols_to_extract_safe.keys())].rename(columns=cols_to_extract_safe)

            # Initialize columns that were not found with None
            for v in cols_to_extract.values():
                if v not in extracted.columns:
                    extracted[v] = None

            extracted['SEASON'] = season
            extracted['SOURCE_SHEET'] = sheet

            # Clean up junk rows (copied headers or empty rows)
            extracted = extracted.dropna(subset=['PLOT'])
            extracted = extracted[~extracted['PLOT'].astype(str).str.upper().str.contains("QUADRA")]

            all_data.append(extracted)

    if not all_data:
        print("No valid data could be extracted from the spreadsheets.")
        return

    # Consolidate the global dataframe
    final_df = pd.concat(all_data, ignore_index=True)

    # --- DATA ANONYMIZATION (academic privacy) ---
    # Replaces real farm names with generic labels (e.g. FARM_01)
    if 'FARM' in final_df.columns:
        unique_names = final_df['FARM'].dropna().unique()
        anon_map = {name: f"FARM_{str(i+1).zfill(2)}" for i, name in enumerate(unique_names)}
        final_df['FARM'] = final_df['FARM'].map(anon_map).fillna(final_df['FARM'])
        print(f"Data anonymized successfully. Farms processed: {len(unique_names)}")

    # Cascading forward-fill of the date within each farm
    final_df['DATE'] = final_df['DATE'].ffill()

    # Advanced natural-language processing (pest-collision filter)
    import re
    def guarded_nlp(texts, stage_regex):
        """Flags mentions of a life stage in the free-text field, while filtering out
        unrelated pests whose names share the same Portuguese stage words (egg/nymph/adult)."""
        flags = []
        for text in texts:
            text_str = str(text).lower()
            if text_str == 'nan' or text_str == 'none':
                flags.append(False)
                continue

            found = False
            parts = re.split(r'[,.;]', text_str)
            for part in parts:
                if re.search(stage_regex, part):
                    if re.search(r'(mexicano|falsa|ferrugem|purpureu|branco|verde|texano)', part):
                        if 'lepros' not in part and 'brevip' not in part:
                            continue
                    found = True
                    break
            flags.append(found)
        return flags

    final_df['EGG_PRESENT'] = guarded_nlp(final_df['OBSERVATION'], r'\bovos?\b')
    final_df['NYMPH_PRESENT'] = guarded_nlp(final_df['OBSERVATION'], r'\bninfas?\b')
    final_df['ADULT_PRESENT'] = guarded_nlp(final_df['OBSERVATION'], r'\badult[oa]s?\b')

    # Order columns
    cols = ['SEASON', 'FARM', 'SOURCE_SHEET', 'PLOT', 'DATE', 'INCIDENCE', 'PERCENTAGE', 'OBSERVATION',
            'EGG_PRESENT', 'NYMPH_PRESENT', 'ADULT_PRESENT']

    final_df = final_df[[c for c in cols if c in final_df.columns]]

    # Save the final spreadsheet
    out_path = os.path.join(input_dir, output_name)
    final_df.to_excel(out_path, index=False)

    print(f"Data consolidated successfully into: {out_path}")
    print(f"Total records compiled: {len(final_df)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Consolidates raw pest-inspection spreadsheets.")
    parser.add_argument('--input_dir', type=str, default='../data', help='Directory where the raw spreadsheets are.')
    parser.add_argument('--output_name', type=str, default='INSPECOES_CONSOLIDADAS.xlsx', help='Name of the consolidated output file.')
    args = parser.parse_args()

    process_files(args.input_dir, args.output_name)
