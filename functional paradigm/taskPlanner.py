import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import Calendar
from datetime import datetime, timedelta
from collections import namedtuple
import json

# Immutable Task Representation as Tuple
Task = namedtuple("Task", ["title", "description", "due_date", "priority", "status", "creation_time", "highlight"])

####### functionality Functions :

# Adds a new task to the tasks tuple
def add_task(tasks, task_data):
    new_task = Task(**task_data)
    return tasks + (new_task,)

# Updates a task at a specific index
def update_task(tasks, index, updates):
    updated_task = tasks[index]._replace(**updates)
    return tasks[:index] + (updated_task,) + tasks[index + 1:]

# Deletes a task from the tasks tuple
def delete_task(tasks, index):
    return tasks[:index] + tasks[index + 1:]

# Sort tasks using a higher-order approach ( Genericity )
# using quick-sort algorithm , It splits tasks into tasks <= pivot  and tasks > pivot
def sort_tasks(tasks, key_function):
    if not tasks:
        return tasks
    pivot, *rest = tasks
    pivot_value = key_function(pivot)

    # Recursive filter function
    def filter_tasks(tasks, predicate):
        if not tasks:
            return []
        task = tasks[0]
        rest = tasks[1:]
        if predicate(task):
            return [task] + filter_tasks(rest, predicate)
        return filter_tasks(rest, predicate)

    less = filter_tasks(rest, lambda task: key_function(task) <= pivot_value)
    greater = filter_tasks(rest, lambda task: key_function(task) > pivot_value)
    return sort_tasks(less, key_function) + [pivot] + sort_tasks(greater, key_function)

# Key function for sorting by priority
def priority_key(task):
    priority_order = {"Low": 2, "Medium": 1, "High": 0}
    return priority_order[task.priority]

# Key function for sorting by due date
def due_date_key(task):
    return datetime.strptime(task.due_date, "%Y-%m-%d")

#Key function for sorting by creation time
def creation_time_key(task):
    return datetime.strptime(task.creation_time, "%Y-%m-%d %H:%M:%S")

# Key function for sorting by status
def status_key(task):
    return task.status

#filter tasks using a higher-order approach ( Genericity )
def filter_tasks(tasks, *criteria_functions):

    # Recursive filtering function
    def filter_recursive(tasks, filtered_tasks):
        if not tasks:
            return filtered_tasks
        task = tasks[0]
        rest = tasks[1:]

        # Check if the task matches all criteria
        def matches(task, criteria_index=0):
            if criteria_index == len(criteria_functions):
                return True
            return criteria_functions[criteria_index](task) and matches(task, criteria_index + 1)

        if matches(task):
            return filter_recursive(rest, filtered_tasks + (task,))
        return filter_recursive(rest, filtered_tasks)

    return filter_recursive(tasks, ())

# Criteria for priority
def priority_criteria(priority):
    return lambda task: task.priority == priority

# Criteria for status
def status_criteria(status):
    return lambda task: task.status == status

# Criteria for start date
def start_date_criteria(start_date):
    return lambda task: datetime.strptime(task.due_date, "%Y-%m-%d") >= start_date

# Criteria for end date
def end_date_criteria(end_date):
    return lambda task: datetime.strptime(task.due_date, "%Y-%m-%d") <= end_date


# Saves tasks to a JSON file
def save_tasks_to_file(tasks, filename="tasks.json"):

    # Recursive function to accumulate tasks
    def save_recursive(tasks, accumulated_tasks):
        if not tasks:
            with open(filename, "w") as file:
                json.dump(accumulated_tasks, file, indent=4)
            return
        task = tasks[0]
        rest = tasks[1:]
        save_recursive(rest, accumulated_tasks + [task._asdict()])

    save_recursive(tasks, [])

# Loads tasks from a JSON file
def load_tasks_from_file(filename="tasks.json"):
    try:
        with open(filename, "r") as file:

            # Recursive function to convert JSON data into Task objects
            def load_recursive(tasks_data, loaded_tasks):
                if not tasks_data:
                    return tuple(loaded_tasks)
                task_data = tasks_data[0]
                rest = tasks_data[1:]
                # Create Task object and recurse
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    due_date=task_data["due_date"],
                    priority=task_data["priority"],
                    status=task_data["status"],
                    creation_time=task_data["creation_time"],
                    highlight=task_data.get("highlight", False)
                )
                return load_recursive(rest, loaded_tasks + [task])

            return load_recursive(json.load(file), [])
    except FileNotFoundError:
        return ()


