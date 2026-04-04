"""
Nexus Management UI Module.

Provides the NexusManagementUI class for managing network device
documentation through remote access and SCCD CI configuration updates.
Supports manual device entry and Excel import.
"""

import tkinter
from tkinter import ttk, filedialog, messagebox
import shutil
from threading import Thread

from core import SCCD_CI_CONF as SCCD_CI
from core import nexus_remote_access

from .components import error_window, load_excel


DEVICE_OPTIONS = ("cisco", "fortinet", "juniper")
OWNER_OPTIONS = ("CW", "CUSTOMER")
MANAGED_BY_OPTIONS = ("CW", "Customer")


class DeviceTableFrame(ttk.Frame):
    """
    Reusable frame for managing a dynamic list of network devices.

    Provides manual row-by-row entry and bulk Excel import for device data
    including IP, device platform, dealcode, device_owner, and managed_by.

    Args:
        master: Parent Tkinter widget.
    """

    COLUMNS = ("IP", "Device", "Dealcode", "Owner", "Managed By")
    COL_WIDTHS = (18, 10, 10, 12, 12)

    def __init__(self, master, geo_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.geo_callback = geo_callback
        self.window_weight = 565
        self.window_height = 480
        self._set_window_size(self.window_weight, self.window_height)

        self._rows = []
        self._global_dealcode = tkinter.StringVar()
        self._use_global_dealcode = tkinter.BooleanVar(value=False)
        self._build()

    def _set_window_size(self, width, height):
        """Set the window size using the provided geometry callback."""
        self.window_weight = width
        self.window_height = height
        if self.geo_callback:
            self.geo_callback(f"{self.window_weight}x{self.window_height}")

    def _build(self):
        """Build the device table layout."""
        # Global dealcode option
        dc_frame = ttk.Frame(self)
        dc_frame.pack(fill="x", pady=(0, 8))

        self._chk_global_dc = ttk.Checkbutton(
            dc_frame,
            text="Same dealcode for all",
            variable=self._use_global_dealcode,
            command=self._toggle_global_dealcode,
        )
        self._chk_global_dc.pack(side="left")

        self._ent_global_dc = ttk.Entry(
            dc_frame, textvariable=self._global_dealcode, width=12, state="disabled"
        )
        self._ent_global_dc.pack(side="left", padx=(5, 0))

        # Column headers
        hdr = ttk.Frame(self)
        hdr.pack(fill="x")
        for i, (text, w) in enumerate(zip(self.COLUMNS, self.COL_WIDTHS)):
            ttk.Label(
                hdr, text=text, width=w, anchor="center",
                font=("Helvetica", 9, "bold"),
            ).grid(row=0, column=i, padx=2)

        # Rows container
        self._rows_frame = ttk.Frame(self)
        self._rows_frame.pack(fill="both", expand=True)

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="+ Add Row", command=self.add_row).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Remove Last", command=self.remove_last_row).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Load Excel", command=self._load_from_excel).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Get Template", command=self._get_template).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=2)

        # Start with one empty row
        self.add_row()

    def _toggle_global_dealcode(self):
        """Enable or disable individual dealcode entries based on the global toggle."""
        if self._use_global_dealcode.get():
            self._ent_global_dc.config(state="normal")
            for row in self._rows:
                row["dealcode_widget"].config(state="disabled")
        else:
            self._ent_global_dc.config(state="disabled")
            for row in self._rows:
                row["dealcode_widget"].config(state="normal")

    def add_row(self, ip="", device="cisco", dealcode="", owner="CW", managed="CW"):
        """
        Append a new device row to the table.

        Args:
            ip: Default IP address value.
            device: Default device platform.
            dealcode: Default dealcode value.
            owner: Default device_owner value.
            managed: Default managed_by value.
        """
        frame = ttk.Frame(self._rows_frame)
        frame.pack(fill="x", pady=1)

        ip_var = tkinter.StringVar(value=ip)
        device_var = tkinter.StringVar(value=device)
        dealcode_var = tkinter.StringVar(value=dealcode)
        owner_var = tkinter.StringVar(value=owner)
        managed_var = tkinter.StringVar(value=managed)

        ttk.Entry(frame, textvariable=ip_var, width=18).grid(row=0, column=0, padx=2)
        ttk.Combobox(
            frame, textvariable=device_var, values=DEVICE_OPTIONS,
            state="readonly", width=8,
        ).grid(row=0, column=1, padx=2)

        dc_ent = ttk.Entry(frame, textvariable=dealcode_var, width=10)
        dc_ent.grid(row=0, column=2, padx=2)
        if self._use_global_dealcode.get():
            dc_ent.config(state="disabled")

        ttk.Combobox(
            frame, textvariable=owner_var, values=OWNER_OPTIONS,
            state="readonly", width=10,
        ).grid(row=0, column=3, padx=2)
        ttk.Combobox(
            frame, textvariable=managed_var, values=MANAGED_BY_OPTIONS,
            state="readonly", width=10,
        ).grid(row=0, column=4, padx=2)

        self._rows.append({
            "frame": frame,
            "ip": ip_var,
            "device": device_var,
            "dealcode": dealcode_var,
            "dealcode_widget": dc_ent,
            "device_owner": owner_var,
            "managed_by": managed_var,
        })
        if 480 <= self.window_height < 720:
            self._set_window_size(self.window_weight, self.window_height + 30)


    def remove_last_row(self):
        """Remove the last device row from the table."""
        if self._rows:
            self._rows.pop()["frame"].destroy()
        if 480 < self.window_height <= 720:
            self._set_window_size(self.window_weight, self.window_height - 30)

    def clear_all(self):
        """Remove all device rows from the table."""
        for row in self._rows:
            row["frame"].destroy()
        self._set_window_size(self.window_weight, 480)
        self._rows.clear()
        

    def _load_from_excel(self):
        """Load device data from an Excel file.

        Expected columns: ip, device, dealcode, device_owner, managed_by.
        """
        data = load_excel()
        if not data:
            return

        required = {"ip", "device"}
        if not required.issubset(data[0].keys()):
            error_window("Excel must contain at least columns: ip, device")
            return

        self.clear_all()
        for record in data:
            device_val = str(record.get("device", "cisco")).lower().strip()
            if device_val not in DEVICE_OPTIONS:
                device_val = "cisco"

            owner_val = str(record.get("device_owner", "CW")).strip().upper()
            if owner_val not in OWNER_OPTIONS:
                owner_val = "CW"

            managed_val = str(record.get("managed_by", "CW")).strip()
            if managed_val not in MANAGED_BY_OPTIONS:
                managed_val = "CW"

            self.add_row(
                ip=str(record.get("ip", "")).strip(),
                device=device_val,
                dealcode=str(record.get("dealcode", "")).strip(),
                owner=owner_val,
                managed=managed_val,
            )

    def _get_template(self):
        """Provide an Excel template for device data entry."""
        template_path = "resources/devices_info.xlsx"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Device Template As",
        )
        if save_path:
            try:
                shutil.copy(template_path, save_path)
                messagebox.showinfo("Template Saved", f"Template saved to {save_path}")
            except Exception as e:
                error_window(f"Error saving template: {e}")

    def get_devices(self) -> list:
        """
        Collect all device entries that have a non-empty IP.

        Returns:
            list: List of dicts with keys ip, device, dealcode,
                  device_owner, managed_by.
        """
        global_dc = self._global_dealcode.get().strip()
        devices = []
        for row in self._rows:
            ip = row["ip"].get().strip()
            if not ip:
                continue
            dealcode = global_dc if self._use_global_dealcode.get() else row["dealcode"].get().strip()
            devices.append({
                "ip": ip,
                "device": row["device"].get(),
                "dealcode": dealcode,
                "device_owner": row["device_owner"].get(),
                "managed_by": row["managed_by"].get(),
            })
        return devices


