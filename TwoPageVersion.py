import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os

class TaskDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.task_label = None
        self.task_width = None
        self.task_height = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Task Label:").grid(row=0)
        self.label_entry = tk.Entry(master)
        self.label_entry.grid(row=0, column=1)

        tk.Label(master, text="Task Width (default 100):").grid(row=1)
        self.width_entry = tk.Entry(master)
        self.width_entry.grid(row=1, column=1)
        self.width_entry.insert(0, "100")

        tk.Label(master, text="Task Height (default 30):").grid(row=2)
        self.height_entry = tk.Entry(master)
        self.height_entry.grid(row=2, column=1)
        self.height_entry.insert(0, "30")

        return self.label_entry  # initial focus

    def apply(self):
        self.task_label = self.label_entry.get()
        try:
            self.task_width = int(self.width_entry.get())
        except ValueError:
            self.task_width = 100  # default value
        try:
            self.task_height = int(self.height_entry.get())
        except ValueError:
            self.task_height = 30  # default value

class DragDropOrganizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.last_selected_label = None
        self.selected_week = 0  # Initialize with the first week selected

        self.title("Drag and Drop Organizer")

        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.times = [f"{hour}:00" for hour in range(5, 23)]  # 5 AM to 10 PM
        self.x_snap_interval = 100
        self.y_snap_interval = 5
        self.x_offset = -17
        self.y_offset = -2

        self.pages = []
        self.current_page = 0
        self.tasks = []
        self.ident = 1

        self.create_navigation()
        self.create_buttons()
        self.create_page()  # Create page for Week 1
        self.create_page()  # Create page for Week 2

        self.drag_data = {"x": 0, "y": 0, "item": None}

        self.load_tasks()
        self.show_page(0)
        self.update_window_size()

    def create_navigation(self):
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=0, column=0, columnspan=len(self.days)+2, pady=10)

        self.page_buttons = []
        for i in range(2):
            button = tk.Button(nav_frame, text=f"Week {i+1}", command=lambda i=i: self.show_page(i))
            button.pack(side="left", padx=10)
            self.page_buttons.append(button)

        self.update_selected_week_button()  # Initially set the selected week button appearance

    def update_selected_week_button(self):
        for i, button in enumerate(self.page_buttons):
            if i == self.selected_week:
                button.config(relief="sunken")  # Set the selected week button as sunken (pressed)
            else:
                button.config(relief="raised")  # Reset other buttons to raised (not pressed)

    def show_page(self, page_index):
        if 0 <= page_index < len(self.pages):
            self.selected_week = page_index
            self.update_selected_week_button()

            for page in self.pages:
                page.grid_remove()
            self.pages[page_index].grid(row=2, column=0, columnspan=len(self.days)+2)
            self.current_page = page_index

    def create_buttons(self):
        button_frame = tk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=len(self.days)+2, pady=10)

        add_button = tk.Button(button_frame, text="Add Task", command=self.add_task)
        add_button.pack(side="left", padx=10)

        delete_button = tk.Button(button_frame, text="Delete Task", command=self.delete_task)
        delete_button.pack(side="left", padx=10)

        save_button = tk.Button(button_frame, text="Save Tasks", command=self.save_tasks)
        save_button.pack(side="left", padx=10)

    def create_page(self):
        page_frame = tk.Frame(self)
        page_frame.grid(row=2, column=0, columnspan=len(self.days)+2)

        for col, day in enumerate(self.days):
            color = "lightblue"
            if day in ["Sat", "Sun"]:
                color = "green"
            label = tk.Label(page_frame, text=day, bg=color)
            label.grid(row=0, column=col+1, sticky="nsew")

        for row, time in enumerate(self.times):
            label = tk.Label(page_frame, text=time, bg="lightblue")
            label.grid(row=row+1, column=0, sticky="nsew")

        for row in range(1, len(self.times) + 1):
            for col in range(1, len(self.days) + 1):
                frame = tk.Frame(page_frame, bd=1, relief="sunken", width=100, height=30)
                frame.grid(row=row, column=col, sticky="nsew")
                frame.grid_propagate(False)

        self.pages.append(page_frame)

    def add_task(self):
        dialog = TaskDialog(self, title="New Task")
        task_label = dialog.task_label
        task_width = dialog.task_width
        task_height = dialog.task_height

        if not task_label:
            return

        spacing = round(task_height/10) * "\n"
        task_label = spacing + task_label + spacing + str(self.ident)
        label = tk.Label(self.pages[self.current_page], text=task_label, bg="yellow", bd=1, relief="raised")
        label.place(x=50, y=50, width=task_width, height=task_height)
        label.bind("<ButtonPress-1>", self.on_start_drag)
        label.bind("<B1-Motion>", self.on_drag)
        label.bind("<ButtonRelease-1>", self.on_drop)

        self.tasks.append({
            "label": task_label,
            "x": 50,
            "y": 50,
            "width": task_width,
            "height": task_height,
            "page": self.current_page
        })
        self.ident += 1

    def delete_task(self):
        if self.last_selected_label is None:
            messagebox.showwarning("No Task Selected", "Please select a task to delete.")
            return

        label_to_delete = self.last_selected_label
        label_text = label_to_delete.cget("text")  # Get text BEFORE destroying
        label_to_delete.destroy()

        # Remove task from self.tasks list based on the label text
        self.tasks = [task for task in self.tasks if task["label"] != label_text]

        self.last_selected_label = None
        self.drag_data["item"] = None

        messagebox.showinfo("Task Deleted", "Task deleted.")

    def on_start_drag(self, event):
        if self.last_selected_label is not None:
            self.last_selected_label.config(bg="yellow")
        widget = event.widget
        widget.config(bg="cyan")
        self.drag_data["item"] = widget
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y + 50
        self.last_selected_label = widget  # Update last selected label

    def on_drag(self, event):
        widget = self.drag_data["item"]
        if not widget or not str(widget):
            return
        x = self.winfo_pointerx() - self.winfo_rootx() - self.drag_data["x"]
        y = self.winfo_pointery() - self.winfo_rooty() - self.drag_data["y"]
        snap_x = self.snap_to_grid(x, self.x_snap_interval) + self.x_offset
        snap_y = self.snap_to_grid(y, self.y_snap_interval) + self.y_offset
        widget.place(x=snap_x, y=snap_y)

    def snap_to_grid(self, coordinate, interval):
        """ Snap coordinate to nearest interval """
        offset = interval / 2  # Adjusting for half interval offset
        return round((coordinate + offset) / interval) * interval - offset

    def on_drop(self, event):
        widget = event.widget
        x = self.winfo_pointerx() - self.winfo_rootx() - self.drag_data["x"]
        y = self.winfo_pointery() - self.winfo_rooty() - self.drag_data["y"]
        snap_x = self.snap_to_grid(x, self.x_snap_interval) + self.x_offset
        snap_y = self.snap_to_grid(y, self.y_snap_interval) + self.y_offset
        widget.place(x=snap_x, y=snap_y)

        for task in self.tasks:
            if task["label"] == widget.cget("text"):
                task["x"] = snap_x
                task["y"] = snap_y
                task["page"] = self.current_page
                break

    def save_tasks(self):
        with open("Save/tasks.json", "w") as file:
            for task in self.tasks:
                task["x"] = task["x"] + 700 if task["page"] == 1 else task["x"]
            json.dump(self.tasks, file)
        with open("Save/ident.json", "w") as file:
            json.dump(self.ident, file)
        messagebox.showinfo("Save Tasks", "Tasks have been saved successfully.")

    def load_tasks(self):
        if os.path.exists("Save/ident.json"):
            with open("Save/ident.json", "r") as file:
                self.ident = json.load(file)

        if os.path.exists("Save/tasks.json"):
            with open("Save/tasks.json", "r") as file:
                self.tasks = json.load(file)

        for task in self.tasks:
            page_index = 0 if task["x"] < 700 else 1  # Determine page based on x-coordinate
            task["x"] = task["x"] - 700 if task["x"] > 700 else task["x"]
            task["page"] = page_index
            page = self.pages[page_index]
            label = tk.Label(page, text=task["label"], bg="yellow", bd=1, relief="raised")
            label.place(x=task["x"], y=task["y"], width=task["width"], height=task["height"])
            label.bind("<ButtonPress-1>", self.on_start_drag)
            label.bind("<B1-Motion>", self.on_drag)
            label.bind("<ButtonRelease-1>", self.on_drop)

    def update_window_size(self):
        self.update_idletasks()
        width = max(self.winfo_width(), 100 * len(self.days) + 100)
        height = max(self.winfo_height(), 30 * len(self.times) + 60 + 50)  # 60 for headers, 50 for buttons
        self.geometry(f"{width}x{height}")

if __name__ == "__main__":
    app = DragDropOrganizer()
    app.mainloop()

# pyinstaller --onefile --icon=D:\MyStuff\Python\Projects\DragAndDropOrganiser\icon\logo.ico --noconsole D:\MyStuff\Python\Projects\DragAndDropOrganiser\TwoPageVersion.py
# ^ for making into .exe
