import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, colorchooser
from datetime import date, datetime, timedelta

from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT
from modules.storage import (
    initialize_storage,
    load_settings,
    save_settings,
    load_categories,
    load_tasks,
)
from modules.task_manager import (
    create_task,
    update_task,
    delete_task,
    filter_tasks,
    archive_old_tasks,
    restore_task,
    get_archived_tasks,
)
from modules.category_manager import (
    add_category,
    update_category,
    delete_category,
    get_categories,
    get_category_color,
)
from modules.calander_manager import (
    get_month_days,
    get_tasks_for_date,
    get_month_name,
    get_week_dates,
)
from modules.notifications import send_notification


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class TaskDialog(ctk.CTkToplevel):
    """Dialogruta för att skapa eller redigera en uppgift."""

    def __init__(self, master, task=None, selected_date=None, on_save=None):
        super().__init__(master)
        self.task = task
        self.on_save = on_save
        self.title("Redigera uppgift" if task else "Ny uppgift")
        self.geometry("540x700")
        self.minsize(500, 650)
        self.transient(master)
        self.grab_set()

        categories = get_categories()
        category_names = [item["name"] for item in categories]
        if not category_names:
            category_names = ["Personligt"]

        self.grid_columnconfigure(1, weight=1)

        def field_label(text, row):
            ctk.CTkLabel(
                self, text=text, font=ctk.CTkFont(size=13, weight="bold")
            ).grid(row=row, column=0, padx=(22, 12), pady=9, sticky="w")

        field_label("Namn", 0)
        self.name_entry = ctk.CTkEntry(self, placeholder_text="Vad behöver du göra?")
        self.name_entry.grid(row=0, column=1, padx=(0, 22), pady=9, sticky="ew")

        field_label("Kategori", 1)
        current_category = task.get("category", category_names[0]) if task else category_names[0]
        if current_category not in category_names:
            category_names.append(current_category)
        self.category_menu = ctk.CTkOptionMenu(
            self, values=category_names
        )
        self.category_menu.set(current_category)
        self.category_menu.grid(row=1, column=1, padx=(0, 22), pady=9, sticky="ew")

        field_label("Datum (ÅÅÅÅ-MM-DD)", 2)
        self.date_entry = ctk.CTkEntry(self, placeholder_text="2026-11-12")
        self.date_entry.grid(row=2, column=1, padx=(0, 22), pady=9, sticky="ew")

        field_label("Tid (TT:MM)", 3)
        self.time_entry = ctk.CTkEntry(self, placeholder_text="14:30")
        self.time_entry.grid(row=3, column=1, padx=(0, 22), pady=9, sticky="ew")

        field_label("Prioritet", 4)
        self.priority_menu = ctk.CTkOptionMenu(
            self, values=["Låg", "Normal", "Hög"]
        )
        self.priority_menu.grid(row=4, column=1, padx=(0, 22), pady=9, sticky="ew")

        field_label("Påminnelse", 5)
        self.reminder_menu = ctk.CTkOptionMenu(
            self, values=["Ingen", "5 minuter", "10 minuter", "15 minuter",
                          "30 minuter", "60 minuter", "1 dag"]
        )
        self.reminder_menu.grid(row=5, column=1, padx=(0, 22), pady=9, sticky="ew")

        ctk.CTkLabel(
            self, text="Beskrivning", font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=6, column=0, padx=(22, 12), pady=9, sticky="nw")
        self.description_box = ctk.CTkTextbox(self, height=90)
        self.description_box.grid(row=6, column=1, padx=(0, 22), pady=9, sticky="ew")

        ctk.CTkLabel(
            self, text="Anteckningar", font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=7, column=0, padx=(22, 12), pady=9, sticky="nw")
        self.notes_box = ctk.CTkTextbox(self, height=100)
        self.notes_box.grid(row=7, column=1, padx=(0, 22), pady=9, sticky="ew")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=8, column=0, columnspan=2, padx=22, pady=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            button_frame, text="Avbryt", fg_color="gray",
            command=self.destroy
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(
            button_frame, text="Spara uppgift",
            command=self.save
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        if task:
            self.name_entry.insert(0, task.get("name", ""))
            self.date_entry.insert(0, task.get("date", ""))
            self.time_entry.insert(0, task.get("time", ""))
            self.priority_menu.set(task.get("priority", "Normal"))
            self.description_box.insert("1.0", task.get("description", ""))
            self.notes_box.insert("1.0", task.get("notes", ""))
            self.reminder_menu.set(self.reminder_to_label(task.get("reminder")))
        else:
            self.date_entry.insert(0, (selected_date or date.today()).isoformat())
            self.time_entry.insert(0, "09:00")
            self.priority_menu.set("Normal")
            self.reminder_menu.set("30 minuter")

        self.name_entry.focus_set()

    @staticmethod
    def reminder_to_label(value):
        mapping = {
            None: "Ingen", 0: "Ingen", 5: "5 minuter", 10: "10 minuter",
            15: "15 minuter", 30: "30 minuter", 60: "60 minuter",
            1440: "1 dag",
        }
        return mapping.get(value, "Ingen")

    def save(self):
        name = self.name_entry.get().strip()
        task_date = self.date_entry.get().strip()
        task_time = self.time_entry.get().strip()

        if not name:
            messagebox.showwarning("Saknar namn", "Skriv ett namn på uppgiften.", parent=self)
            return

        try:
            datetime.strptime(task_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Fel datum", "Datum måste skrivas som ÅÅÅÅ-MM-DD.", parent=self
            )
            return

        try:
            datetime.strptime(task_time, "%H:%M")
        except ValueError:
            messagebox.showwarning(
                "Fel tid", "Tid måste skrivas som TT:MM, till exempel 09:30.", parent=self
            )
            return

        reminder_values = {
            "Ingen": None, "5 minuter": 5, "10 minuter": 10,
            "15 minuter": 15, "30 minuter": 30,
            "60 minuter": 60, "1 dag": 1440,
        }

        values = {
            "name": name,
            "category": self.category_menu.get(),
            "date": task_date,
            "time": task_time,
            "priority": self.priority_menu.get(),
            "description": self.description_box.get("1.0", "end").strip(),
            "notes": self.notes_box.get("1.0", "end").strip(),
            "reminder": reminder_values[self.reminder_menu.get()],
        }

        if self.task:
            update_task(self.task["id"], values)
        else:
            create_task(**values)

        if self.on_save:
            self.on_save()
        self.destroy()


class CategoryDialog(ctk.CTkToplevel):
    def __init__(self, master, on_change):
        super().__init__(master)
        self.on_change = on_change
        self.title("Hantera kategorier")
        self.geometry("480x520")
        self.transient(master)
        self.grab_set()

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Ny kategoris namn")
        self.name_entry.pack(fill="x", padx=20, pady=(20, 8))

        self.selected_color = "#4A90E2"
        self.color_button = ctk.CTkButton(
            self, text="Välj färg", fg_color=self.selected_color,
            command=self.choose_color
        )
        self.color_button.pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            self, text="Lägg till kategori", command=self.add
        ).pack(fill="x", padx=20, pady=8)

        self.category_list = ctk.CTkScrollableFrame(self, label_text="Befintliga kategorier")
        self.category_list.pack(fill="both", expand=True, padx=20, pady=12)
        self.refresh()

    def choose_color(self):
        result = colorchooser.askcolor(color=self.selected_color, parent=self)
        if result and result[1]:
            self.selected_color = result[1]
            self.color_button.configure(fg_color=self.selected_color)

    def add(self):
        success, message = add_category(self.name_entry.get(), self.selected_color)
        if success:
            self.name_entry.delete(0, "end")
            self.refresh()
            self.on_change()
        else:
            messagebox.showwarning("Kategorier", message, parent=self)

    def refresh(self):
        for widget in self.category_list.winfo_children():
            widget.destroy()

        for category in get_categories():
            row = ctk.CTkFrame(self.category_list)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row, text="●", text_color=category.get("color", "#808080"),
                font=ctk.CTkFont(size=20)
            ).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=category["name"]).pack(side="left", padx=5)
            ctk.CTkButton(
                row, text="Ta bort", width=75, fg_color="#B94A48",
                command=lambda name=category["name"]: self.remove(name)
            ).pack(side="right", padx=6, pady=5)

    def remove(self, name):
        if not messagebox.askyesno(
            "Ta bort kategori",
            f"Vill du ta bort kategorin '{name}'?",
            parent=self
        ):
            return
        delete_category(name)
        self.refresh()
        self.on_change()


class PlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        initialize_storage()
        archive_old_tasks()

        self.settings = load_settings()
        self.current_month = date.today().replace(day=1)
        self.selected_date = date.today()
        self.selected_task_id = None
        self.current_view = "calendar"

        ctk.set_appearance_mode(self.settings.get("theme", "light"))

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(950, 650)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main_area()
        self.show_calendar()
        self.refresh_task_list()
        self.check_reminders()

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar, text="MIN PLANERARE",
            font=ctk.CTkFont(size=21, weight="bold")
        ).pack(padx=18, pady=(28, 30))

        buttons = [
            ("Kalender", self.show_calendar),
            ("Alla uppgifter", self.show_all_tasks),
            ("Arkiv", self.show_archive),
            ("Kategorier", self.open_categories),
            ("Inställningar", self.open_settings),
        ]
        for label, command in buttons:
            ctk.CTkButton(
                self.sidebar, text=label, anchor="w", height=42,
                command=command
            ).pack(fill="x", padx=14, pady=5)

        ctk.CTkFrame(self.sidebar, height=2).pack(fill="x", padx=16, pady=20)

        ctk.CTkButton(
            self.sidebar, text="+ Ny uppgift", height=44,
            fg_color="#23865B", hover_color="#176B47",
            command=self.new_task
        ).pack(fill="x", padx=14, pady=5)

        self.sidebar_date_label = ctk.CTkLabel(
            self.sidebar, text=date.today().strftime("%d %B %Y"),
            text_color=("gray40", "gray70")
        )
        self.sidebar_date_label.pack(side="bottom", pady=22)

    def build_main_area(self):
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self.main, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.header.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            self.header, text="Kalender",
            font=ctk.CTkFont(size=27, weight="bold")
        )
        self.page_title.grid(row=0, column=0, sticky="w")

        self.content = ctk.CTkFrame(self.main)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_calendar(self):
        self.current_view = "calendar"
        self.page_title.configure(text="Kalender")
        self.clear_content()

        top = ctk.CTkFrame(self.content, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=12)

        ctk.CTkButton(
            top, text="‹", width=42, command=self.previous_month
        ).pack(side="left")
        ctk.CTkLabel(
            top, text=get_month_name(self.current_month.year, self.current_month.month),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            top, text="›", width=42, command=self.next_month
        ).pack(side="right")
        ctk.CTkButton(
            top, text="Idag", width=65, command=self.go_to_today
        ).pack(side="right", padx=8)

        calendar_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        calendar_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        for col in range(7):
            calendar_frame.grid_columnconfigure(col, weight=1, uniform="days")
        for row in range(7):
            calendar_frame.grid_rowconfigure(row, weight=1, uniform="weeks")

        week_start = self.settings.get("week_start", "monday")
        weekdays = ["Mån", "Tis", "Ons", "Tor", "Fre", "Lör", "Sön"]
        if week_start == "sunday":
            weekdays = ["Sön", "Mån", "Tis", "Ons", "Tor", "Fre", "Lör"]

        for col, name in enumerate(weekdays):
            ctk.CTkLabel(
                calendar_frame, text=name,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=col, padx=2, pady=5, sticky="nsew")

        weeks = get_month_days(
            self.current_month.year, self.current_month.month, week_start
        )
        all_tasks = load_tasks()
        active_tasks = [t for t in all_tasks if not t.get("archived", False)]

        for row_index, week in enumerate(weeks, start=1):
            for col_index, day in enumerate(week):
                is_current_month = day.month == self.current_month.month
                is_selected = day == self.selected_date
                is_today = day == date.today()

                if is_selected:
                    border_color = "#2878C8"
                elif is_today:
                    border_color = "#23865B"
                else:
                    border_color = ("#D5D9DE", "#454A52")

                cell = ctk.CTkFrame(
                    calendar_frame,
                    border_width=2 if (is_selected or is_today) else 1,
                    border_color=border_color,
                    fg_color=("white", "#292D33") if is_current_month else ("#F0F1F3", "#202329"),
                    corner_radius=8
                )
                cell.grid(
                    row=row_index, column=col_index,
                    padx=3, pady=3, sticky="nsew"
                )
                cell.grid_columnconfigure(0, weight=1)

                day_button = ctk.CTkButton(
                    cell, text=str(day.day), width=32, height=27,
                    fg_color="transparent", hover_color=("#E4EAF2", "#3A414B"),
                    text_color=("black" if is_current_month else "gray"),
                    anchor="w",
                    command=lambda selected=day: self.select_date(selected)
                )
                day_button.grid(row=0, column=0, padx=4, pady=(3, 1), sticky="w")

                day_tasks = [
                    t for t in active_tasks if t.get("date") == day.isoformat()
                ]
                for task_index, task in enumerate(day_tasks[:3], start=1):
                    color = get_category_color(task.get("category", ""))
                    task_label = ctk.CTkLabel(
                        cell,
                        text="• " + task.get("name", "Uppgift"),
                        anchor="w",
                        text_color=color,
                        font=ctk.CTkFont(size=10),
                    )
                    task_label.grid(
                        row=task_index, column=0, padx=5, pady=0, sticky="ew"
                    )
                if len(day_tasks) > 3:
                    ctk.CTkLabel(
                        cell, text=f"+ {len(day_tasks) - 3} till",
                        font=ctk.CTkFont(size=9), text_color="gray"
                    ).grid(row=4, column=0, padx=5, sticky="w")

        bottom = ctk.CTkFrame(self.content)
        bottom.pack(fill="x", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)

        self.selected_date_heading = ctk.CTkLabel(
            bottom,
            text=f"Uppgifter {self.selected_date.strftime('%Y-%m-%d')}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.selected_date_heading.grid(row=0, column=0, padx=12, pady=8, sticky="w")

        ctk.CTkButton(
            bottom, text="+ Lägg till", width=110,
            command=self.new_task
        ).grid(row=0, column=1, padx=12, pady=8)

        self.day_tasks_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        self.day_tasks_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        self.day_tasks_frame.grid_columnconfigure(0, weight=1)
        self.populate_day_tasks()

    def populate_day_tasks(self):
        for widget in self.day_tasks_frame.winfo_children():
            widget.destroy()

        tasks = get_tasks_for_date(self.selected_date)
        if not tasks:
            ctk.CTkLabel(
                self.day_tasks_frame, text="Inga uppgifter den här dagen.",
                text_color="gray"
            ).grid(row=0, column=0, sticky="w", padx=8, pady=6)
            return

        for index, task in enumerate(tasks):
            row = ctk.CTkFrame(self.day_tasks_frame)
            row.grid(row=index, column=0, sticky="ew", padx=4, pady=3)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row, text=task.get("time", ""),
                width=55, font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=0, padx=8, pady=7)
            ctk.CTkLabel(
                row, text=task.get("name", ""),
                anchor="w"
            ).grid(row=0, column=1, sticky="ew", padx=6)
            ctk.CTkLabel(
                row, text=task.get("category", ""),
                text_color=get_category_color(task.get("category", ""))
            ).grid(row=0, column=2, padx=8)
            ctk.CTkButton(
                row, text="Öppna", width=65,
                command=lambda item=task: self.edit_task(item)
            ).grid(row=0, column=3, padx=7, pady=5)

    def select_date(self, selected):
        self.selected_date = selected
        self.show_calendar()

    def previous_month(self):
        year, month = self.current_month.year, self.current_month.month - 1
        if month == 0:
            year, month = year - 1, 12
        self.current_month = date(year, month, 1)
        self.show_calendar()

    def next_month(self):
        year, month = self.current_month.year, self.current_month.month + 1
        if month == 13:
            year, month = year + 1, 1
        self.current_month = date(year, month, 1)
        self.show_calendar()

    def go_to_today(self):
        self.selected_date = date.today()
        self.current_month = date.today().replace(day=1)
        self.show_calendar()

    def new_task(self):
        TaskDialog(self, selected_date=self.selected_date, on_save=self.refresh_all)

    def edit_task(self, task):
        TaskDialog(self, task=task, on_save=self.refresh_all)

    def refresh_all(self):
        if self.current_view == "calendar":
            self.show_calendar()
        elif self.current_view == "all":
            self.show_all_tasks()
        elif self.current_view == "archive":
            self.show_archive()

    def refresh_task_list(self):
        # Behålls som en enkel gemensam uppdateringspunkt.
        return

    def show_all_tasks(self):
        self.current_view = "all"
        self.page_title.configure(text="Alla uppgifter")
        self.clear_content()

        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(
            toolbar, text="Dina kommande och aktiva uppgifter",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(
            toolbar, text="+ Ny uppgift", command=self.new_task
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(self.content)
        scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        tasks = filter_tasks()
        if not tasks:
            ctk.CTkLabel(scroll, text="Du har inga aktiva uppgifter.").pack(pady=20)
            return

        for task in tasks:
            self.create_task_row(scroll, task)

    def create_task_row(self, parent, task):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=4, pady=5)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text=f'{task.get("date", "")}  {task.get("time", "")}',
            width=145, font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=8, pady=10)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(
            info, text=task.get("name", ""),
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            info,
            text=f'{task.get("category", "")}  •  Prioritet: {task.get("priority", "Normal")}',
            text_color=get_category_color(task.get("category", "")),
            anchor="w"
        ).pack(fill="x")

        ctk.CTkButton(
            row, text="Redigera", width=85,
            command=lambda item=task: self.edit_task(item)
        ).grid(row=0, column=2, padx=5, pady=7)
        ctk.CTkButton(
            row, text="Ta bort", width=75, fg_color="#B94A48",
            command=lambda item=task: self.remove_task(item)
        ).grid(row=0, column=3, padx=(2, 8), pady=7)

    def remove_task(self, task):
        if messagebox.askyesno(
            "Ta bort uppgift",
            f'Vill du ta bort "{task.get("name", "uppgiften")}"?'
        ):
            delete_task(task["id"])
            self.refresh_all()

    def show_archive(self):
        self.current_view = "archive"
        self.page_title.configure(text="Arkiv")
        self.clear_content()

        ctk.CTkLabel(
            self.content, text="Arkiverade uppgifter",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=18, pady=16)

        scroll = ctk.CTkScrollableFrame(self.content)
        scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        tasks = get_archived_tasks()
        if not tasks:
            ctk.CTkLabel(scroll, text="Arkivet är tomt.").pack(pady=20)
            return

        for task in sorted(tasks, key=lambda t: (t.get("date", ""), t.get("time", ""))):
            row = ctk.CTkFrame(scroll)
            row.pack(fill="x", padx=4, pady=5)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row, text=f'{task.get("date", "")} {task.get("time", "")}',
                width=140
            ).grid(row=0, column=0, padx=8, pady=8)
            ctk.CTkLabel(
                row, text=task.get("name", ""), anchor="w"
            ).grid(row=0, column=1, sticky="ew", padx=5)
            ctk.CTkButton(
                row, text="Återställ", width=90,
                command=lambda item=task: self.restore_archived(item)
            ).grid(row=0, column=2, padx=8, pady=6)

    def restore_archived(self, task):
        restore_task(task["id"])
        self.show_archive()

    def open_categories(self):
        CategoryDialog(self, on_change=self.refresh_all)

    def open_settings(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Inställningar")
        dialog.geometry("420x330")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Inställningar",
            font=ctk.CTkFont(size=21, weight="bold")
        ).pack(pady=(20, 18))

        ctk.CTkLabel(dialog, text="Tema").pack(anchor="w", padx=25)
        theme_menu = ctk.CTkOptionMenu(dialog, values=["light", "dark", "system"])
        theme_menu.set(self.settings.get("theme", "light"))
        theme_menu.pack(fill="x", padx=25, pady=(5, 14))

        ctk.CTkLabel(dialog, text="Veckan börjar på").pack(anchor="w", padx=25)
        week_menu = ctk.CTkOptionMenu(
            dialog, values=["monday", "sunday"],
            command=None
        )
        week_menu.set(self.settings.get("week_start", "monday"))
        week_menu.pack(fill="x", padx=25, pady=(5, 14))

        ctk.CTkLabel(
            dialog, text="Påminnelse som standard (minuter)"
        ).pack(anchor="w", padx=25)
        reminder_entry = ctk.CTkEntry(dialog)
        reminder_entry.insert(
            0, str(self.settings.get("default_reminder", 30))
        )
        reminder_entry.pack(fill="x", padx=25, pady=(5, 14))

        def save():
            try:
                default_reminder = int(reminder_entry.get())
                if default_reminder < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Fel värde",
                    "Standardpåminnelsen måste vara ett positivt heltal.",
                    parent=dialog
                )
                return

            self.settings["theme"] = theme_menu.get()
            self.settings["week_start"] = week_menu.get()
            self.settings["default_reminder"] = default_reminder
            save_settings(self.settings)
            ctk.set_appearance_mode(self.settings["theme"])
            dialog.destroy()
            self.show_calendar()

        ctk.CTkButton(dialog, text="Spara inställningar", command=save).pack(
            fill="x", padx=25, pady=12
        )

    def check_reminders(self):
        """Kontrollerar om någon uppgift ska påminnas."""
        now = datetime.now()
        for task in load_tasks():
            if task.get("archived", False) or task.get("reminded", False):
                continue
            reminder = task.get("reminder")
            if reminder is None:
                continue
            try:
                due = datetime.strptime(
                    task["date"] + " " + task["time"], "%Y-%m-%d %H:%M"
                )
            except (ValueError, KeyError, TypeError):
                continue

            notify_at = due - timedelta(minutes=int(reminder))
            if notify_at <= now <= due:
                send_notification(
                    "Min Planerare",
                    f'{task.get("name", "Uppgift")} börjar kl. {task.get("time", "")}.'
                )
                update_task(task["id"], {"reminded": True})

        self.after(30000, self.check_reminders)


if __name__ == "__main__":
    app = PlannerApp()
    app.mainloop()
