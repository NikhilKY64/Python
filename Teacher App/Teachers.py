import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

class TeacherTimetableApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Teacher Timetable Manager")
        # Start maximized so the window decorations (close button) remain visible
        self.default_size = (1200, 800)  # width, height when not fullscreen
        self.is_fullscreen = False
        self.is_maximized = True
        try:
            # On Windows, this maximizes the window while keeping decorations
            self.state("zoomed")
        except tk.TclError:
            # Fallback - set geometry to screen size
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        # Bind F11 to toggle fullscreen; Escape to exit fullscreen (and center)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        
        # Database setup
        self.db_path = "school.db"
        self.create_database()
        
        # Configure ttk style
        self.setup_style()
        
        # Days and periods configuration
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.periods = list(range(1, 9))  # Periods 1..8

        # Subject color mapping for timetable cells
        self.subject_colors = {}
        self.color_palette = [
            "#4CC562", "#AED6F1", "#F5B7B1", "#D2B4DE", "#ABEBC6", "#FADBD8",
            "#D6EAF8", "#F9EBEA", "#E8DAEF", "#FDEBD0"
        ]
        self.next_color_idx = 0

        # Current selected teacher
        self.current_teacher_id = None
        
        # Color scheme for buttons
        self.color_add = "#3EBD3A"      # Green for Add
        self.color_edit = "#3B82F6"     # Blue for Edit
        self.color_delete = "#E93D3D"   # Red for Delete
        self.color_exit = "#E91212"     # Red for Exit
        self.text_color = "#FFFFFF"     # White text
        
        # Build main layout
        self.create_main_layout()
        
        # Load initial data
        self.load_teachers()
    
    def setup_style(self):
        """Configure ttk style for modern appearance"""
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Normal.TLabel", font=("Segoe UI", 10))
        style.configure("Heading.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 9))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=25)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def get_subject_color(self, subject):
        """Return a consistent color for a subject. Assign a new color if first time seen."""
        if not subject:
            return getattr(self, 'default_btn_bg', self.cget('bg'))
        key = subject.strip().lower()
        if key in self.subject_colors:
            return self.subject_colors[key]
        color = self.color_palette[self.next_color_idx % len(self.color_palette)]
        self.subject_colors[key] = color
        self.next_color_idx += 1
        return color
    
    def create_database(self):
        """Create SQLite database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Teachers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                degree TEXT,
                main_subject TEXT
            )
        """)
        
        # Timetable table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                period_number INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                FOREIGN KEY(teacher_id) REFERENCES teachers(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_main_layout(self):
        """Create the two-panel main layout"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # LEFT PANEL - Teachers
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        ttk.Label(left_frame, text="Teachers", style="Title.TLabel").pack(anchor="w", pady=(0, 10))
        
        # Teachers Treeview
        self.teachers_tree = ttk.Treeview(
            left_frame,
            columns=("Name", "Main Subject"),
            height=15,
            show="headings"
        )
        self.teachers_tree.column("Name", width=150)
        self.teachers_tree.column("Main Subject", width=130)
        self.teachers_tree.heading("Name", text="Name")
        self.teachers_tree.heading("Main Subject", text="Main Subject")
        self.teachers_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        # Alternate row colors for readability
        self.teachers_tree.tag_configure('evenrow', background="#b7d6f0")
        self.teachers_tree.tag_configure('oddrow', background="#8ca6e7")
        
        self.teachers_tree.bind("<<TreeviewSelect>>", self.on_teacher_selected)
        
        # Teacher buttons
        teacher_btn_frame = ttk.Frame(left_frame)
        teacher_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(teacher_btn_frame, text="Add Teacher", command=self.add_teacher_dialog,
                  bg=self.color_add, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#059669", cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(teacher_btn_frame, text="Edit Teacher", command=self.edit_teacher_dialog,
                  bg=self.color_edit, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#1D4ED8", cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(teacher_btn_frame, text="Delete Teacher", command=self.delete_teacher,
                  bg=self.color_delete, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#DC2626", cursor="hand2").pack(side=tk.LEFT, padx=2)
        
        # RIGHT PANEL - Timetable
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Teacher details
        details_frame = ttk.LabelFrame(right_frame, text="Selected Teacher", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.teacher_name_label = ttk.Label(details_frame, text="No teacher selected", style="Heading.TLabel")
        self.teacher_name_label.pack(anchor="w")
        
        self.teacher_degree_label = ttk.Label(details_frame, text="", style="Normal.TLabel")
        self.teacher_degree_label.pack(anchor="w")
        
        self.teacher_subject_label = ttk.Label(details_frame, text="", style="Normal.TLabel")
        self.teacher_subject_label.pack(anchor="w")
        
        # Timetable section (grid layout)
        ttk.Label(right_frame, text="Timetable", style="Title.TLabel").pack(anchor="w", pady=(10, 5))

        # Use a canvas for horizontal scrolling
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.timetable_canvas = tk.Canvas(canvas_frame, height=360)
        h_scroll = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.timetable_canvas.xview)
        self.timetable_canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.timetable_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame inside canvas that will hold the grid
        self.timetable_grid_frame = ttk.Frame(self.timetable_canvas)
        self.timetable_canvas.create_window((0, 0), window=self.timetable_grid_frame, anchor='nw')

        # Build the grid: header row + days rows
        self.grid_buttons = {}  # (day, period) -> button

        # Header row: empty top-left, then Period 1..8
        header_style = "Heading.TLabel"
        ttk.Label(self.timetable_grid_frame, text="DAY", style=header_style, borderwidth=1, relief="solid", anchor="center", padding=6).grid(row=0, column=0, sticky="nsew")
        for c, period in enumerate(self.periods, start=1):
            ttk.Label(self.timetable_grid_frame, text=f"Period {period}", style=header_style, borderwidth=1, relief="solid", anchor="center", padding=6).grid(row=0, column=c, sticky="nsew")

        for r, day in enumerate(self.days, start=1):
            # Day label
            ttk.Label(self.timetable_grid_frame, text=day.upper(), style="Normal.TLabel", borderwidth=1, relief="solid", padding=6).grid(row=r, column=0, sticky="nsew")
            for c, period in enumerate(self.periods, start=1):
                btn = tk.Button(self.timetable_grid_frame, text="", width=18, height=3, wraplength=120,
                                command=lambda d=day, p=period: self.on_cell_click(d, p))
                btn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                # Right-click context menu to edit/delete
                btn.bind("<Button-3>", lambda e, d=day, p=period: self.on_cell_right_click(e, d, p))
                self.grid_buttons[(day, period)] = btn
                # capture default background color for resetting
                if not hasattr(self, 'default_btn_bg'):
                    self.default_btn_bg = btn.cget('bg')

        # Make columns expand evenly for nicer layout
        for col in range(len(self.periods) + 1):
            self.timetable_grid_frame.grid_columnconfigure(col, weight=1)

        self.timetable_grid_frame.update_idletasks()
        self.timetable_canvas.configure(scrollregion=self.timetable_canvas.bbox('all'))

        # Add a small note on using the grid
        ttk.Label(right_frame, text="Tip: Click a cell to add/edit the period. Right-click for more options.", style="Normal.TLabel").pack(anchor="w")
        
        # Timetable buttons
        timetable_btn_frame = ttk.Frame(right_frame)
        timetable_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(timetable_btn_frame, text="Add Period", command=self.add_period_dialog,
                  bg=self.color_add, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#059669", cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(timetable_btn_frame, text="Edit Period", command=self.edit_period_dialog,
                  bg=self.color_edit, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#1D4ED8", cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(timetable_btn_frame, text="Delete Period", command=self.delete_period,
                  bg=self.color_delete, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#DC2626", cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(timetable_btn_frame, text="Exit", command=self.quit,
                  bg=self.color_exit, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#634B4B", cursor="hand2").pack(side=tk.RIGHT, padx=2)
    
    def load_teachers(self):
        """Load all teachers into the treeview"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Order by name case-insensitive (A -> Z)
        cursor.execute("SELECT id, name, main_subject FROM teachers ORDER BY LOWER(name) ASC")
        teachers = cursor.fetchall()
        conn.close()
        
        # Clear treeview
        for item in self.teachers_tree.get_children():
            self.teachers_tree.delete(item)
        
        # Populate treeview with alternating row colors
        for idx, (teacher_id, name, main_subject) in enumerate(teachers):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.teachers_tree.insert("", "end", iid=teacher_id, values=(name, main_subject or ""), tags=(tag,))
    
    def on_teacher_selected(self, event):
        """Handle teacher selection"""
        selection = self.teachers_tree.selection()
        if selection:
            self.current_teacher_id = selection[0]
            self.load_teacher_details()
            self.load_timetable_for_teacher()
    
    def load_teacher_details(self):
        """Load and display selected teacher's details"""
        if not self.current_teacher_id:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, degree, main_subject FROM teachers WHERE id = ?", (self.current_teacher_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            name, degree, main_subject = result
            self.teacher_name_label.config(text=name)
            self.teacher_degree_label.config(text=f"Degree: {degree or 'N/A'}")
            self.teacher_subject_label.config(text=f"Main Subject: {main_subject or 'N/A'}")
    
    def load_timetable_for_teacher(self):
        """Load timetable entries for selected teacher"""
        if not self.current_teacher_id:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, day_of_week, period_number, class_name, subject FROM timetable 
               WHERE teacher_id = ? ORDER BY 
               CASE day_of_week 
                   WHEN 'Monday' THEN 1
                   WHEN 'Tuesday' THEN 2
                   WHEN 'Wednesday' THEN 3
                   WHEN 'Thursday' THEN 4
                   WHEN 'Friday' THEN 5
                   WHEN 'Saturday' THEN 6
               END, period_number""",
            (self.current_teacher_id,)
        )
        entries = cursor.fetchall()
        conn.close()
        
        # Clear grid buttons
        for (day, period), btn in self.grid_buttons.items():
            btn.config(text="", bg=getattr(self, 'default_btn_bg', btn.cget('bg')), fg="#000000")
            # Remove any attached entry id
            if hasattr(btn, 'entry_id'):
                delattr(btn, 'entry_id')

        # Populate grid
        for entry_id, day, period, class_name, subject in entries:
            key = (day, period)
            if key in self.grid_buttons:
                btn = self.grid_buttons[key]
                color = self.get_subject_color(subject)
                btn.config(text=f"{class_name}\n{subject}", bg=color, fg="#000000")
                # Store entry_id on button for easy lookup
                btn.entry_id = entry_id
            else:
                # Unexpected day/period; skip
                pass
        # Update canvas scrollregion after making changes
        self.timetable_grid_frame.update_idletasks()
        self.timetable_canvas.configure(scrollregion=self.timetable_canvas.bbox('all'))
    
    def add_teacher_dialog(self):
        """Open add teacher dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Teacher")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(main_frame, width=25)
        name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(main_frame, text="Degree:").grid(row=1, column=0, sticky="w", pady=5)
        degree_entry = ttk.Entry(main_frame, width=25)
        degree_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(main_frame, text="Main Subject:").grid(row=2, column=0, sticky="w", pady=5)
        subject_entry = ttk.Entry(main_frame, width=25)
        subject_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=15)
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Validation Error", "Name is required!")
                return
            
            degree = degree_entry.get().strip() or None
            subject = subject_entry.get().strip() or None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO teachers (name, degree, main_subject) VALUES (?, ?, ?)",
                         (name, degree, subject))
            conn.commit()
            conn.close()
            
            self.load_teachers()
            dialog.destroy()
            messagebox.showinfo("Success", "Teacher added successfully!")
        
        tk.Button(button_frame, text="Save", command=save,
                  bg=self.color_add, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#059669").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                  bg=self.color_exit, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#1174FD").pack(side=tk.LEFT, padx=5)
    
    def edit_teacher_dialog(self):
        """Open edit teacher dialog"""
        if not self.current_teacher_id:
            messagebox.showerror("Error", "Please select a teacher to edit!")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, degree, main_subject FROM teachers WHERE id = ?", (self.current_teacher_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return
        
        name, degree, subject = result
        
        dialog = tk.Toplevel(self)
        dialog.title("Edit Teacher")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(main_frame, width=25)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(main_frame, text="Degree:").grid(row=1, column=0, sticky="w", pady=5)
        degree_entry = ttk.Entry(main_frame, width=25)
        degree_entry.insert(0, degree or "")
        degree_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(main_frame, text="Main Subject:").grid(row=2, column=0, sticky="w", pady=5)
        subject_entry = ttk.Entry(main_frame, width=25)
        subject_entry.insert(0, subject or "")
        subject_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=15)
        
        def update():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Validation Error", "Name is required!")
                return
            
            new_degree = degree_entry.get().strip() or None
            new_subject = subject_entry.get().strip() or None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE teachers SET name = ?, degree = ?, main_subject = ? WHERE id = ?",
                         (new_name, new_degree, new_subject, self.current_teacher_id))
            conn.commit()
            conn.close()
            
            self.load_teachers()
            self.load_teacher_details()
            dialog.destroy()
            messagebox.showinfo("Success", "Teacher updated successfully!")
        
        tk.Button(button_frame, text="Update", command=update,
                  bg=self.color_edit, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#1D4ED8").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                  bg=self.color_exit, fg=self.text_color, font=("Segoe UI", 9, "bold"),
                  activebackground="#4B5563").pack(side=tk.LEFT, padx=5)
    
    def delete_teacher(self):
        """Delete selected teacher"""
        if not self.current_teacher_id:
            messagebox.showerror("Error", "Please select a teacher to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this teacher and all their timetable entries?"):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM timetable WHERE teacher_id = ?", (self.current_teacher_id,))
            cursor.execute("DELETE FROM teachers WHERE id = ?", (self.current_teacher_id,))
            conn.commit()
            conn.close()
            
            self.current_teacher_id = None
            self.load_teachers()
            
            # Clear details and timetable
            self.teacher_name_label.config(text="No teacher selected")
            self.teacher_degree_label.config(text="")
            self.teacher_subject_label.config(text="")
            # Clear grid cells
            for (day, period), btn in self.grid_buttons.items():
                btn.config(text="", bg=getattr(self, 'default_btn_bg', btn.cget('bg')), fg="#000000")
                if hasattr(btn, 'entry_id'):
                    delattr(btn, 'entry_id')
            
            messagebox.showinfo("Success", "Teacher deleted successfully!")
    
    def add_period_dialog(self, day=None, period=None):
        """Open add period dialog. If day and period provided, prefill them."""
        if not self.current_teacher_id:
            messagebox.showerror("Error", "Please select a teacher first!")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("Add Period")
        dialog.geometry("350x250")
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Day of Week:").grid(row=0, column=0, sticky="w", pady=8)
        day_combo = ttk.Combobox(main_frame, width=22, 
                                values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                                state="readonly")
        day_combo.grid(row=0, column=1, sticky="ew", pady=8, padx=5)
        
        ttk.Label(main_frame, text="Period Number:").grid(row=1, column=0, sticky="w", pady=8)
        period_entry = ttk.Entry(main_frame, width=25)
        period_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=5)
        # Prefill if provided
        if day:
            day_combo.set(day)
        if period:
            period_entry.insert(0, str(period))
        
        ttk.Label(main_frame, text="Class Name:").grid(row=2, column=0, sticky="w", pady=8)
        class_entry = ttk.Entry(main_frame, width=25)
        class_entry.grid(row=2, column=1, sticky="ew", pady=8, padx=5)
        
        ttk.Label(main_frame, text="Subject:").grid(row=3, column=0, sticky="w", pady=8)
        subject_entry = ttk.Entry(main_frame, width=25)
        subject_entry.grid(row=3, column=1, sticky="ew", pady=8, padx=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=15)
        
        def save():
            day = day_combo.get().strip()
            period_str = period_entry.get().strip()
            class_name = class_entry.get().strip()
            subject = subject_entry.get().strip()
            
            if not day or not period_str or not class_name or not subject:
                messagebox.showerror("Validation Error", "All fields are required!")
                return
            
            try:
                period = int(period_str)
            except ValueError:
                messagebox.showerror("Validation Error", "Period number must be an integer!")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Check if an entry already exists for this teacher/day/period
            cursor.execute("SELECT id FROM timetable WHERE teacher_id = ? AND day_of_week = ? AND period_number = ?",
                         (self.current_teacher_id, day, period))
            exists = cursor.fetchone()
            if exists:
                messagebox.showerror("Validation Error", "A period already exists for this day and period! Use Edit instead.")
                conn.close()
                return
            cursor.execute("""INSERT INTO timetable (teacher_id, day_of_week, period_number, class_name, subject)
                           VALUES (?, ?, ?, ?, ?)""",
                         (self.current_teacher_id, day, period, class_name, subject))
            conn.commit()
            conn.close()
            
            self.load_timetable_for_teacher()
            dialog.destroy()
            messagebox.showinfo("Success", "Period added successfully!")
        
        ttk.Button(button_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def edit_period_dialog(self, day=None, period=None, period_id=None):
        """Open edit period dialog. If day/period provided, use them to resolve period_id."""
        if not self.current_teacher_id:
            messagebox.showerror("Error", "Please select a teacher first!")
            return
        
        # Resolve period_id if day and period given
        if period_id is None:
            if day is not None and period is not None:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM timetable WHERE teacher_id = ? AND day_of_week = ? AND period_number = ?",
                             (self.current_teacher_id, day, period))
                row = cursor.fetchone()
                conn.close()
                if row:
                    period_id = row[0]
                else:
                    messagebox.showerror("Error", "No period configured for this day and period.")
                    return
            else:
                messagebox.showerror("Error", "Please click a timetable cell to edit, or pass a day/period.")
                return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""SELECT day_of_week, period_number, class_name, subject FROM timetable WHERE id = ?""",
                      (period_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return
        
        day, period, class_name, subject = result
        
        dialog = tk.Toplevel(self)
        dialog.title("Edit Period")
        dialog.geometry("350x250")
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Day of Week:").grid(row=0, column=0, sticky="w", pady=8)
        day_combo = ttk.Combobox(main_frame, width=22,
                                values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                                state="readonly")
        day_combo.set(day)
        day_combo.grid(row=0, column=1, sticky="ew", pady=8, padx=5)
        
        ttk.Label(main_frame, text="Period Number:").grid(row=1, column=0, sticky="w", pady=8)
        period_entry = ttk.Entry(main_frame, width=25)
        period_entry.insert(0, str(period))
        period_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=5)
        
        ttk.Label(main_frame, text="Class Name:").grid(row=2, column=0, sticky="w", pady=8)
        class_entry = ttk.Entry(main_frame, width=25)
        class_entry.insert(0, class_name)
        class_entry.grid(row=2, column=1, sticky="ew", pady=8, padx=5)
        
        ttk.Label(main_frame, text="Subject:").grid(row=3, column=0, sticky="w", pady=8)
        subject_entry = ttk.Entry(main_frame, width=25)
        subject_entry.insert(0, subject)
        subject_entry.grid(row=3, column=1, sticky="ew", pady=8, padx=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=15)
        
        def update():
            new_day = day_combo.get().strip()
            new_period_str = period_entry.get().strip()
            new_class = class_entry.get().strip()
            new_subject = subject_entry.get().strip()
            
            if not new_day or not new_period_str or not new_class or not new_subject:
                messagebox.showerror("Validation Error", "All fields are required!")
                return
            
            try:
                new_period = int(new_period_str)
            except ValueError:
                messagebox.showerror("Validation Error", "Period number must be an integer!")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""UPDATE timetable SET day_of_week = ?, period_number = ?, class_name = ?, subject = ?
                           WHERE id = ?""",
                         (new_day, new_period, new_class, new_subject, period_id))
            conn.commit()
            conn.close()
            
            self.load_timetable_for_teacher()
            dialog.destroy()
            messagebox.showinfo("Success", "Period updated successfully!")
        
        tk.Button(button_frame, text="Update", command=update).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_period(self):
        """Delete selected period"""
    def delete_period(self, day=None, period=None, period_id=None):
        """Delete a period by id or by day/period."""
        if not self.current_teacher_id:
            messagebox.showerror("Error", "Please select a teacher first!")
            return

        # Resolve period_id if needed
        if period_id is None:
            if day is None or period is None:
                messagebox.showerror("Error", "Please click a timetable cell to delete, or pass a day/period.")
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM timetable WHERE teacher_id = ? AND day_of_week = ? AND period_number = ?",
                          (self.current_teacher_id, day, period))
            row = cursor.fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Error", "No period exists for that day and period.")
                return
            period_id = row[0]

        if messagebox.askyesno("Confirm", "Delete this period?"):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM timetable WHERE id = ?", (period_id,))
            conn.commit()
            conn.close()
            self.load_timetable_for_teacher()
            messagebox.showinfo("Success", "Period deleted successfully!")

    def on_cell_click(self, day, period):
        """Called when a timetable cell is left-clicked: add or edit depending on if entry exists."""
        if not self.current_teacher_id:
            messagebox.showerror("Error", "Please select a teacher first!")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM timetable WHERE teacher_id = ? AND day_of_week = ? AND period_number = ?",
                      (self.current_teacher_id, day, period))
        row = cursor.fetchone()
        conn.close()

        if row:
            self.edit_period_dialog(day, period, period_id=row[0])
        else:
            self.add_period_dialog(day, period)

    def on_cell_right_click(self, event, day, period):
        """Right-click context menu for a timetable cell to Edit or Delete."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Add / Edit", command=lambda d=day, p=period: self.on_cell_click(d, p))
        menu.add_command(label="Delete", command=lambda d=day, p=period: self.delete_period(day=d, period=p))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen on/off (F11). When exiting fullscreen, center with default size."""
        if not getattr(self, "is_fullscreen", False):
            # Enter fullscreen, record previous window state
            self.prev_state = self.state()
            self.attributes("-fullscreen", True)
            self.is_fullscreen = True
        else:
            # Exit fullscreen, restore previous state (maximized or centered)
            self.attributes("-fullscreen", False)
            self.is_fullscreen = False
            if getattr(self, "prev_state", "") == "zoomed":
                try:
                    self.state("zoomed")
                except tk.TclError:
                    self.center_window(*getattr(self, "default_size", (1200, 800)))
            else:
                self.center_window(*getattr(self, "default_size", (1200, 800)))

    def exit_fullscreen(self, event=None):
        """Force exit fullscreen and center window (Escape)."""
        if getattr(self, "is_fullscreen", False):
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
            if getattr(self, "prev_state", "") == "zoomed":
                try:
                    self.state("zoomed")
                    return
                except tk.TclError:
                    pass
            self.center_window(*getattr(self, "default_size", (1200, 800)))

    def center_window(self, width, height):
        """Center the window for the given width and height."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
    app = TeacherTimetableApp()
    app.mainloop()