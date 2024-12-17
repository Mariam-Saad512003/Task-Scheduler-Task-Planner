import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import Calendar
import json
from datetime import datetime, timedelta

# Pure functions for state management
def custom_min(lst, key_func):
    if not lst:
        raise ValueError("min() arg is an empty sequence")
    min_item = lst[0]
    for item in lst[1:]:
        if key_func(item) < key_func(min_item):
            min_item = item
    return min_item

def custom_append(lst, item):
    new_list = lst + [item]
    return new_list

def load_tasks():
    try:
        with open("tasks.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_tasks(tasks):
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=4)

def add_task(state, task):
    updated_task = {**task, "highlight": datetime.strptime(task["due_date"], "%Y-%m-%d").date() <= datetime.now().date() + timedelta(days=2) and task["status"] != "Completed"}
    return {**state, "tasks": state["tasks"] + [updated_task]}

def update_task(state, index, priority, status=None):
    tasks = state["tasks"]
    updated_task = {**tasks[index], "priority": priority}
    if status is not None:
        updated_task["status"] = status
    # Update highlight status based on the new status
    updated_task["highlight"] = datetime.strptime(updated_task["due_date"], "%Y-%m-%d").date() <= datetime.now().date() + timedelta(days=2) and updated_task["status"] != "Completed"
    new_tasks = tasks[:index] + [updated_task] + tasks[index + 1:]
    return {**state, "tasks": new_tasks}

def delete_task(state, index):
    tasks = state["tasks"]
    new_tasks = tasks[:index] + tasks[index + 1:]
    return {**state, "tasks": new_tasks}

def update_status_due_dates(state):
    today = datetime.now().date()
    updated_tasks = update_status_due_dates_recursive(state["tasks"], today)
    return {**state, "tasks": updated_tasks}

def update_status_due_dates_recursive(tasks, today, index=0, acc=None):
    if acc is None:
        acc = []
    if index >= len(tasks):
        return acc
    task = tasks[index]
    if task["status"] == "Pending" and datetime.strptime(task["due_date"], "%Y-%m-%d").date() < today:
        task = {**task, "status": "Overdue"}
    acc = custom_append(acc, task)
    return update_status_due_dates_recursive(tasks, today, index + 1, acc)

def update_highlight_due_soon(state):
    today = datetime.now().date()
    updated_tasks = update_highlight_due_soon_recursive(state["tasks"], today)
    return {**state, "tasks": updated_tasks}

def update_highlight_due_soon_recursive(tasks, today, index=0, acc=None):
    if acc is None:
        acc = []
    if index >= len(tasks):
        return acc
    task = tasks[index]

    # Highlight overdue tasks in red
    if task["status"] == "Overdue":
        task = {**task, "highlight": True}

    highlight = datetime.strptime(task["due_date"], "%Y-%m-%d").date() <= today + timedelta(days=2) and task["status"] != "Completed"

    task = {**task, "highlight": highlight}

    acc = custom_append(acc, task)

    return update_highlight_due_soon_recursive(tasks, today, index + 1, acc)

def filter_tasks(state, priority, status, start_date=None, end_date=None):
    tasks = state["tasks"]

    filtered_tasks = filter_tasks_recursive(tasks, priority, status, start_date, end_date)

    return {**state, "tasks": filtered_tasks}

def filter_tasks_recursive(tasks, priority, status, start_date=None, end_date=None, index=0, acc=None):
    if acc is None:
        acc = []

    if index >= len(tasks):
        return acc

    task = tasks[index]

    due_date = datetime.strptime(task["due_date"], "%Y-%m-%d")

    matches = True

    if priority != "All" and task["priority"] != priority:
        matches = False

    if status != "All" and task["status"] != status:
        matches = False

    if start_date and end_date and not (start_date <= due_date <= end_date):
        matches = False

    if matches:
        acc = custom_append(acc, task)

    return filter_tasks_recursive(tasks, priority, status, start_date, end_date, index + 1, acc)

def sort_by_priority(task):
    return {"Low": 0, "Medium": 1, "High": 2}[task["priority"]]

def sort_by_due_date(task):
    return datetime.strptime(task["due_date"], "%Y-%m-%d")

def sort_by_status(task):
    return task["status"]

def sort_tasks(state, key_func):
    sorted_tasks = sort_tasks_recursive(state["tasks"], key_func)

    return {**state, "tasks": sorted_tasks}

