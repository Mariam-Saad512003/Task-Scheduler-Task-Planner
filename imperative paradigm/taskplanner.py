import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import Calendar
import json
from datetime import datetime, timedelta

# Global variables
tasks = []

# Functions to manage tasks
def load_tasks():
    global tasks
    try:
        with open("tasks.json", "r") as file:
            task_dicts = json.load(file)
            tasks = task_dicts
    except FileNotFoundError:
        tasks = []

def save_tasks():
    global tasks
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=4)

def update_task(index, priority, status):
    global tasks
    tasks[index]["priority"] = priority

def add_task(task):
    global tasks
    tasks.append(task)

def save_tasks():
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, default=str, indent=4)

def add_task_gui(root, tree):
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
        if not title_entry.get().strip():
            messagebox.showerror("Input Error", "Title is required.")
            return
        if not priority_combobox.get():
            messagebox.showerror("Input Error", "Priority must be selected.")
            return

        due_date = cal.get_date()
        today = datetime.now().date()
        selected_date = datetime.strptime(due_date, "%Y-%m-%d").date()

        if selected_date < today:
            response = messagebox.askyesno("Date Warning", "The due date is in the past. Do you want to add this task anyway?")
            if not response:
                return

        # Get current timestamp for creation time
        creation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        task_data = {
            "title": title_entry.get(),
            "description": description_entry.get(),
            "due_date": due_date,
            "priority": priority_combobox.get(),
            "status": "Pending",
            "creation_time": creation_time,  # Add creation time to task data
        }

        add_task(task_data)
        save_tasks()  # Save tasks to the JSON file
        update_task_list(tree)  # Update UI
        dialog.destroy()

    tk.Button(dialog, text="Save", command=save_task).grid(row=4, column=0, columnspan=2, pady=10)

def delete_task(index):
    global tasks
    del tasks[index]

def check_due_dates():
    global tasks
    today = datetime.now().date()
    overdue_tasks = []
    for task in tasks:
        due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
        if due_date < today and task["status"] == "Pending":
            task["status"] = "Overdue"
            overdue_tasks.append(task)
        elif due_date <= today + timedelta(days=2) and task["status"] != "Completed":
            # Highlight tasks nearing deadlines (within 2 days)
            task["highlight"] = True
        else:
            task["highlight"] = False

    if overdue_tasks:
        overdue_task_titles = ", ".join([task["title"] for task in overdue_tasks])
        messagebox.showwarning("Overdue Tasks", f"The following tasks are overdue: {overdue_task_titles}")

def update_task_list(tree):
    global tasks
    check_due_dates()  # Assuming this function updates task states based on due dates
      
    for row in tree.get_children():
        tree.delete(row)

    for task in tasks:
        # Parse the due_date into a datetime object for comparison
        due_date = datetime.strptime(task["due_date"], "%Y-%m-%d")
        today = datetime.now()

        # Check if task is "completed" - do not highlight
        if task["status"].lower() == "completed":
            task["highlight"] = "none"  # Reset any previous highlighting
        else:
            # Check if task is overdue (due date has passed)
            if due_date < today:  # Overdue tasks
                task["highlight"] = 'red'
            elif due_date - today <= timedelta(days=2):  # Tasks due soon
                task["highlight"] = 'yellow'
            else:
                task["highlight"] = "normal"  # Default state

        # Insert the task into the treeview
        tree.insert("", "end", 
                    values=(task["title"], task["description"], task["due_date"], task["priority"], task["status"]),
                    tags=('highlight' if task["highlight"] == 'yellow' 
                          else 'overdue' if task["highlight"] == 'red' 
                          else 'normal'))

    # Configure the tags for highlighting
    tree.tag_configure('highlight', background='yellow')  # Highlight tasks due soon
    tree.tag_configure('overdue', background='red', foreground='white')  # Highlight overdue tasks
    tree.tag_configure('normal', background='white', foreground='black')  # Default style for normal tasks

    save_tasks()

def task_dialog(root, tree, action, task=None):
    dialog = tk.Toplevel(root)
    dialog.title(f"{action} Task")

    # Label and combobox for the status
    tk.Label(dialog, text="Status:").grid(row=0, column=0, padx=10, pady=5)
    status_combobox = ttk.Combobox(dialog, values=["Completed"], state="readonly")
    status_combobox.grid(row=0, column=1, padx=10, pady=5)

    # Label and combobox for the priority
    tk.Label(dialog, text="Priority:").grid(row=1, column=0, padx=10, pady=5)
    priority_combobox = ttk.Combobox(dialog, values=["Low", "Medium", "High"], state="readonly")
    priority_combobox.grid(row=1, column=1, padx=10, pady=5)

    if task:
        status_combobox.set(task["status"])
        priority_combobox.set(task["priority"])

    def save_task():
        # Ensure that the status and priority are selected
        if not status_combobox.get() or not priority_combobox.get():
            messagebox.showerror("Input Error", "Both Status and Priority must be selected.")
            return

        selected_task_index = get_selected_task_index(tree)
        if selected_task_index is not None:
            # Update task status and priority
            tasks[selected_task_index]["status"] = status_combobox.get()
            tasks[selected_task_index]["priority"] = priority_combobox.get()

        # Save the tasks and update the Treeview
        save_tasks()
        update_task_list(tree)
        dialog.destroy()

    # Save button
    tk.Button(dialog, text="Save", command=save_task).grid(row=2, column=0, columnspan=2, pady=10)

