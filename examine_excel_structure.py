#!/usr/bin/env python
"""
Script to examine the Excel file structure to understand column layout
"""

import os
import openpyxl

def examine_excel_structure():
    """Examine the Excel file structure"""

    try:
        # Load the quarterly plan Excel file
        excel_file = "02 Quarter Plan.xlsx"
        if not os.path.exists(excel_file):
            print(f"Excel file {excel_file} not found")
            return

        workbook = openpyxl.load_workbook(excel_file, data_only=True)

        print("Sheet names:", workbook.sheetnames)

        # Examine FPI sheet structure
        if 'FPI' in workbook.sheetnames:
            fpi_sheet = workbook['FPI']
            print(f"\n=== FPI Sheet ===")
            print(f"Max row: {fpi_sheet.max_row}, Max col: {fpi_sheet.max_column}")

            # Print first 10 rows to understand structure
            for row_num in range(1, min(11, fpi_sheet.max_row + 1)):
                row_data = []
                for col in range(1, min(15, fpi_sheet.max_column + 1)):  # First 15 columns
                    cell_value = fpi_sheet.cell(row=row_num, column=col).value
                    row_data.append(str(cell_value) if cell_value is not None else "")
                print(f"Row {row_num}: {row_data}")

        # Examine GPI-W sheet structure
        if 'GPI-W' in workbook.sheetnames:
            gpi_w_sheet = workbook['GPI-W']
            print(f"\n=== GPI-W Sheet ===")
            print(f"Max row: {gpi_w_sheet.max_row}, Max col: {gpi_w_sheet.max_column}")

            # Print first 10 rows to understand structure
            for row_num in range(1, min(11, gpi_w_sheet.max_row + 1)):
                row_data = []
                for col in range(1, min(20, gpi_w_sheet.max_column + 1)):  # First 20 columns
                    cell_value = gpi_w_sheet.cell(row=row_num, column=col).value
                    row_data.append(str(cell_value) if cell_value is not None else "")
                print(f"Row {row_num}: {row_data}")

        # Examine GPI-M sheet structure
        if 'GPI-M' in workbook.sheetnames:
            gpi_m_sheet = workbook['GPI-M']
            print(f"\n=== GPI-M Sheet ===")
            print(f"Max row: {gpi_m_sheet.max_row}, Max col: {gpi_m_sheet.max_column}")

            # Print first 10 rows to understand structure
            for row_num in range(1, min(11, gpi_m_sheet.max_row + 1)):
                row_data = []
                for col in range(1, min(15, gpi_m_sheet.max_column + 1)):  # First 15 columns
                    cell_value = gpi_m_sheet.cell(row=row_num, column=col).value
                    row_data.append(str(cell_value) if cell_value is not None else "")
                print(f"Row {row_num}: {row_data}")

    except Exception as e:
        print(f"Error examining Excel structure: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_excel_structure()