def sort_tasks_recursive(tasks,key_func ,acc=None):

    if acc is None:
        acc = []

    if not tasks:
        return acc

    min_task = custom_min(tasks,key_func)

    tasks.remove(min_task)

    acc=custom_append(acc,min_task)

    return sort_tasks_recursive(tasks,key_func ,acc)

# GUI-related functions (stateless rendering)
def render_treeview(tree ,items ):
    tree.delete(*tree.get_children())
    for item in items:
        tree.insert(
            "",
            "end",
            values=(item ["title"],item ["description"],item ["due_date"],item ["priority"],item ["status"]),
            tags=("overdue" if item.get("status") == "Overdue" else "highlight" if item.get("highlight", False) else "normal"),
        )
    tree.tag_configure("overdue", background="red", foreground="white")
    tree.tag_configure("highlight", background="yellow")

def get_selected_task_index(tree, tasks):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Select Task", "Please select a task to update or delete.")
        return None
    title = tree.item(selected_item[0], "values")[0]
    for index, task in enumerate(tasks):
        if task["title"] == title:
            return index
    return None

# Function to open a window with overdue tasks
def open_overdue_window(overdue_tasks):
    overdue_window = tk.Toplevel()
    overdue_window.title("Overdue Tasks")
    overdue_tree = ttk.Treeview(
        overdue_window,
        columns=("Title", "Description", "Due Date", "Priority", "Status"),
        show="headings",
    )
    overdue_tree.heading("Title", text="Title")
    overdue_tree.heading("Description", text="Description")
    overdue_tree.heading("Due Date", text="Due Date")
    overdue_tree.heading("Priority", text="Priority")
    overdue_tree.heading("Status", text="Status")
    overdue_tree.pack(fill=tk.BOTH, expand=True)
    render_treeview(overdue_tree, overdue_tasks)

def main():
    # Initial state
    state = {"tasks": update_highlight_due_soon(update_status_due_dates({"tasks": load_tasks()}))["tasks"]}
    def update_state(new_state):
        nonlocal state
        state = new_state
        save_tasks(state["tasks"])
        render_treeview(tree, state["tasks"])

    root = tk.Tk()
    root.title("Functional Task Manager")

    # Create a Style object to customize the Treeview
    style = ttk.Style(root)

    # Customize the appearance of the Treeview (content rows)
    style.configure("Treeview",
    background="#F0F0F0",# Light gray background for rows
    foreground="#001A6E",   # Set font color to dark blue for rows
    font=("Arial", 10))      # Set font for the table content

    # Customize the header appearance (first row)
    style.configure("Treeview.Heading",
    background="#001A6E",  # Dark blue background for the header
    foreground="#00008B",   # Light font color for the header
    font=("Arial", 12, "bold"))  # Bold font for the header

    # Set a color for the selected row
    style.map("Treeview",
    background=[('selected', '#4C75A3')])  # Color for selected row

    tree = ttk.Treeview(
    root,
    columns=("Title", "Description", "Due Date", "Priority", "Status"),
    show="headings",
    )
    tree.heading("Title", text="Title")
    tree.heading("Description", text="Description")
    tree.heading("Due Date", text="Due Date")
    tree.heading("Priority", text="Priority")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)
    render_treeview(tree, state["tasks"])