# Function to update task highlighting based on due dates and status
def check_task_highlighting(tasks):
    today = datetime.now().date()

    # Return an updated task based on highlighting rules
    def highlight_task(task):
        due_date = datetime.strptime(task.due_date, "%Y-%m-%d").date()
        status = task.status
        highlight = False
        if due_date < today and status == "Pending":
            status = "Overdue"
            highlight = True
        elif today <= due_date <= today + timedelta(days=2) and status == "Pending":
            highlight = True
        # Return a new task (updated copy)
        return Task(
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            priority=task.priority,
            status=status,
            highlight=highlight,
            creation_time=task.creation_time,
        )

    # Recursive processing of tasks to update highlights
    def process_tasks(tasks, processed_tasks=()):
        if not tasks:
            return processed_tasks
        return process_tasks(tasks[1:], processed_tasks + (highlight_task(tasks[0]),))
    return process_tasks(tasks)


####### GUI Functions :

# Update the GUI Treeview with the task Tuple
def update_task_list(tree, tasks):
    updated_tasks = check_task_highlighting(tasks)

    # Recursively clear rows from the Treeview
    def clear_tree(rows):
        if not rows:
            return
        tree.delete(rows[0])
        clear_tree(rows[1:])

    clear_tree(tree.get_children())

    # Recursively insert tasks into the Treeview
    def insert_tasks(tasks):
        if not tasks:
            return
        task = tasks[0]
        color = (
            "yellow" if task.highlight and task.status != "Overdue"
            else "red" if task.status == "Overdue"
            else "black"
        )
        tree.insert(
            "",
            "end",
            values=(task.title, task.description, task.due_date, task.priority, task.status),
            tags=(
                "highlight" if task.highlight and task.status != "Overdue"
                else "overdue" if task.status == "Overdue"
                else "normal"
            ),
        )
        insert_tasks(tasks[1:])

    insert_tasks(updated_tasks)
    tree.tag_configure("highlight", background="yellow")
    tree.tag_configure("overdue", background="red", foreground="white")
    tree.tag_configure("normal", background="white", foreground="black")
    return updated_tasks


# Open a GUI dialog to add a new task
def add_task_gui(root, tree, tasks):

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

    # handles add task logic
    def save_task():
        # Validation of Inputs
        if not title_entry.get().strip():
            messagebox.showerror("Input Error", "Title is required.")
            return
        if not priority_combobox.get():
            messagebox.showerror("Input Error", "Priority must be selected.")
            return
        if not description_entry.get():
            messagebox.showerror("Input Error", "Description is required.")
            return

        due_date = cal.get_date()
        creation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().date()
        selected_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        status = "Pending"
        highlight = False
        if selected_date < today:
            response = messagebox.askyesno("Date Warning", "The due date is in the past. Do you want to add this task anyway?")
            if not response:
                return
            status = "Overdue"
            highlight = True
            messagebox.showwarning("Overdue Tasks", f"The following tasks are overdue: {title_entry.get()}")
        task_data = {
            "title": title_entry.get(),
            "description": description_entry.get(),
            "due_date": due_date,
            "priority": priority_combobox.get(),
            "status": status,
            "creation_time": creation_time,
            "highlight": highlight,
        }
        new_tasks = add_task(tasks, task_data)
        update_task_list(tree, new_tasks)
        save_tasks_to_file(new_tasks)
        dialog.destroy()

    tk.Button(dialog, text="Save", command=save_task).grid(row=4, column=0, columnspan=2, pady=10)
    return tasks

# let the user update task
def update_task_gui(root, tree, tasks):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Select Task", "Please select a task to update.")
        return tasks

    selected_index = tree.index(selected_item[0])
    task = tasks[selected_index]

    dialog = tk.Toplevel(root)
    dialog.title("Update Task")

    tk.Label(dialog, text="Status:").grid(row=0, column=0, padx=10, pady=5)
    status_combobox = ttk.Combobox(dialog, values=["Leave as is", "Completed"], state="readonly")
    status_combobox.set("Leave as is")
    status_combobox.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(dialog, text="Priority:").grid(row=1, column=0, padx=10, pady=5)
    priority_combobox = ttk.Combobox(dialog, values=["Low", "Medium", "High"], state="readonly")
    priority_combobox.set(task.priority)
    priority_combobox.grid(row=1, column=1, padx=10, pady=5)

    # handles update task logic
    def save_update():
        updates = {}
        if status_combobox.get() != "Leave as is":
            updates["status"] = status_combobox.get()
        updates["priority"] = priority_combobox.get()

        new_tasks = update_task(tasks, selected_index, updates)
        update_task_list(tree, new_tasks)
        save_tasks_to_file(new_tasks)
        dialog.destroy()

    tk.Button(dialog, text="Save", command=save_update).grid(row=2, column=0, columnspan=2, pady=10)

    return tasks

