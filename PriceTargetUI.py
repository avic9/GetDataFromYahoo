import os
import tkinter as tk

from price_target_service import build_report, load_rows_from_xml, save_rows_to_xml, update_rows_from_yahoo


class DataEntryTable:
    def __init__(self, root, rows, cols, headers):
        self.root = root
        self.rows = rows
        self.cols = cols
        self.entries = {}

        # Display Column Headers
        for col_idx, header in enumerate(headers):
            lbl = tk.Label(root, text=header, font=('Arial', 10, 'bold'))
            lbl.grid(row=0, column=col_idx, padx=5, pady=5)

        # Generate Input Grid
        for row in range(1, rows + 1):
            for col in range(cols):
                entry = tk.Entry(root, width=15)
                entry.grid(row=row, column=col, padx=2, pady=2)
                self.entries[(row, col)] = entry

        # Load existing data from XML if available
        self.load_from_xml()

        # Submit Button
        btn = tk.Button(root, text="Get Data", command=self.print_data)
        btn.grid(row=rows+1, column=0, pady=10)

        # Update From Yahoo Button
        btn_yahoo = tk.Button(root, text="Update From Yahoo", command=self.update_from_yahoo)
        btn_yahoo.grid(row=rows+1, column=1, pady=10)



#######################################################################################
#    This function is responsible for loading the data from an XML file into the GUI.
#    its call at the initialization of the DataEntryTable class to populate 
#    the input fields with existing data if available.
#######################################################################################

    def load_from_xml(self):
        xml_path = r"D:\avi\TargetPrice\price_targets.xml"
        rows = load_rows_from_xml(xml_path)

        row_idx = 1
        for row in rows[:self.rows]:
            if row_idx <= self.rows:
                self.entries[(row_idx, 0)].insert(0, row.get("TickerName", ""))
                self.entries[(row_idx, 1)].insert(0, row.get("TargetPrice", ""))
                self.entries[(row_idx, 2)].insert(0, row.get("CurrentPrice", ""))
                self.entries[(row_idx, 3)].insert(0, row.get("PERatio", ""))
                self.entries[(row_idx, 4)].insert(0, row.get("ROIC", ""))
                row_idx += 1

        print(f"Data loaded from {xml_path}")



#######################################################################################
#     This function is responsible for printing the data entered by the user in the GUI.
#     And it also calls the save_to_xml function to save the data to an XML file.
#######################################################################################

    def print_data(self):
        print("\n--- User Entered Data ---")
        rows = []
        for row in range(1, self.rows + 1):
            row_data = [self.entries[(row, col)].get() for col in range(self.cols)]
            print(row_data)
            rows.append({
                "TickerName": row_data[0],
                "TargetPrice": row_data[1],
                "CurrentPrice": row_data[2],
                "PERatio": row_data[3],
                "ROIC": row_data[4],
            })

        self.save_to_xml(rows)



#######################################################################################
#     Save the tickers from GUI to an XML file in the specified directory. 
#     The XML structure will have a root element "PriceTargets" 
#     and each entry will be represented as an "Entry" element with attributes for TickerName, 
#     TargetPrice, CurrentPrice, PERatio, and ROIC.    
#######################################################################################
    def save_to_xml(self, rows=None):
        if rows is None:
            rows = []
            for row in range(1, self.rows + 1):
                row_data = [self.entries[(row, col)].get() for col in range(self.cols)]
                rows.append({
                    "TickerName": row_data[0],
                    "TargetPrice": row_data[1],
                    "CurrentPrice": row_data[2],
                    "PERatio": row_data[3],
                    "ROIC": row_data[4],
                })

        output_path = save_rows_to_xml(rows)
        print(f"Data saved to {output_path}")


#######################################################################################
#     This function fetches current stock prices, P/E ratio, and ROIC from Yahoo Finance 
#     for each ticker entered in the GUI and updates the corresponding columns.
#######################################################################################
    def update_from_yahoo(self):
        print("\n--- Updating prices from Yahoo Finance ---")
        rows = []
        for row in range(1, self.rows + 1):
            row_data = [self.entries[(row, col)].get() for col in range(self.cols)]
            rows.append({
                "TickerName": row_data[0],
                "TargetPrice": row_data[1],
                "CurrentPrice": row_data[2],
                "PERatio": row_data[3],
                "ROIC": row_data[4],
            })

        updated_rows = update_rows_from_yahoo(rows)
        for row_idx, row in enumerate(updated_rows, start=1):
            self.entries[(row_idx, 2)].delete(0, tk.END)
            self.entries[(row_idx, 2)].insert(0, row.get("CurrentPrice", ""))
            self.entries[(row_idx, 3)].delete(0, tk.END)
            self.entries[(row_idx, 3)].insert(0, row.get("PERatio", ""))
            self.entries[(row_idx, 4)].delete(0, tk.END)
            self.entries[(row_idx, 4)].insert(0, row.get("ROIC", ""))

            try:
                target_price = float(self.entries[(row_idx, 1)].get())
                current_price = row.get("CurrentPrice", "")
                if isinstance(current_price, str) and current_price.startswith("Error:"):
                    self.entries[(row_idx, 2)].config(bg='white')
                elif isinstance(current_price, (int, float)) and target_price > 0:
                    percentage_diff = abs((float(current_price) - target_price) / target_price) * 100
                    if percentage_diff <= 3:
                        self.entries[(row_idx, 2)].config(bg='lightgreen')
                    else:
                        self.entries[(row_idx, 2)].config(bg='white')
                else:
                    self.entries[(row_idx, 2)].config(bg='white')
            except (ValueError, ZeroDivisionError):
                self.entries[(row_idx, 2)].config(bg='white')

            print(f"{row.get('TickerName', '')}: {row.get('CurrentPrice', '')} (P/E: {row.get('PERatio', '')}) (ROIC: {row.get('ROIC', '')})")

        print("Update complete")


app = tk.Tk()
app.title("Price Target")
headers_list = ["Ticker Name", "Target Price", "Current Price", "P/E Ratio", "ROIC"]
table = DataEntryTable(app, rows=20, cols=5, headers=headers_list)
app.mainloop()