def update_task_gui(root, tree):
    selected_task_index = get_selected_task_index(tree)
    if selected_task_index is not None:
        task_dialog(root, tree, "Update", tasks[selected_task_index])

def delete_task_gui(tree):
    selected_task_index = get_selected_task_index(tree)
    if selected_task_index is not None:
        task = tasks[selected_task_index]
        if messagebox.askyesno("Delete Task", f"Are you sure you want to delete task '{task['title']}'?"):
            delete_task(selected_task_index)
            save_tasks()
            update_task_list(tree)

def get_selected_task_index(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Select Task", "Please select a task to update or delete.")
        return None
    selected_item = selected_item[0]
    title = tree.item(selected_item, "values")[0]  # Adjusted for task_id being removed
    for index, task in enumerate(tasks):
        if task["title"] == title:
            return index
    return None

def sort_tasks(tree, sort_key):
    global tasks

    # Bubble Sort Algorithm
    n = len(tasks)
    
    # Perform the Bubble Sort
    for i in range(n):
        for j in range(0, n-i-1):
            swap = False
            # Compare two adjacent tasks based on the sort_key
            if sort_key == "priority":
                priority_order = {"Low": 0, "Medium": 1, "High": 2}
                if priority_order[tasks[j][sort_key]] > priority_order[tasks[j + 1][sort_key]]:
                    tasks[j], tasks[j + 1] = tasks[j + 1], tasks[j]
                    swap = True
            elif sort_key == "due_date":
                if datetime.strptime(tasks[j][sort_key], "%Y-%m-%d") > datetime.strptime(tasks[j + 1][sort_key], "%Y-%m-%d"):
                    tasks[j], tasks[j + 1] = tasks[j + 1], tasks[j]
                    swap = True
            elif sort_key == "status":
                if tasks[j][sort_key] > tasks[j + 1][sort_key]:
                    tasks[j], tasks[j + 1] = tasks[j + 1], tasks[j]
                    swap = True
            elif sort_key == "creation_time":
                if datetime.strptime(tasks[j][sort_key], "%Y-%m-%d %H:%M:%S") > datetime.strptime(tasks[j + 1][sort_key], "%Y-%m-%d %H:%M:%S"):
                    tasks[j], tasks[j + 1] = tasks[j + 1], tasks[j]
                    swap = True

            # If there was a swap, the list might still not be sorted
            if swap:
                continue
    
    # Update the task list after sorting
    update_task_list(tree)

def display_filtered_results(filtered_tasks):
    result_window = tk.Toplevel()
    result_window.title("Filtered Tasks")

    tree = ttk.Treeview(result_window, columns=("Title", "Description", "Due Date", "Priority", "Status"), show="headings")
    tree.heading("Title", text="Title")
    tree.heading("Description", text="Description")
    tree.heading("Due Date", text="Due Date")
    tree.heading("Priority", text="Priority")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)

    for task in filtered_tasks:
        tree.insert("", "end", values=(task["title"], task["description"], task["due_date"], task["priority"], task["status"]))

def filter_tasks_window(root, tree):
    filter_window = tk.Toplevel(root)
    filter_window.title("Filter Tasks")

    # Priority filter
    tk.Label(filter_window, text="Priority:").grid(row=0, column=0, padx=10, pady=5)
    priority_combobox = ttk.Combobox(filter_window, values=["Low", "Medium", "High", "All"], state="readonly")
    priority_combobox.grid(row=0, column=1, padx=10, pady=5)
    priority_combobox.set("All")

    # Status filter
    tk.Label(filter_window, text="Status:").grid(row=1, column=0, padx=10, pady=5)
    status_combobox = ttk.Combobox(filter_window, values=["Pending", "Completed", "Overdue", "All"], state="readonly")
    status_combobox.grid(row=1, column=1, padx=10, pady=5)
    status_combobox.set("All")

    # Start Date filter
    tk.Label(filter_window, text="Start Date:").grid(row=2, column=0, padx=10, pady=5)
    start_date_cal = Calendar(filter_window, date_pattern="yyyy-mm-dd")
    start_date_cal.grid(row=2, column=1, padx=10, pady=5)

    # End Date filter
    tk.Label(filter_window, text="End Date:").grid(row=3, column=0, padx=10, pady=5)
    end_date_cal = Calendar(filter_window, date_pattern="yyyy-mm-dd")
    end_date_cal.grid(row=3, column=1, padx=10, pady=5)

    # Checkbox to ignore date filters
    ignore_dates_var = tk.BooleanVar()
    ignore_dates_checkbox = tk.Checkbutton(filter_window, text="Ignore Date Filters", variable=ignore_dates_var)
    ignore_dates_checkbox.grid(row=4, column=0, columnspan=2, pady=10)

    def apply_filter():
        filtered_tasks = tasks
        priority_filter = priority_combobox.get()
        if priority_filter != "All":
            filtered_tasks = [task for task in filtered_tasks if task["priority"] == priority_filter]

        status_filter = status_combobox.get()
        if status_filter != "All":
            filtered_tasks = [task for task in filtered_tasks if task["status"] == status_filter]

        if not ignore_dates_var.get():  # Only apply date filters if the checkbox is not checked
            start_date = start_date_cal.get_date()
            end_date = end_date_cal.get_date()

            if start_date:
                filtered_tasks = [task for task in filtered_tasks if task["due_date"] >= start_date]

            if end_date:
                filtered_tasks = [task for task in filtered_tasks if task["due_date"] <= end_date]

        display_filtered_results(filtered_tasks)

    apply_button = tk.Button(filter_window, text="Apply Filter", command=apply_filter)
    apply_button.grid(row=5, column=0, columnspan=2, pady=10)