# let the user delete task
def delete_task_gui(tree, tasks):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Select Task", "Please select a task to delete.")
        return tasks

    selected_index = tree.index(selected_item[0])
    task = tasks[selected_index]
    if messagebox.askyesno("Delete Task", f"Are you sure you want to delete task '{task.title}'?"):
        new_tasks = delete_task(tasks, selected_index)
        update_task_list(tree, new_tasks)
        save_tasks_to_file(new_tasks)
        return new_tasks
    return tasks

# opens the overdue tasks window
def show_overdue_tasks(tasks):

    # Recursive function to filter overdue tasks
    def filter_overdue_tasks(tasks, overdue_tasks):
        if not tasks:
            return overdue_tasks
        task = tasks[0]
        rest = tasks[1:]
        if task.status == "Overdue":
            overdue_tasks.append(task)
        return filter_overdue_tasks(rest, overdue_tasks)

    overdue_tasks = filter_overdue_tasks(tasks, [])
    if not overdue_tasks:
        return

    dialog = tk.Toplevel()
    dialog.title("Overdue Tasks")

    tree = ttk.Treeview(dialog, columns=("Title", "Description", "Due Date", "Priority", "Status"), show="headings")
    tree.heading("Title", text="Title")
    tree.heading("Description", text="Description")
    tree.heading("Due Date", text="Due Date")
    tree.heading("Priority", text="Priority")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)

    # Recursive function to insert overdue tasks into the Treeview
    def insert_task_recursive(tasks, index=0):
        if index >= len(tasks):
            return
        task = tasks[index]
        tree.insert("", "end", values=(task.title, task.description, task.due_date, task.priority, task.status))
        insert_task_recursive(tasks, index + 1)

    insert_task_recursive(overdue_tasks)

# opens the filter tasks window
def filter_tasks_gui(root, tree, tasks):
    dialog = tk.Toplevel(root)
    dialog.title("Filter Tasks")

    tk.Label(dialog, text="Priority:").grid(row=0, column=0, padx=10, pady=5)
    priority_combobox = ttk.Combobox(dialog, values=["Low", "Medium", "High", "All"], state="readonly")
    priority_combobox.grid(row=0, column=1, padx=10, pady=5)
    priority_combobox.set("All")

    tk.Label(dialog, text="Status:").grid(row=1, column=0, padx=10, pady=5)
    status_combobox = ttk.Combobox(dialog, values=["Pending", "Completed", "Overdue", "All"], state="readonly")
    status_combobox.grid(row=1, column=1, padx=10, pady=5)
    status_combobox.set("All")

    tk.Label(dialog, text="Start Date:").grid(row=2, column=0, padx=10, pady=5)
    start_date_cal = Calendar(dialog, date_pattern="yyyy-mm-dd")
    start_date_cal.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(dialog, text="End Date:").grid(row=3, column=0, padx=10, pady=5)
    end_date_cal = Calendar(dialog, date_pattern="yyyy-mm-dd")
    end_date_cal.grid(row=3, column=1, padx=10, pady=5)

    ignore_dates_var = tk.BooleanVar()
    ignore_dates_checkbox = tk.Checkbutton(dialog, text="Ignore Date Filters", variable=ignore_dates_var)
    ignore_dates_checkbox.grid(row=4, column=0, columnspan=2, pady=5)

    # handles filter tasks logic
    def apply_filter():
        # Extract the filter values
        priority = None if priority_combobox.get() == "All" else priority_combobox.get()
        status = None if status_combobox.get() == "All" else status_combobox.get()
        ignore_dates = ignore_dates_var.get()

        # Extract dates only if ignore_dates is False
        start_date = None
        end_date = None
        if not ignore_dates:
            start_date = datetime.strptime(start_date_cal.get_date(), "%Y-%m-%d")
            end_date = datetime.strptime(end_date_cal.get_date(), "%Y-%m-%d")

        criteria_functions = []
        if priority:
            criteria_functions.append(priority_criteria(priority))
        if status:
            criteria_functions.append(status_criteria(status))
        if start_date:
            criteria_functions.append(start_date_criteria(start_date))
        if end_date:
            criteria_functions.append(end_date_criteria(end_date))

        # Apply the filter with the dynamic criteria functions
        filtered_tasks = filter_tasks(tasks, *criteria_functions)

        # Update the UI with filtered tasks
        show_filtered_tasks(filtered_tasks)
        dialog.destroy()

    tk.Button(dialog, text="Apply Filter", command=apply_filter).grid(row=5, column=0, columnspan=2, pady=10)

