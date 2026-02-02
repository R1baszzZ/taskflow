import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable

from taskflow import db


class TaskFlowApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TaskFlow")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Map combobox labels to user IDs. Keeps UI friendly while storing IDs internally.
        self._assignee_filter_map: dict[str, int | None] = {"All": None}
        self._assignee_form_map: dict[str, int | None] = {"Unassigned": None}

        self._build_ui()
        self.refresh_users()
        self.refresh_tasks()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tasks_tab = ttk.Frame(notebook)
        self.users_tab = ttk.Frame(notebook)
        notebook.add(self.tasks_tab, text="Tasks")
        notebook.add(self.users_tab, text="Users")

        self._build_tasks_tab()
        self._build_users_tab()

    def _build_tasks_tab(self) -> None:
        filter_frame = ttk.Frame(self.tasks_tab)
        filter_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT)
        self.status_filter = ttk.Combobox(
            filter_frame,
            values=["All", "todo", "doing", "done"],
            state="readonly",
            width=10,
        )
        self.status_filter.current(0)
        self.status_filter.pack(side=tk.LEFT, padx=5)
        self.status_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())

        ttk.Label(filter_frame, text="Assignee:").pack(side=tk.LEFT, padx=(10, 0))
        self.assignee_filter = ttk.Combobox(filter_frame, values=["All"], state="readonly")
        self.assignee_filter.current(0)
        self.assignee_filter.pack(side=tk.LEFT, padx=5)
        self.assignee_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())

        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 0))
        self.search_entry = ttk.Entry(filter_frame, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="Apply", command=self.refresh_tasks).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Clear", command=self._clear_task_filters).pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self.tasks_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("title", "status", "assignee", "created")
        self.tasks_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tasks_tree.heading("title", text="Title")
        self.tasks_tree.heading("status", text="Status")
        self.tasks_tree.heading("assignee", text="Assignee")
        self.tasks_tree.heading("created", text="Created At")
        self.tasks_tree.column("title", width=320)
        self.tasks_tree.column("status", width=90)
        self.tasks_tree.column("assignee", width=150)
        self.tasks_tree.column("created", width=160)
        self.tasks_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tasks_tree.bind("<<TreeviewSelect>>", lambda _e: self._update_task_buttons())

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.tasks_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Button(button_frame, text="Add Task", command=self.add_task).pack(side=tk.LEFT)
        self.edit_task_btn = ttk.Button(button_frame, text="Edit Task", command=self.edit_task, state=tk.DISABLED)
        self.edit_task_btn.pack(side=tk.LEFT, padx=5)
        self.delete_task_btn = ttk.Button(button_frame, text="Delete Task", command=self.delete_task, state=tk.DISABLED)
        self.delete_task_btn.pack(side=tk.LEFT, padx=5)

        ttk.Separator(button_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.todo_btn = ttk.Button(button_frame, text="Mark Todo", command=lambda: self.set_status("todo"), state=tk.DISABLED)
        self.todo_btn.pack(side=tk.LEFT)
        self.doing_btn = ttk.Button(button_frame, text="Mark Doing", command=lambda: self.set_status("doing"), state=tk.DISABLED)
        self.doing_btn.pack(side=tk.LEFT, padx=5)
        self.done_btn = ttk.Button(button_frame, text="Mark Done", command=lambda: self.set_status("done"), state=tk.DISABLED)
        self.done_btn.pack(side=tk.LEFT)

    def _build_users_tab(self) -> None:
        tree_frame = ttk.Frame(self.users_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.users_tree = ttk.Treeview(tree_frame, columns=("name",), show="headings", selectmode="browse")
        self.users_tree.heading("name", text="Name")
        self.users_tree.column("name", width=300)
        self.users_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.users_tree.bind("<<TreeviewSelect>>", lambda _e: self._update_user_buttons())

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.users_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.users_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Button(button_frame, text="Add User", command=self.add_user).pack(side=tk.LEFT)
        self.delete_user_btn = ttk.Button(button_frame, text="Delete User", command=self.delete_user, state=tk.DISABLED)
        self.delete_user_btn.pack(side=tk.LEFT, padx=5)

    def _clear_task_filters(self) -> None:
        # Reset filters to defaults and refresh the list.
        self.status_filter.current(0)
        self.assignee_filter.current(0)
        self.search_entry.delete(0, tk.END)
        self.refresh_tasks()

    def _update_task_buttons(self) -> None:
        has_selection = bool(self.tasks_tree.selection())
        state = tk.NORMAL if has_selection else tk.DISABLED
        self.edit_task_btn.config(state=state)
        self.delete_task_btn.config(state=state)
        self.todo_btn.config(state=state)
        self.doing_btn.config(state=state)
        self.done_btn.config(state=state)

    def _update_user_buttons(self) -> None:
        has_selection = bool(self.users_tree.selection())
        self.delete_user_btn.config(state=(tk.NORMAL if has_selection else tk.DISABLED))

    def refresh_users(self) -> None:
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        users = db.list_users()
        for user_id, name in users:
            # Store user_id as the item iid so we can fetch it later without showing it.
            self.users_tree.insert("", tk.END, iid=str(user_id), values=(name,))

        self._assignee_filter_map = {"All": None}
        self._assignee_form_map = {"Unassigned": None}
        for user_id, name in users:
            label = f"{name} (#{user_id})"
            self._assignee_filter_map[label] = user_id
            self._assignee_form_map[label] = user_id

        self.assignee_filter["values"] = list(self._assignee_filter_map.keys())
        if self.assignee_filter.get() not in self._assignee_filter_map:
            self.assignee_filter.current(0)

    def refresh_tasks(self) -> None:
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        status = self.status_filter.get()
        status_value = None if status == "All" else status

        assignee_label = self.assignee_filter.get()
        assignee_id = self._assignee_filter_map.get(assignee_label)

        query = self.search_entry.get().strip() or None

        try:
            tasks = db.list_tasks(status=status_value, assignee_id=assignee_id, title_query=query)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        for task_id, title, status, assignee_name, created_at in tasks:
            # Keep task_id internally as iid, but only show friendly columns.
            assignee_display = assignee_name or ""
            self.tasks_tree.insert(
                "",
                tk.END,
                iid=str(task_id),
                values=(title, status, assignee_display, created_at),
            )

        self._update_task_buttons()

    def _get_selected_task_id(self) -> int | None:
        selection = self.tasks_tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _get_selected_user_id(self) -> int | None:
        selection = self.users_tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def add_user(self) -> None:
        name = simpledialog.askstring("Add User", "Name:", parent=self)
        if not name:
            return
        try:
            db.add_user(name)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.refresh_users()
        self.refresh_tasks()

    def delete_user(self) -> None:
        user_id = self._get_selected_user_id()
        if user_id is None:
            return
        # We warn because tasks will be unassigned by FK rule.
        confirm = messagebox.askyesno(
            "Delete User",
            "Deleting a user will unassign their tasks. Continue?",
            parent=self,
        )
        if not confirm:
            return
        deleted = db.delete_user(user_id)
        if not deleted:
            messagebox.showerror("Error", "User not found.")
            return
        self.refresh_users()
        self.refresh_tasks()

    def add_task(self) -> None:
        dialog = TaskDialog(self, "Add Task", self._assignee_form_map)
        if not dialog.result:
            return
        title, description, assignee_id = dialog.result
        try:
            db.add_task(title, description, assignee_id)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.refresh_tasks()

    def edit_task(self) -> None:
        task_id = self._get_selected_task_id()
        if task_id is None:
            return
        task = db.get_task(task_id)
        if not task:
            messagebox.showerror("Error", "Task not found.")
            return
        _, title, description, _status, assignee_id, _created_at, _updated_at = task
        dialog = TaskDialog(
            self,
            "Edit Task",
            self._assignee_form_map,
            title_text=title,
            description=description,
            assignee_id=assignee_id,
        )
        if not dialog.result:
            return
        new_title, new_description, new_assignee_id = dialog.result
        try:
            updated = db.update_task(task_id, new_title, new_description, new_assignee_id)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        if not updated:
            messagebox.showerror("Error", "Task not found.")
            return
        self.refresh_tasks()

    def delete_task(self) -> None:
        task_id = self._get_selected_task_id()
        if task_id is None:
            return
        confirm = messagebox.askyesno("Delete Task", "Delete the selected task?", parent=self)
        if not confirm:
            return
        deleted = db.delete_task(task_id)
        if not deleted:
            messagebox.showerror("Error", "Task not found.")
            return
        self.refresh_tasks()

    def set_status(self, status: str) -> None:
        task_id = self._get_selected_task_id()
        if task_id is None:
            return
        if status == "done":
            confirm = messagebox.askyesno("Mark Done", "Mark this task as done?", parent=self)
            if not confirm:
                return
        try:
            updated = db.update_task_status(task_id, status)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        if not updated:
            messagebox.showerror("Error", "Task not found.")
            return
        self.refresh_tasks()


class TaskDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        title: str,
        assignee_map: dict[str, int | None],
        title_text: str | None = None,
        description: str | None = None,
        assignee_id: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.result: tuple[str, str | None, int | None] | None = None
        self.assignee_map = assignee_map
        self.resizable(False, False)

        ttk.Label(self, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=8)
        self.title_entry = ttk.Entry(self, width=40)
        self.title_entry.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(self, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=10)
        self.description_text = tk.Text(self, width=40, height=5)
        self.description_text.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self, text="Assignee:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=8)
        self.assignee_combo = ttk.Combobox(self, values=list(self.assignee_map.keys()), state="readonly", width=37)
        self.assignee_combo.grid(row=2, column=1, padx=10, pady=8)
        self.assignee_combo.current(0)

        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT)

        if title_text:
            self.title_entry.insert(0, title_text)
        if description:
            self.description_text.insert("1.0", description)
        if assignee_id is not None:
            for label, value in self.assignee_map.items():
                if value == assignee_id:
                    self.assignee_combo.set(label)
                    break

        self.title_entry.focus()
        self.grab_set()
        self.wait_window(self)

    def _save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Title is required.", parent=self)
            return

        description = self.description_text.get("1.0", tk.END).strip()
        if description == "":
            description = None

        assignee_label = self.assignee_combo.get()
        assignee_id = self.assignee_map.get(assignee_label)

        self.result = (title, description, assignee_id)
        self.destroy()

    def _cancel(self) -> None:
        self.destroy()


def main() -> None:
    app = TaskFlowApp()
    app.mainloop()