def main():
    # Initial state
    state = {"tasks": update_highlight_due_soon(update_status_due_dates({"tasks": load_tasks()}))["tasks"]}
    def update_state(new_state):
        nonlocal state
        state = new_state
        save_tasks(state["tasks"])
        render_treeview(tree, state["tasks"])

    root = tk.Tk()
    root.title("Functional Task Manager")

    # Create a Style object to customize the Treeview
    style = ttk.Style(root)

    # Customize the appearance of the Treeview (content rows)
    style.configure("Treeview",
    background="#F0F0F0",# Light gray background for rows
    foreground="#001A6E",   # Set font color to dark blue for rows
    font=("Arial", 10))      # Set font for the table content

    # Customize the header appearance (first row)
    style.configure("Treeview.Heading",
    background="#001A6E",  # Dark blue background for the header
    foreground="#00008B",   # Light font color for the header
    font=("Arial", 12, "bold"))  # Bold font for the header

    # Set a color for the selected row
    style.map("Treeview",
    background=[('selected', '#4C75A3')])  # Color for selected row

    tree = ttk.Treeview(
    root,
    columns=("Title", "Description", "Due Date", "Priority", "Status"),
    show="headings",
    )
    tree.heading("Title", text="Title")
    tree.heading("Description", text="Description")
    tree.heading("Due Date", text="Due Date")
    tree.heading("Priority", text="Priority")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)
    render_treeview(tree, state["tasks"])

    # Open overdue tasks window
    overdue_tasks = [task for task in state["tasks"] if task["status"] == "Overdue"]
    open_overdue_window(overdue_tasks)

    def add_task_gui():
        dialog = tk.Toplevel(root)
        dialog.title("Add Task")
        tk.Label(dialog, text="Title:").grid(row=0, column=0, padx=10, pady=5)
        title_entry = tk.Entry(dialog)
        title_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(dialog, text="Description:").grid(row=1, column=0, padx=10, pady=5)
        description_entry = tk.Entry(dialog)
        description_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(dialog, text="Due Date:").grid(row=2, column=0, padx=10, pady=5)
        cal = Calendar(dialog, date_pattern="yyyy-mm-dd")
        cal.grid(row=2, column=1, padx=10, pady=5)
        tk.Label(dialog, text="Priority:").grid(row=3, column=0, padx=10, pady=5)
        priority_combobox = ttk.Combobox(dialog, values=["Low", "Medium", "High"], state="readonly")
        priority_combobox.grid(row=3, column=1, padx=10, pady=5)

        def save_task():
            if not title_entry.get().strip() or not priority_combobox.get():
                messagebox.showerror("Input Error", "All fields must be completed.")
                return
            task_data = {
                "title": title_entry.get(),
                "description": description_entry.get(),
                "due_date": cal.get_date(),
                "priority": priority_combobox.get(),
                "status": "Pending",
                "highlight": False,
            }
            # Check if the due date is in the past
            due_date = datetime.strptime(task_data["due_date"], "%Y-%m-%d").date()
            if due_date < datetime.now().date():
                result = messagebox.askyesno(
                    "Date Warning",
                    "The due date is in the past. Do you want to add this task anyway?"
                )
                if not result:
                    dialog.destroy()
                    return
                task_data["status"] = "Overdue"
                messagebox.showinfo("Overdue Tasks", f"The following tasks are overdue: {task_data['title']}")
            # Update the task with its correct highlight status
            updated_task = {**task_data, "highlight": datetime.strptime(task_data["due_date"], "%Y-%m-%d").date() <= datetime.now().date() + timedelta(days=2) and task_data["status"] != "Completed"}
            update_state(add_task(state, updated_task))
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save_task).grid(row=4, column=0, columnspan=2, pady=10)

    def delete_task_gui():
        index = get_selected_task_index(tree, state["tasks"])
        if index is not None and messagebox.askyesno(
            "Delete Task", f"Are you sure you want to delete task '{state['tasks'][index]['title']}'?"
        ):
            update_state(delete_task(state, index))

    def update_task_gui():
        index = get_selected_task_index(tree, state["tasks"])
        if index is None:
            return
        dialog = tk.Toplevel(root)
        dialog.title("Update Task")
        tk.Label(dialog, text="Priority:").grid(row=0, column=0, padx=10, pady=5)
        priority_combobox = ttk.Combobox(dialog, values=["Low", "Medium", "High"], state="readonly")
        priority_combobox.set(state["tasks"][index]["priority"])
        priority_combobox.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(dialog, text="Status:").grid(row=1, column=0, padx=10, pady=5)
        status_combobox = ttk.Combobox(dialog, values=["Leave as is", "Completed"], state="readonly")
        status_combobox.set("Leave as is")
        status_combobox.grid(row=1, column=1, padx=10, pady=5)

        def save_updates():
            new_status = None if status_combobox.get() == "Leave as is" else "Completed"
            update_state(update_task(state, index, priority_combobox.get(), new_status))
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save_updates).grid(row=2, column=0, columnspan=2, pady=10)

    def filter_tasks_gui():
        dialog = tk.Toplevel(root)
        dialog.title("Filter Tasks")
        tk.Label(dialog, text="Priority:").grid(row=0, column=0, padx=10, pady=5)
        priority_combobox = ttk.Combobox(dialog, values=["All", "Low", "Medium", "High"], state="readonly")
        priority_combobox.set("All")
        priority_combobox.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(dialog, text="Status:").grid(row=1, column=0, padx=10, pady=5)
        status_combobox = ttk.Combobox(dialog, values=["All", "Pending", "Completed", "Overdue"], state="readonly")
        status_combobox.set("All")
        status_combobox.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(dialog, text="Start Date:").grid(row=2, column=0, padx=10, pady=5)
        start_cal = Calendar(dialog, date_pattern="yyyy-mm-dd")
        start_cal.grid(row=2, column=1, padx=10, pady=5)
        tk.Label(dialog, text="End Date:").grid(row=3, column=0, padx=10, pady=5)
        end_cal = Calendar(dialog, date_pattern="yyyy-mm-dd")
        end_cal.grid(row=3, column=1, padx=10, pady=5)
        ignore_dates_var = tk.BooleanVar()
        ignore_dates_check = tk.Checkbutton(dialog, text="Ignore Dates", variable=ignore_dates_var)
        ignore_dates_check.grid(row=4, column=0, columnspan=2, pady=5)

        def apply_filter():
            start_date = start_cal.get_date() if not ignore_dates_var.get() and start_cal.get_date() else None
            end_date = end_cal.get_date() if not ignore_dates_var.get() and end_cal.get_date() else None
            filtered_state = filter_tasks(
                state,
                priority_combobox.get(),
                status_combobox.get(),
                datetime.strptime(start_date, "%Y-%m-%d") if start_date else None,
                datetime.strptime(end_date, "%Y-%m-%d") if end_date else None,
            )
            if not filtered_state["tasks"]:
                messagebox.showinfo("No Results", "No tasks match the filter criteria.")
                return
            results_window = tk.Toplevel(root)
            results_window.title("Filtered Tasks")
            results_tree = ttk.Treeview(
                results_window,
                columns=("Title", "Description", "Due Date", "Priority", "Status"),
                show="headings",
            )
            results_tree.heading("Title", text="Title")
            results_tree.heading("Description", text="Description")
            results_tree.heading("Due Date", text="Due Date")
            results_tree.heading("Priority", text="Priority")
            results_tree.heading("Status", text="Status")
            results_tree.pack(fill=tk.BOTH, expand=True)
            render_treeview(results_tree, filtered_state["tasks"])
            tk.Button(results_window, text="Close", command=results_window.destroy).pack(pady=10)
            dialog.destroy()

        tk.Button(dialog, text="Apply", command=apply_filter).grid(row=5, column=0, columnspan=2, pady=10)

    def sort_by_priority_gui():
        update_state(sort_tasks(state, sort_by_priority))

    def sort_by_due_date_gui():
        update_state(sort_tasks(state, sort_by_due_date))

    def sort_by_status_gui():
        update_state(sort_tasks(state, sort_by_status))

    # Frame to group the Add, Update, and Delete buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    button_style = {
        "bg": "#001A6E",  # Dark blue background for buttons
        "fg": "#F8FAFC",  # Light font color for buttons
        "font": ("Arial", 12)
    }
    tk.Button(button_frame, text="Add Task", command=add_task_gui, **button_style).grid(row=0, column=0, padx=10)
    tk.Button(button_frame, text="Update Task", command=update_task_gui, **button_style).grid(row=0, column=1, padx=10)
    tk.Button(button_frame, text="Delete Task", command=delete_task_gui, **button_style).grid(row=0, column=2, padx=10)

    # Frame to group the Sort and Filter buttons in the same row
    sort_filter_frame = tk.Frame(root)
    sort_filter_frame.pack(pady=10)
    tk.Button(sort_filter_frame, text="Sort by Priority", command=sort_by_priority_gui, **button_style).grid(row=1, column=0, padx=10)
    tk.Button(sort_filter_frame, text="Sort by Due Date", command=sort_by_due_date_gui, **button_style).grid(row=1, column=1, padx=10)
    tk.Button(sort_filter_frame, text="Sort by Status", command=sort_by_status_gui, **button_style).grid(row=1, column=2, padx=10)
    tk.Button(sort_filter_frame, text="Filter Tasks", command=filter_tasks_gui, **button_style).grid(row=1, column=3, padx=10)

    root.mainloop()


if __name__ == "__main__":
    main()