# Displays the filtered Tuple of tasks in a new window using a Treeview
def show_filtered_tasks(filtered_tasks):
    dialog = tk.Toplevel()
    dialog.title("Filtered Tasks")

    tree = ttk.Treeview(dialog, columns=("Title", "Description", "Due Date", "Priority", "Status"), show="headings")
    tree.heading("Title", text="Title")
    tree.heading("Description", text="Description")
    tree.heading("Due Date", text="Due Date")
    tree.heading("Priority", text="Priority")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)

    # Recursive function to insert tasks into the Treeview
    def insert_task_recursive(tasks, index=0):
        if index >= len(tasks):
            return
        task = tasks[index]
        tree.insert("", "end", values=(task.title, task.description, task.due_date, task.priority, task.status))
        insert_task_recursive(tasks, index + 1)

    insert_task_recursive(filtered_tasks)



def main():
    tasks = load_tasks_from_file()     # Load the tasks from a JSON file

    root = tk.Tk()
    root.title("Task Manager")

    # Style object to customize the Treeview
    style = ttk.Style(root)

    # Change the look of the Treeview ( rows )
    style.configure("Treeview",
    background="#F0F0F0",              # Light gray background for rows
    foreground="#001A6E",              # dark blue font color for rows
    font=("Arial", 10))                # font of the table content

    # Change the header look ( first row )
    style.configure("Treeview.Heading",
    background="#001A6E",              # blue background for the header
    foreground="#00008B",              # Light font color for the header
    font=("Arial", 12, "bold"))        # Bold font for the header

    # Change background Color for the selected row
    style.map("Treeview",
            background=[('selected', '#4C75A3')])

    tree = ttk.Treeview(root, columns=("Title", "Description", "Due Date", "Priority", "Status"), show="headings")
    tree.heading("Title", text="Title")
    tree.heading("Description", text="Description")
    tree.heading("Due Date", text="Due Date")
    tree.heading("Priority", text="Priority")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)

    tasks = update_task_list(tree, tasks)
    show_overdue_tasks(tasks)

    # Frame to group the Add, Update, and Delete buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    button_style = {
        "bg": "#001A6E",        # Dark blue background for buttons
        "fg": "#F8FAFC",        # Light font color for buttons
        "font": ("Arial", 12)   # Bold font for the header
    }

    tk.Button(button_frame, text="Add Task", command=lambda: add_task_gui(root, tree, tasks), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Update Task", command=lambda: update_task_gui(root, tree, tasks), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Delete Task", command=lambda: delete_task_gui(tree, tasks), **button_style).pack(side=tk.LEFT, padx=10)

    # Frame to group the Sort and Filter buttons in the same row
    sort_filter_frame = tk.Frame(root)
    sort_filter_frame.pack(pady=10)

    tk.Button(sort_filter_frame, text="Sort by Priority", command=lambda: update_task_list(tree, sort_tasks(tasks, priority_key)), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(sort_filter_frame, text="Sort by Due Date", command=lambda: update_task_list(tree, sort_tasks(tasks, due_date_key)), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(sort_filter_frame, text="Sort by Status", command=lambda: update_task_list(tree, sort_tasks(tasks, status_key)), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(sort_filter_frame, text="Sort by Creation Time", command=lambda: update_task_list(tree, sort_tasks(tasks, creation_time_key)), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(sort_filter_frame, text="Filter Tasks", command=lambda: filter_tasks_gui(root, tree, tasks), **button_style).pack(side=tk.LEFT, padx=10)

    root.mainloop()

if __name__ == "__main__":
    main()
