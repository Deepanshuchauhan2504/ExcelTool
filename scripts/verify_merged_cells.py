import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

import polars as pl
import xlsxwriter
from core.data_manager import DataManager

def create_test_excel(filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()

    # Write headers
    headers = ["Category", "Subcategory", "Value"]
    for i, h in enumerate(headers):
        worksheet.write(0, i, h)

    # Write merged cells
    # Row 1-3 merged for Category "Fruit"
    worksheet.merge_range('A2:A4', 'Fruit')
    
    # Subcategories and Values (not merged)
    data = [
        [None, "Apple", 10],
        [None, "Banana", 20],
        [None, "Cherry", 30],
        ["Vegetable", "Carrot", 5],
        ["Vegetable", "Broccoli", 15]
    ]

    for r, row_data in enumerate(data, start=1):
        if row_data[0] is not None and r > 3: # Manual write for non-merged
             worksheet.write(r, 0, row_data[0])
        worksheet.write(r, 1, row_data[1])
        worksheet.write(r, 2, row_data[2])

    workbook.close()
    print(f"Created {filename}")

def verify():
    test_file = "test_merged.xlsx"
    create_test_excel(test_file)
    
    dm = DataManager()
    success, msg = dm.load_from_path(test_file)
    
    if not success:
        print(f"Load failed: {msg}")
        return

    print("File loaded.")

    # Apply Forward Fill on 'Category'
    dm.apply_forward_fill(['Category'])
    
    categories = dm.df['Category'].to_list()
    print(f"Categories after fill: {categories}")

    expected = ['Fruit', 'Fruit', 'Fruit', 'Vegetable', 'Vegetable']
    
    if categories == expected:
        print("\nVerification SUCCESS: Forward fill worked as expected!")

    else:
        print(f"\n❌ Verification FAILED: Expected {expected}, got {categories}")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    verify()
