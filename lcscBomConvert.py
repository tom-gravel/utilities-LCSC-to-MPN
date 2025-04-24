import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
import re
from lcscToMPN import get_manufacturer_info  # Make sure this file is in the same folder

class BOMConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BOM Converter with LCSC to MPN and Manufacturer")
        self.file_path = None
        self.df = None
        self.header_row = 0

        # Top frame for file input
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10, anchor='w')

        tk.Label(top_frame, text="Input BOM:").pack(side='left')
        self.file_entry = tk.Entry(top_frame, width=80)
        self.file_entry.pack(side='left', padx=5)
        tk.Button(top_frame, text="Browse", command=self.load_file).pack(side='left')

        # Middle frame for header row and preview
        middle_frame = tk.Frame(root)
        middle_frame.pack(pady=10, anchor='w')

        tk.Label(middle_frame, text="Header Row:").grid(row=0, column=0, sticky='w')
        self.row_selector = tk.Spinbox(middle_frame, from_=0, to=100, width=5, command=self.update_preview)
        self.row_selector.grid(row=0, column=1, sticky='w', padx=5)

        self.preview = tk.Text(middle_frame, height=10, width=120)
        self.preview.grid(row=1, column=0, columnspan=2, sticky='w')
        scrollbar = tk.Scrollbar(middle_frame, command=self.preview.yview)
        scrollbar.grid(row=1, column=2, sticky='nsw')
        self.preview.config(yscrollcommand=scrollbar.set)

        # Column selector
        tk.Label(root, text="LCSC part number column").pack(anchor='w', padx=5)
        self.column_selector = ttk.Combobox(root, state="readonly", width=50)
        self.column_selector.pack(anchor='w', padx=5, pady=5)

        # Controls
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10, anchor='w')

        self.format_var = tk.StringVar(value="excel")
        format_option = ttk.Combobox(control_frame, textvariable=self.format_var, values=["excel", "csv"], state="readonly", width=10)
        format_option.pack(side='left', padx=5)

        self.process_btn = tk.Button(control_frame, text="Process File", command=self.process_file)
        self.process_btn.pack(side='left', padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10, anchor='w', padx=5)

    def load_file(self):
        filetypes = [("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path:
            return

        self.file_path = path
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, path)

        if path.endswith('.csv'):
            self.df = pd.read_csv(path)
        else:
            self.df = pd.read_excel(path)

        self.header_row = self.detect_header_row()
        self.row_selector.delete(0, tk.END)
        self.row_selector.insert(0, self.header_row)
        self.update_preview()
        self.update_column_selector()

    def detect_header_row(self):
        for i, row in self.df.iterrows():
            if row.notna().sum() >= len(row) // 2:
                return i
        return 0

    def update_preview(self):
        try:
            row = int(self.row_selector.get())
        except ValueError:
            return

        lines = []
        for i in range(max(0, row - 2), min(len(self.df), row + 3)):
            prefix = "-> " if i == row else "   "
            lines.append(f"{prefix}Row {i}: {self.df.iloc[i].tolist()}")

        self.preview.delete("1.0", tk.END)
        self.preview.insert(tk.END, "\n".join(lines))

    def update_column_selector(self):
        self.df.columns = self.df.iloc[self.header_row]
        self.df = self.df.drop(index=range(0, self.header_row+1))
        self.df.reset_index(drop=True, inplace=True)
        self.column_selector['values'] = list(self.df.columns)

    def process_file(self):
        col = self.column_selector.get()
        if not col:
            messagebox.showerror("Error", "Please select a column containing LCSC part numbers.")
            return

        self.progress['maximum'] = len(self.df)
        results = []

        pattern = re.compile(r'^C\d+$')

        for i, part in enumerate(self.df[col]):
            part_str = str(part).strip()
            if pattern.match(part_str):
                info = get_manufacturer_info(part_str)
                if info:
                    results.append(info)
                else:
                    results.append({'MPN': '', 'Manufacturer': ''})
            else:
                results.append({'MPN': '', 'Manufacturer': ''})
            self.progress['value'] = i + 1
            self.root.update_idletasks()

        mpns = [res['MPN'] for res in results]
        mfgs = [res['Manufacturer'] for res in results]

        insert_index = self.df.columns.get_loc(col) + 1
        self.df.insert(insert_index, "Converted MPN", mpns)
        self.df.insert(insert_index + 1, "Converted MFG", mfgs)

        default_name = os.path.splitext(os.path.basename(self.file_path))[0] + "-converted"
        extension = ".xlsx" if self.format_var.get() == "excel" else ".csv"
        save_path = filedialog.asksaveasfilename(defaultextension=extension,
                                                 initialfile=default_name + extension,
                                                 initialdir=os.path.dirname(self.file_path),
                                                 filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])

        if save_path:
            if save_path.endswith('.csv'):
                self.df.to_csv(save_path, index=False)
            else:
                self.df.to_excel(save_path, index=False)
            messagebox.showinfo("Done", f"File saved: {save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BOMConverterGUI(root)
    root.mainloop()
