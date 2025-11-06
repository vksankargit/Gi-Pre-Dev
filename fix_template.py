import openpyxl

# Load the template file
wb = openpyxl.load_workbook('Annual_Plan_Template.xlsx')

# Get the PPIs sheet
ppi_sheet = wb['PPIs']

# Find and fix the column name in row 4
for row in ppi_sheet.iter_rows(min_row=4, max_row=4):
    for cell in row:
        if cell.value and 'Completion Criteri' in str(cell.value):
            print(f"Found typo in cell {cell.coordinate}: '{cell.value}'")
            cell.value = cell.value.replace('Completion Criteri', 'Completion Criteria')
            print(f"Fixed to: '{cell.value}'")

# Save the file
wb.save('Annual_Plan_Template.xlsx')
print("Template file updated successfully!")