def show_overdue_tasks(tree):
    global tasks

    # Filter overdue tasks that are not completed
    overdue_tasks = [
        task for task in tasks 
        if datetime.strptime(task["due_date"], "%Y-%m-%d") < datetime.now() and task["status"].lower() != "completed"
    ]

    if not overdue_tasks:
        messagebox.showinfo("No Overdue Tasks", "There are no overdue tasks.")
        return

    # Create a new window to display overdue tasks
    overdue_window = tk.Toplevel()
    overdue_window.title("Overdue Tasks")

    # Create a Treeview to display the overdue tasks
    overdue_tree = ttk.Treeview(overdue_window, columns=("Title", "Description", "Due Date", "Priority", "Status"), show="headings")
    overdue_tree.heading("Title", text="Title")
    overdue_tree.heading("Description", text="Description")
    overdue_tree.heading("Due Date", text="Due Date")
    overdue_tree.heading("Priority", text="Priority")
    overdue_tree.heading("Status", text="Status")
    overdue_tree.pack(fill=tk.BOTH, expand=True)

    # Insert overdue tasks into the Treeview
    for task in overdue_tasks:
        overdue_tree.insert("", "end", values=(task["title"], task["description"], task["due_date"], task["priority"], task["status"]))

    overdue_window.mainloop()

def main():
    global tasks
    load_tasks()

    root = tk.Tk()
    root.title("Task Manager")

    # Create a Style object to customize the Treeview
    style = ttk.Style(root)



    #  (first row)
    style.configure("Treeview.Heading",
    background="#001A6E",  
    foreground="#00008B",   
    font=("Arial", 12, "bold"))  
    # (content rows)
    style.configure("Treeview",
    background="#F0F0F0",
    foreground="#001A6E",  
    font=("Arial", 10))      

    # Set a color for the selected row
    style.map("Treeview",
              background=[('selected', '#4C75A3')])  # Color for selected row

    # Create the Treeview widget with columns
    tree = ttk.Treeview(root, columns=("Title", "Description", "Due Date", "Priority", "Status"), show="headings", style="Treeview")
    tree.heading("Title", text="Title")
    tree.heading("Description", text="Description")
    tree.heading("Due Date", text="Due Date")
    tree.heading("Priority", text="Priority")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)

    update_task_list(tree)

    # Frame to group the buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    button_style = {
        "bg": "#001A6E",  
        "fg": "#F8FAFC",  
        "font": ("Arial", 12)
    }

    tk.Button(button_frame, text="Add Task", command=lambda: add_task_gui(root, tree), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Update Task", command=lambda: update_task_gui(root, tree), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Delete Task", command=lambda: delete_task_gui(tree), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="sort by creation time", command=lambda: sort_tasks(tree, "priority"), **button_style).pack(side=tk.LEFT, padx=10)

    # Frame to group the Sort and Filter buttons in the same row
    sort_filter_frame = tk.Frame(root)
    sort_filter_frame.pack(pady=10)

    tk.Button(sort_filter_frame, text="Sort by Priority", command=lambda: sort_tasks(tree, "priority"), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(sort_filter_frame, text="Sort by Due Date", command=lambda: sort_tasks(tree, "due_date"), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(sort_filter_frame, text="Sort by Status", command=lambda: sort_tasks(tree, "status"), **button_style).pack(side=tk.LEFT, padx=10)
    tk.Button(sort_filter_frame, text="Filter Tasks", command=lambda: filter_tasks_window(root, tree), **button_style).pack(side=tk.LEFT, padx=10)

    show_overdue_tasks(None) 
    root.mainloop()

if __name__ == "__main__":
    main()
