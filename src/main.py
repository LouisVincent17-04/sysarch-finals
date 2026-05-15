import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
import threading
import os
import sys
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import seaborn as sns

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.api import get_summary_data

try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    plt.style.use('bmh')


class EmployeeManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Management System v1.0")
        self.root.geometry("1400x900")
        self.root.configure(bg='#ecf0f1')

        self.df          = None
        self.df_filtered = None
        self.filepath    = None

        self.setup_styles()
        self.create_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        self.colors = {
            'primary':   '#1a252f',
            'secondary': '#2c3e50',
            'accent':    '#2980b9',
            'success':   '#27ae60',
            'warning':   '#e67e22',
            'danger':    '#c0392b',
            'light':     '#ecf0f1',
            'white':     '#ffffff'
        }

        style.configure('Action.TButton',  font=('Segoe UI', 10, 'bold'), background=self.colors['accent'],  foreground='white')
        style.map('Action.TButton',  background=[('active', '#1f618d')])

        style.configure('Success.TButton', font=('Segoe UI', 10, 'bold'), background=self.colors['success'], foreground='white')
        style.map('Success.TButton', background=[('active', '#1e8449')])

        style.configure('Danger.TButton',  font=('Segoe UI', 10, 'bold'), background=self.colors['danger'],  foreground='white')
        style.map('Danger.TButton',  background=[('active', '#e74c3c')])

    def create_ui(self):
        header = tk.Frame(self.root, bg=self.colors['primary'], height=70)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)

        tk.Label(
            header, text="EMPLOYEE MANAGEMENT SYSTEM",
            font=('Segoe UI', 18, 'bold'),
            bg=self.colors['primary'], fg='white'
        ).pack(side='left', padx=20)

        main_container = tk.Frame(self.root, bg=self.colors['light'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        sidebar = tk.Frame(main_container, bg='white', width=320, relief='groove', bd=1)
        sidebar.pack(side='left', fill='y', padx=(0, 10))
        sidebar.pack_propagate(False)

        self.create_sidebar_content(sidebar)

        content_area = tk.Frame(main_container, bg=self.colors['light'])
        content_area.pack(side='left', fill='both', expand=True)

        self.create_dashboard_content(content_area)

        self.status_bar = tk.Label(
            self.root, text="Ready - Load a CSV file to begin",
            bd=1, relief=tk.SUNKEN, anchor=tk.W, font=('Segoe UI', 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_sidebar_content(self, parent):
        lf_file = tk.LabelFrame(parent, text="DATA SOURCE", font=('Segoe UI', 9, 'bold'), bg='white', fg=self.colors['secondary'])
        lf_file.pack(fill='x', padx=10, pady=10)

        self.btn_load = ttk.Button(lf_file, text="Load CSV Data", style='Action.TButton', command=self.start_file_load)
        self.btn_load.pack(fill='x', padx=5, pady=5)

        self.lbl_filename = tk.Label(lf_file, text="No file loaded", bg='white', fg='gray', font=('Segoe UI', 8))
        self.lbl_filename.pack(pady=(0, 5))

        lf_filter = tk.LabelFrame(parent, text="FILTERS", font=('Segoe UI', 9, 'bold'), bg='white', fg=self.colors['secondary'])
        lf_filter.pack(fill='both', expand=True, padx=10, pady=10)

        tk.Label(lf_filter, text="Joining Year Range:", bg='white', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=5, pady=(5, 0))
        year_frame = tk.Frame(lf_filter, bg='white')
        year_frame.pack(fill='x', padx=5)
        self.spin_year_start = tk.Spinbox(year_frame, width=8)
        self.spin_year_start.pack(side='left')
        tk.Label(year_frame, text="-", bg='white').pack(side='left', padx=5)
        self.spin_year_end = tk.Spinbox(year_frame, width=8)
        self.spin_year_end.pack(side='left')

        tk.Label(lf_filter, text="City:", bg='white', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=5, pady=(10, 0))
        self.combo_city = ttk.Combobox(lf_filter, state='readonly')
        self.combo_city.pack(fill='x', padx=5)

        tk.Label(lf_filter, text="Gender:", bg='white', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=5, pady=(10, 0))
        self.combo_gender = ttk.Combobox(lf_filter, state='readonly')
        self.combo_gender.pack(fill='x', padx=5)

        tk.Label(lf_filter, text="Education (Multi-select):", bg='white', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=5, pady=(10, 0))
        frame_list = tk.Frame(lf_filter)
        frame_list.pack(fill='both', expand=True, padx=5, pady=2)

        scrollbar = tk.Scrollbar(frame_list)
        scrollbar.pack(side='right', fill='y')
        self.list_education = tk.Listbox(frame_list, selectmode='multiple', yscrollcommand=scrollbar.set, height=5)
        self.list_education.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.list_education.yview)

        tk.Label(lf_filter, text="Payment Tier:", bg='white', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=5, pady=(10, 0))
        self.combo_tier = ttk.Combobox(lf_filter, state='readonly')
        self.combo_tier.pack(fill='x', padx=5)

        btn_frame = tk.Frame(lf_filter, bg='white')
        btn_frame.pack(fill='x', pady=10, padx=5)
        ttk.Button(btn_frame, text="Apply Filters", style='Success.TButton', command=self.apply_filters).pack(side='left', fill='x', expand=True, padx=(0, 2))
        ttk.Button(btn_frame, text="Reset",         style='Danger.TButton',  command=self.reset_filters).pack(side='left', fill='x', expand=True, padx=(2, 0))

        lf_api = tk.LabelFrame(parent, text="API TOOLS", font=('Segoe UI', 9, 'bold'), bg='white', fg=self.colors['secondary'])
        lf_api.pack(fill='x', padx=10, pady=(0, 5))
        ttk.Button(lf_api, text="Use Summary API", style='Action.TButton', command=self.show_summary_modal).pack(fill='x', padx=5, pady=6)

        ttk.Button(parent, text="Export Filtered Data", command=self.export_data).pack(fill='x', padx=10, pady=10, side='bottom')

    def create_dashboard_content(self, parent):
        self.metrics_frame = tk.Frame(parent, bg=self.colors['light'])
        self.metrics_frame.pack(fill='x', pady=(0, 10))

        self.metric_widgets = {}
        for key, title in [
            ('total',     'Total Employees'),
            ('attrition', 'Attrition Rate'),
            ('avg_age',   'Avg Age'),
            ('avg_exp',   'Avg Experience (yrs)'),
        ]:
            card = tk.Frame(self.metrics_frame, bg='white', padx=15, pady=10, relief='raised')
            card.pack(side='left', fill='x', expand=True, padx=5)
            tk.Label(card, text=title, font=('Segoe UI', 10), fg='gray', bg='white').pack()
            lbl_val = tk.Label(card, text="--", font=('Segoe UI', 16, 'bold'), fg=self.colors['primary'], bg='white')
            lbl_val.pack()
            self.metric_widgets[key] = lbl_val

        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)

        self.tabs = {}
        for key, name in [
            ('summary',   'Summary'),
            ('attrition', 'Attrition Analysis'),
            ('city',      'City Distribution'),
            ('education', 'Education Breakdown'),
            ('age',       'Age vs Experience'),
        ]:
            frame = tk.Frame(self.notebook, bg='white')
            self.notebook.add(frame, text=name)
            self.tabs[key] = frame

        self.txt_summary = scrolledtext.ScrolledText(self.tabs['summary'], font=('Consolas', 10))
        self.txt_summary.pack(fill='both', expand=True, padx=10, pady=10)

    def start_file_load(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        self.status_bar.config(text="Loading dataset... please wait")
        self.btn_load.config(state='disabled')
        threading.Thread(target=self.load_data_thread, args=(file_path,), daemon=True).start()

    def load_data_thread(self, file_path):
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            # Aggressively clean column names: strip whitespace, BOM, and
            # any other invisible unicode characters
            df.columns = [c.strip().lstrip(chr(0xFEFF)).strip() for c in df.columns]

            cols_required = ['Education', 'JoiningYear', 'City', 'PaymentTier',
                             'Age', 'Gender', 'EverBenched', 'ExperienceInCurrentDomain', 'LeaveOrNot']
            missing = [col for col in cols_required if col not in df.columns]
            if missing:
                found = list(df.columns)
                msg = "Missing columns: " + str(missing) + " | Found: " + str(found)
                raise ValueError(msg)

            df['JoiningYear']               = pd.to_numeric(df['JoiningYear'],               errors='coerce')
            df['Age']                       = pd.to_numeric(df['Age'],                       errors='coerce')
            df['PaymentTier']               = pd.to_numeric(df['PaymentTier'],               errors='coerce')
            df['ExperienceInCurrentDomain'] = pd.to_numeric(df['ExperienceInCurrentDomain'], errors='coerce')
            df['LeaveOrNot']                = pd.to_numeric(df['LeaveOrNot'],                errors='coerce')
            df.dropna(subset=['Age', 'LeaveOrNot'], inplace=True)
            df['JoiningYear'] = df['JoiningYear'].astype(int)
            df['LeaveOrNot']  = df['LeaveOrNot'].astype(int)

            self.root.after(0, lambda: self.on_load_success(df, file_path))

        except Exception as e:
            msg = str(e)
            self.root.after(0, lambda: self.on_load_error(msg))

    def on_load_success(self, df, filepath):
        self.df          = df
        self.df_filtered = df.copy()
        self.filepath    = filepath
        self.lbl_filename.config(text=os.path.basename(filepath))
        self.btn_load.config(state='normal')
        self.status_bar.config(text="Data loaded successfully")

        years = sorted(self.df['JoiningYear'].unique())
        self.spin_year_start.config(from_=min(years), to=max(years))
        self.spin_year_start.delete(0, 'end')
        self.spin_year_start.insert(0, min(years))

        self.spin_year_end.config(from_=min(years), to=max(years))
        self.spin_year_end.delete(0, 'end')
        self.spin_year_end.insert(0, max(years))

        cities = ['All'] + sorted(self.df['City'].unique().tolist())
        self.combo_city['values'] = cities
        self.combo_city.current(0)

        genders = ['All'] + sorted(self.df['Gender'].unique().tolist())
        self.combo_gender['values'] = genders
        self.combo_gender.current(0)

        tiers = ['All'] + sorted(str(t) for t in self.df['PaymentTier'].unique())
        self.combo_tier['values'] = tiers
        self.combo_tier.current(0)

        edu_levels = sorted(self.df['Education'].unique().tolist())
        self.list_education.delete(0, 'end')
        for e in edu_levels:
            self.list_education.insert('end', e)

        self.refresh_dashboard()
        messagebox.showinfo("Success", f"Loaded {len(df):,} employee records.")

    def on_load_error(self, error_msg):
        self.btn_load.config(state='normal')
        self.status_bar.config(text="Error loading file")
        messagebox.showerror("Load Error", error_msg)

    def apply_filters(self):
        if self.df is None:
            return

        try:
            start   = int(self.spin_year_start.get())
            end     = int(self.spin_year_end.get())
            temp_df = self.df[(self.df['JoiningYear'] >= start) & (self.df['JoiningYear'] <= end)]

            city = self.combo_city.get()
            if city != 'All':
                temp_df = temp_df[temp_df['City'] == city]

            gender = self.combo_gender.get()
            if gender != 'All':
                temp_df = temp_df[temp_df['Gender'] == gender]

            tier = self.combo_tier.get()
            if tier != 'All':
                temp_df = temp_df[temp_df['PaymentTier'] == int(tier)]

            indices = self.list_education.curselection()
            if indices:
                selected = [self.list_education.get(i) for i in indices]
                temp_df  = temp_df[temp_df['Education'].isin(selected)]

            self.df_filtered = temp_df
            self.refresh_dashboard()
            self.status_bar.config(text=f"Filter applied: {len(temp_df):,} records found")

        except Exception as e:
            messagebox.showerror("Filter Error", str(e))

    def reset_filters(self):
        if self.df is None:
            return
        self.df_filtered = self.df.copy()
        self.list_education.selection_clear(0, 'end')
        self.combo_city.current(0)
        self.combo_gender.current(0)
        self.combo_tier.current(0)
        years = sorted(self.df['JoiningYear'].unique())
        self.spin_year_start.delete(0, 'end')
        self.spin_year_start.insert(0, min(years))
        self.spin_year_end.delete(0, 'end')
        self.spin_year_end.insert(0, max(years))
        self.refresh_dashboard()

    def export_data(self):
        if self.df_filtered is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            self.df_filtered.to_csv(path, index=False)
            messagebox.showinfo("Export", "Data exported successfully!")

    def show_summary_modal(self):
        if self.df_filtered is None:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return

        data = get_summary_data(self.df_filtered)

        modal = tk.Toplevel(self.root)
        modal.title("Summary API Response")
        modal.geometry("500x580")
        modal.resizable(False, False)
        modal.grab_set()
        modal.configure(bg='white')

        hdr = tk.Frame(modal, bg=self.colors['primary'], height=55)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="Summary API",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['primary'], fg='white'
        ).pack(side='left', padx=15, pady=12)
        tk.Label(
            hdr, text="api.py  |  get_summary_data()",
            font=('Segoe UI', 8),
            bg=self.colors['primary'], fg='#95a5a6'
        ).pack(side='right', padx=15)

        if "error" in data:
            tk.Label(
                modal, text=data["error"],
                fg=self.colors['danger'], font=('Segoe UI', 11), bg='white'
            ).pack(pady=40)
        else:
            cards_frame = tk.Frame(modal, bg='#f0f3f4', padx=15, pady=15)
            cards_frame.pack(fill='x')

            cards = [
                ("Total Employees",   f"{data['total_employees']:,}",          self.colors['primary']),
                ("Attrition Count",   f"{data['attrition_count']:,}",          self.colors['danger']),
                ("Attrition Rate",    f"{data['attrition_rate_pct']}%",        self.colors['warning']),
                ("Avg Age",           str(data['avg_age']),                    self.colors['accent']),
                ("Avg Experience",    f"{data['avg_experience']} yrs",         self.colors['success']),
                ("Avg Payment Tier",  str(data['avg_payment_tier']),           self.colors['secondary']),
                ("Cities Covered",    str(data['cities_covered']),             self.colors['accent']),
                ("Year Range",        f"{data['year_range'][0]} - {data['year_range'][1]}", self.colors['primary']),
            ]

            for i, (label, value, color) in enumerate(cards):
                row, col = divmod(i, 2)
                card = tk.Frame(cards_frame, bg='white', padx=12, pady=10, relief='groove', bd=1)
                card.grid(row=row, column=col, padx=6, pady=6, sticky='nsew')
                tk.Label(card, text=label, font=('Segoe UI', 8),         fg='gray',  bg='white').pack(anchor='w')
                tk.Label(card, text=value,  font=('Segoe UI', 15, 'bold'), fg=color, bg='white').pack(anchor='w')

            cards_frame.columnconfigure(0, weight=1)
            cards_frame.columnconfigure(1, weight=1)

            tk.Label(
                modal, text="Raw JSON Response",
                font=('Segoe UI', 9, 'bold'),
                bg='white', fg=self.colors['secondary']
            ).pack(anchor='w', padx=18, pady=(12, 2))

            json_box = scrolledtext.ScrolledText(
                modal, height=8, font=('Consolas', 9),
                bg='#1a252f', fg='#2ecc71',
                insertbackground='white', relief='flat'
            )
            json_box.pack(fill='x', padx=15, pady=(0, 10))
            json_box.insert('1.0', json.dumps(data, indent=2))
            json_box.config(state='disabled')

        ttk.Button(modal, text="Close", command=modal.destroy).pack(pady=(0, 15))

    def refresh_dashboard(self):
        self.update_metrics()
        self.update_summary()
        self.plot_attrition()
        self.plot_city()
        self.plot_education()
        self.plot_age_experience()

    def update_metrics(self):
        total      = len(self.df_filtered)
        attrition  = self.df_filtered['LeaveOrNot'].mean() * 100 if total > 0 else 0
        avg_age    = self.df_filtered['Age'].mean() if total > 0 else 0
        avg_exp    = self.df_filtered['ExperienceInCurrentDomain'].mean() if total > 0 else 0

        self.metric_widgets['total'].config(text=f"{total:,}")
        self.metric_widgets['attrition'].config(
            text=f"{attrition:.1f}%",
            fg=self.colors['danger'] if attrition > 30 else self.colors['success']
        )
        self.metric_widgets['avg_age'].config(text=f"{avg_age:.1f}")
        self.metric_widgets['avg_exp'].config(text=f"{avg_exp:.1f}")

    def update_summary(self):
        self.txt_summary.delete('1.0', 'end')
        if self.df_filtered.empty:
            return

        total     = len(self.df_filtered)
        left      = self.df_filtered['LeaveOrNot'].sum()
        stayed    = total - left
        attr_rate = left / total * 100 if total > 0 else 0

        edu_dist  = self.df_filtered['Education'].value_counts().to_string()
        city_dist = self.df_filtered['City'].value_counts().to_string()
        gen_dist  = self.df_filtered['Gender'].value_counts().to_string()
        tier_dist = self.df_filtered['PaymentTier'].value_counts().sort_index().to_string()

        stats = self.df_filtered[['Age', 'ExperienceInCurrentDomain', 'PaymentTier']].describe().to_string()

        report = (
            f"EMPLOYEE DATA SUMMARY\n{'='*35}\n\n"
            f"Headcount:        {total:,}\n"
            f"Stayed:           {stayed:,}\n"
            f"Left (Attrition): {left:,}\n"
            f"Attrition Rate:   {attr_rate:.1f}%\n\n"
            f"Education Distribution:\n{'-'*35}\n{edu_dist}\n\n"
            f"City Distribution:\n{'-'*35}\n{city_dist}\n\n"
            f"Gender Distribution:\n{'-'*35}\n{gen_dist}\n\n"
            f"Payment Tier Distribution:\n{'-'*35}\n{tier_dist}\n\n"
            f"Numeric Statistics:\n{'-'*35}\n{stats}"
        )
        self.txt_summary.insert('1.0', report)

    def embed_plot(self, fig, tab_key):
        for widget in self.tabs[tab_key].winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.tabs[tab_key])
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, self.tabs[tab_key])
        toolbar.update()

        canvas.get_tk_widget().pack(fill='both', expand=True)

    def plot_attrition(self):
        if self.df_filtered.empty:
            return

        fig = Figure(figsize=(9, 5), dpi=100)

        ax1 = fig.add_subplot(121)
        by_city = self.df_filtered.groupby('City')['LeaveOrNot'].mean() * 100
        by_city.sort_values().plot(kind='barh', ax=ax1, color='#c0392b', width=0.6)
        ax1.set_title("Attrition Rate by City (%)")
        ax1.set_xlabel("Attrition %")

        ax2 = fig.add_subplot(122)
        by_edu = self.df_filtered.groupby('Education')['LeaveOrNot'].mean() * 100
        by_edu.sort_values().plot(kind='barh', ax=ax2, color='#e67e22', width=0.6)
        ax2.set_title("Attrition Rate by Education (%)")
        ax2.set_xlabel("Attrition %")

        fig.tight_layout()
        self.embed_plot(fig, 'attrition')

    def plot_city(self):
        if self.df_filtered.empty:
            return

        city_counts = self.df_filtered['City'].value_counts()

        fig = Figure(figsize=(9, 5), dpi=100)

        ax1 = fig.add_subplot(121)
        colors = ['#2980b9', '#27ae60', '#e67e22']
        ax1.pie(city_counts.values, labels=city_counts.index, autopct='%1.1f%%',
                colors=colors, startangle=90)
        ax1.set_title("Employee Distribution by City")

        ax2 = fig.add_subplot(122)
        pivot = self.df_filtered.groupby(['City', 'Gender']).size().unstack(fill_value=0)
        pivot.plot(kind='bar', ax=ax2, color=['#e74c3c', '#3498db'], width=0.6)
        ax2.set_title("City vs Gender Breakdown")
        ax2.set_ylabel("Employee Count")
        ax2.tick_params(axis='x', rotation=0)

        fig.tight_layout()
        self.embed_plot(fig, 'city')

    def plot_education(self):
        if self.df_filtered.empty:
            return

        fig = Figure(figsize=(9, 5), dpi=100)

        ax1 = fig.add_subplot(121)
        edu_counts = self.df_filtered['Education'].value_counts().sort_values()
        edu_counts.plot(kind='barh', ax=ax1, color='#2980b9', width=0.6)
        ax1.set_title("Headcount by Education Level")
        ax1.set_xlabel("Count")

        ax2 = fig.add_subplot(122)
        pivot = self.df_filtered.groupby(['Education', 'PaymentTier']).size().unstack(fill_value=0)
        pivot.plot(kind='bar', ax=ax2, colormap='viridis', width=0.7)
        ax2.set_title("Education vs Payment Tier")
        ax2.set_ylabel("Count")
        ax2.tick_params(axis='x', rotation=15)
        ax2.legend(title="Tier")

        fig.tight_layout()
        self.embed_plot(fig, 'education')

    def plot_age_experience(self):
        if self.df_filtered.empty:
            return

        fig = Figure(figsize=(9, 5), dpi=100)

        ax1 = fig.add_subplot(121)
        colors_map = self.df_filtered['LeaveOrNot'].map({0: '#27ae60', 1: '#c0392b'})
        ax1.scatter(
            self.df_filtered['ExperienceInCurrentDomain'],
            self.df_filtered['Age'],
            c=colors_map, alpha=0.5, edgecolors='none', s=40
        )
        ax1.set_title("Age vs Experience (Green=Stayed, Red=Left)")
        ax1.set_xlabel("Experience in Domain (yrs)")
        ax1.set_ylabel("Age")
        ax1.grid(True, linestyle='--', alpha=0.5)

        ax2 = fig.add_subplot(122)
        self.df_filtered['Age'].hist(ax=ax2, bins=15, color='#2980b9', edgecolor='white')
        ax2.set_title("Age Distribution")
        ax2.set_xlabel("Age")
        ax2.set_ylabel("Count")

        fig.tight_layout()
        self.embed_plot(fig, 'age')


if __name__ == "__main__":
    root = tk.Tk()
    app  = EmployeeManagementApp(root)
    root.mainloop()