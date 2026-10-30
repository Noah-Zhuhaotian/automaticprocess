"""Step: General - job number, client (a MinuteDock Contact), street,
suburb, town. The info every Create mode needs, whether it's making
folders, documents, or both.

Client info is picked from the MinuteDock account's existing Contacts (one
client typically owns many projects), or added as a new name - a new one is
created in MinuteDock at Create time by web_filler.sync_to_minutedock's
find-or-create, not here. Scope and Role have their own Scope step, since
only the Word documents use them.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app.core import folder_creator, minutedock_client
from app.core.minutedock_client import MinuteDockError


class GeneralStepMixin:
    def _init_general_vars(self) -> None:
        self.job_number_var = tk.StringVar()
        # Still named client_info_var (and still fills the Word templates'
        # {{client_info}} token) - it now holds the MinuteDock Contact name.
        self.client_info_var = tk.StringVar()
        self.street_var = tk.StringVar()
        self.suburb_var = tk.StringVar()
        self.town_var = tk.StringVar()

        self.availability_var = tk.StringVar()
        self.contact_status_var = tk.StringVar()

        # Names of the account's active Contacts, fetched once and cached for
        # the session (Refresh re-fetches). None = not loaded yet / failed.
        self._minutedock_contact_names: list[str] | None = None
        # Names typed in via "Add new contact..." - not in MinuteDock yet.
        self._new_contact_names: list[str] = []
        self._contact_combobox: ttk.Combobox | None = None
        self._contact_status_label: ttk.Label | None = None

    # ---------- Step: General ----------
    def _build_general_step(self, parent: ttk.Frame) -> None:
        # In "documents_only" mode (see mode_step.py), Job number/Street were
        # already derived from the existing folder the user picked - locked
        # read-only here so they can't drift out of sync with that folder.
        locked = self.create_mode_var.get() == "documents_only"
        # ...and if that job's MinuteDock Project was found, its Contact is
        # fixed too: the folder already belongs to that client.
        contact_locked = locked and self.existing_minutedock_project is not None

        ttk.Label(parent, text="Job number:").grid(row=0, column=0, sticky="w", pady=4)
        self.job_number_entry = ttk.Entry(parent, textvariable=self.job_number_var, width=40)
        self.job_number_entry.grid(row=0, column=1, sticky="w", pady=4, padx=8)
        self.job_number_entry.bind("<FocusOut>", lambda event: self._update_availability_status())
        if locked:
            self.job_number_entry.configure(state="readonly")

        ttk.Label(parent, text="Client info:").grid(row=1, column=0, sticky="w", pady=4)
        contact_row = ttk.Frame(parent)
        contact_row.grid(row=1, column=1, columnspan=2, sticky="w", pady=4, padx=8)
        self._contact_combobox = ttk.Combobox(contact_row, textvariable=self.client_info_var, width=37)
        self._contact_combobox.grid(row=0, column=0, sticky="w")
        add_button = ttk.Button(contact_row, text="Add new contact...", command=self._add_new_contact)
        add_button.grid(row=0, column=1, padx=(8, 0))
        refresh_button = ttk.Button(
            contact_row, text="Refresh", command=lambda: self._load_minutedock_contacts(force=True)
        )
        refresh_button.grid(row=0, column=2, padx=(8, 0))
        if contact_locked:
            add_button.configure(state="disabled")
            refresh_button.configure(state="disabled")

        self._contact_status_label = ttk.Label(
            parent, textvariable=self.contact_status_var, wraplength=560, justify="left"
        )
        self._contact_status_label.grid(row=2, column=1, columnspan=2, sticky="w", padx=8)

        ttk.Label(parent, text="Street:").grid(row=3, column=0, sticky="w", pady=4)
        self.street_entry = ttk.Entry(parent, textvariable=self.street_var, width=40)
        self.street_entry.grid(row=3, column=1, sticky="w", pady=4, padx=8)
        self.street_entry.bind("<FocusOut>", lambda event: self._update_availability_status())
        if locked:
            self.street_entry.configure(state="readonly")

        ttk.Label(parent, text="Suburb:").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=self.suburb_var, width=40).grid(row=4, column=1, sticky="w", pady=4, padx=8)

        ttk.Label(parent, text="Town:").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=self.town_var, width=40).grid(row=5, column=1, sticky="w", pady=4, padx=8)

        self.availability_label = ttk.Label(parent, textvariable=self.availability_var, wraplength=560, justify="left")
        self.availability_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 8))
        self._update_availability_status()

        if contact_locked:
            self._contact_combobox.configure(values=[self.client_info_var.get()], state="disabled")
            self._set_contact_status("Client is fixed by this job's existing MinuteDock project.", "gray")
        else:
            self._load_minutedock_contacts(force=False)

    # ---------- MinuteDock Contact picker ----------
    def _set_contact_status(self, text: str, color: str) -> None:
        self.contact_status_var.set(text)
        if self._contact_status_label is not None and self._contact_status_label.winfo_exists():
            self._contact_status_label.configure(foreground=color)

    def _load_minutedock_contacts(self, force: bool) -> None:
        """Fill the Client info dropdown from MinuteDock. Cached after the
        first successful load (Refresh passes force=True). On failure, the
        box becomes free-text so work isn't blocked by a network hiccup -
        Create's find-or-create still matches or creates the typed name."""
        if force or self._minutedock_contact_names is None:
            token = self.settings.get("minutedock_access_token", "").strip()
            self.config(cursor="watch")
            self.update_idletasks()
            try:
                contacts = minutedock_client.list_contacts(token)
                self._minutedock_contact_names = sorted(
                    {str(c.get("name", "")).strip() for c in contacts if str(c.get("name", "")).strip()},
                    key=str.casefold,
                )
            except MinuteDockError as exc:
                self._minutedock_contact_names = None
                self._apply_contact_values(editable=True)
                self._set_contact_status(
                    f"Couldn't load MinuteDock contacts - type the client name instead.\n{exc}", "red"
                )
                return
            finally:
                self.config(cursor="")

        self._apply_contact_values(editable=False)
        count = len(self._minutedock_contact_names or [])
        self._set_contact_status(
            f"{count} existing MinuteDock contact(s). Not listed? Use \"Add new contact...\".", "gray"
        )

    def _apply_contact_values(self, editable: bool) -> None:
        combo = self._contact_combobox
        if combo is None or not combo.winfo_exists():
            return
        names = list(self._minutedock_contact_names or [])
        for name in self._new_contact_names:
            if name.casefold() not in {n.casefold() for n in names}:
                names.append(f"{name}")
        combo.configure(values=names, state="normal" if editable else "readonly")

    def _add_new_contact(self) -> None:
        name = simpledialog.askstring("Add new contact", "Client name:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()

        existing = {n.casefold(): n for n in (self._minutedock_contact_names or [])}
        if name.casefold() in existing:
            # Already a MinuteDock contact - pick it instead of making a duplicate.
            self.client_info_var.set(existing[name.casefold()])
            self._set_contact_status(f'"{existing[name.casefold()]}" already exists in MinuteDock - selected it.', "gray")
            return

        if name.casefold() not in {n.casefold() for n in self._new_contact_names}:
            self._new_contact_names.append(name)
        self._apply_contact_values(editable=self._minutedock_contact_names is None)
        self.client_info_var.set(name)
        self._set_contact_status(f'"{name}" will be added to MinuteDock contacts when you click Create.', "green")

    # ---------- Job number availability ----------
    def _update_availability_status(self) -> None:
        # The label lives on the General step and gets destroyed whenever the
        # wizard navigates to a different step, so a stale reference here
        # would raise TclError - skip the update unless it's currently shown.
        if not hasattr(self, "availability_label") or not self.availability_label.winfo_exists():
            return

        job_number = self.job_number_var.get().strip()
        street = self.street_var.get().strip()
        if not job_number:
            self.availability_var.set("")
            return

        if self.create_mode_var.get() == "documents_only":
            # The folder is expected to already exist here - that's the
            # whole point of this mode, not a conflict to warn about.
            if street:
                project_name = folder_creator.build_project_folder_name(job_number, street)
                self.availability_label.configure(foreground="green")
                self.availability_var.set(f'Filling documents into: "{project_name}"')
            return

        # Folders only here - the MinuteDock half of the uniqueness check
        # needs the network, so it only runs on Next (_validate_general_step).
        conflicts = folder_creator.find_job_number_conflicts(
            job_number,
            self.settings.get("engineer_drive", ""),
            self.settings.get("drafting_drive", ""),
            self.settings.get("admin_drive", ""),
        )
        if conflicts:
            self.availability_label.configure(foreground="red")
            self.availability_var.set(
                f"Job number {job_number} is already used by:\n" + "\n".join(str(path) for path in conflicts)
            )
        elif street:
            project_name = folder_creator.build_project_folder_name(job_number, street)
            self.availability_label.configure(foreground="green")
            self.availability_var.set(f'Available: "{project_name}"')
        else:
            self.availability_var.set("")

    def _validate_general_step(self) -> bool:
        if not self.job_number_var.get().strip():
            messagebox.showerror("Missing info", "Job number is required.")
            return False
        if not self.client_info_var.get().strip():
            messagebox.showerror("Missing info", "Client info is required - pick a contact or add a new one.")
            return False
        if not self.street_var.get().strip():
            messagebox.showerror("Missing info", "Street is required.")
            return False
        if not self.suburb_var.get().strip():
            messagebox.showerror("Missing info", "Suburb is required.")
            return False
        if not self.town_var.get().strip():
            messagebox.showerror("Missing info", "Town is required.")
            return False

        if self.create_mode_var.get() != "documents_only":
            return self._check_job_number_unique(self.job_number_var.get().strip())
        return True

    def _check_job_number_unique(self, job_number: str) -> bool:
        """Job numbers are unique per job: blocked by any "{job} - ..."
        folder on any drive (whatever its street), or any MinuteDock Project
        already using it as its Short Code."""
        conflicts = folder_creator.find_job_number_conflicts(
            job_number,
            self.settings.get("engineer_drive", ""),
            self.settings.get("drafting_drive", ""),
            self.settings.get("admin_drive", ""),
        )
        if conflicts:
            messagebox.showerror(
                "Job number already used",
                f"Job number {job_number} is already used by:\n"
                + "\n".join(str(path) for path in conflicts)
                + "\n\nUse a different job number.",
            )
            return False

        token = self.settings.get("minutedock_access_token", "").strip()
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            project = minutedock_client.find_project_by_short_code(token, job_number)
        except MinuteDockError as exc:
            messagebox.showerror(
                "Can't check MinuteDock",
                "Couldn't check whether this job number is already used in MinuteDock, "
                f"so it can't be confirmed unique yet:\n{exc}\n\nCheck the connection and try again.",
            )
            return False
        finally:
            self.config(cursor="")

        if project is not None:
            messagebox.showerror(
                "Job number already used",
                f"Job number {job_number} is already the Short Code of MinuteDock project "
                f'"{project.get("name", "")}".\n\nUse a different job number.',
            )
            return False
        return True