class NexusManagementUI:
    """
    Nexus Management graphical interface.

    Provides a UI for executing remote access tasks on network devices
    and documenting the results in SCCD. Designed for extensibility
    with new tasks via the TASK_OPTIONS mapping.

    Args:
        root_window: Parent Tkinter widget where UI will be rendered.
        env: Environment handler providing credential access methods.
    """

    TASK_OPTIONS = {
        "Basic Info Documentation": "basic_info",
    }

    def __init__(self, root_window, env, geo_callback=None):
        self.root_window = root_window
        self.env = env
        self.geo_callback = geo_callback
        #self.geo_callback("450x480")
        self._status = tkinter.StringVar(value="Ready")
        self._credential_type = tkinter.StringVar(value="radius")
        self._selected_task = tkinter.StringVar(value="Basic Info Documentation")
        self._draw()



    def _draw(self):
        """Draw the complete Nexus Management interface."""
        main = ttk.Frame(self.root_window)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        row = 0

        # Title
        ttk.Label(
            main, text="NEXUS MANAGEMENT 🌐",
            anchor="center", font=("Helvetica", 18, "bold"),
        ).grid(row=row, column=0, columnspan=2, pady=(0, 10))
        row += 1

        # Credential selection
        cred_frame = ttk.LabelFrame(main, text="Credentials", padding=5)
        cred_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Radiobutton(
            cred_frame, text="Radius",
            variable=self._credential_type, value="radius",
        ).pack(side="left", padx=10)
        ttk.Radiobutton(
            cred_frame, text="Temporal",
            variable=self._credential_type, value="temporal",
        ).pack(side="left", padx=10)
        row += 1

        # Task selection
        task_frame = ttk.LabelFrame(main, text="Task", padding=5)
        task_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Combobox(
            task_frame,
            textvariable=self._selected_task,
            values=list(self.TASK_OPTIONS.keys()),
            state="readonly", width=30,
        ).pack(side="left", padx=5)
        row += 1

        # Device table
        dev_frame = ttk.LabelFrame(main, text="Devices", padding=5)
        dev_frame.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=5)
        self._device_table = DeviceTableFrame(dev_frame, geo_callback=self.geo_callback)
        self._device_table.pack(fill="both", expand=True)
        row += 1

        # Execute button
        self._btn_execute = ttk.Button(main, text="Execute", command=self._execute)
        self._btn_execute.grid(row=row, column=0, columnspan=2, pady=10)
        row += 1

        # Status label
        ttk.Label(main, textvariable=self._status).grid(
            row=row, column=0, columnspan=2,
        )

    def _get_credentials(self):
        """
        Get username and password based on selected credential type.

        Returns:
            tuple: (username, password)
        """
        if self._credential_type.get() == "radius":
            return self.env.get_radius_user(), self.env.get_radius_pass()
        return self.env.get_temporal_user(), self.env.get_temporal_pass()

    def _execute(self):
        """Validate inputs and launch the selected task in a background thread."""
        devices = self._device_table.get_devices()
        if not devices:
            error_window("No devices entered. Add at least one device with an IP address.")
            return

        task_key = self.TASK_OPTIONS.get(self._selected_task.get())
        if not task_key:
            error_window("Please select a task.")
            return

        for d in devices:
            if not d["dealcode"]:
                error_window(f"Dealcode is required for device {d['ip']}.")
                return

        self._btn_execute.config(state="disabled")
        self._status.set("Working...")

        thread = Thread(
            target=self._run_task, args=(task_key, devices), daemon=True,
        )
        thread.start()

    def _run_task(self, task_key, devices):
        """
        Execute the selected task in a background thread.

        Args:
            task_key: Task identifier for nexus_remote_access.
            devices: List of device dicts from the device table.
        """
        try:
            username, password = self._get_credentials()
        except Exception as e:
            self._ui(lambda: error_window(f"Credential error: {e}"))
            self._finish("Credential error")
            return

        try:
            # Build remote access input
            device_tuples = tuple((d["ip"], d["device"]) for d in devices)
            remote_input = {
                "username": username,
                "password": password,
                "task": task_key,
                "devices": device_tuples,
            }

            self._ui(lambda: self._status.set("Connecting to devices..."))
            results = nexus_remote_access(remote_input)
            self._ui(lambda: self._status.set("Data retrieved, processing..."))
            

            if not results:
                self._ui(lambda: error_window("No results returned from remote access."))
                self._finish("No results")
                return

            # Merge remote results with user-provided fields (matched by order)
            ci_updates = []
            for i, result in enumerate(results):
                user_entry = devices[i] if i < len(devices) else {}
                ci_updates.append({
                    "cid": result.get("cid", ""),
                    "vendor": result.get("vendor", ""),
                    "model": result.get("model", ""),
                    "device_owner": user_entry.get("device_owner", "CW"),
                    "sn": result.get("sn", ""),
                    "dcn": result.get("dcn", ""),
                    "hostname": result.get("hostname", ""),
                    "cids_related": result.get("cids_related", ""),
                    "channels": result.get("channels", ""),
                    "dealcode": user_entry.get("dealcode", ""),
                    "managed_by": user_entry.get("managed_by", "CW"),
                    "device": result.get("device", ""),
                })

            # Update SCCD CIs
            self._ui(lambda: self._status.set("Updating SCCD..."))
            sccd_ci = SCCD_CI(self.env.get_user_sccd(), self.env.get_pass_sccd())
            sccd_ci.update_multiple_sw_rt_ci(ci_updates)

            self._finish("Completed successfully")

        except Exception as e:
            self._ui(lambda: error_window(f"Execution error: {e}"))
            self._finish("Error")

    def _ui(self, callback):
        """Schedule a callback on the main Tkinter thread."""
        self.root_window.after(0, callback)

    def _finish(self, status_text):
        """Reset the execute button and update status from any thread."""
        self._ui(lambda: self._btn_execute.config(state="normal"))
        self._ui(lambda: self._status.set(status_text))
