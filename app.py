import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


def run_adb(args, device_id=None):
    cmd = ["adb"]
    if device_id:
        cmd += ["-s", device_id]
    cmd += args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ADB command failed")
    return result.stdout.strip()


class AndroidAppController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Android App Controller (ADB)")
        self.geometry("900x600")
        self.resizable(True, True)

        self.device_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.package_filter_var = tk.StringVar()

        self._build_ui()
        self.refresh_devices()

    def _build_ui(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=12, pady=8)

        ttk.Label(top_frame, text="Device:").pack(side=tk.LEFT)
        self.device_combo = ttk.Combobox(top_frame, textvariable=self.device_var, state="readonly")
        self.device_combo.pack(side=tk.LEFT, padx=8)

        ttk.Button(top_frame, text="Refresh Devices", command=self.refresh_devices).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Refresh Apps", command=self.refresh_packages).pack(side=tk.LEFT, padx=8)

        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=12, pady=4)
        ttk.Label(filter_frame, text="Filter packages:").pack(side=tk.LEFT)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.package_filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        filter_entry.bind("<KeyRelease>", lambda _event: self.apply_filter())

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.package_list = tk.Listbox(main_frame)
        self.package_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.package_list.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.package_list.configure(yscrollcommand=scrollbar.set)

        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=12)

        ttk.Button(actions_frame, text="Launch App", command=self.launch_app).pack(fill=tk.X, pady=4)
        ttk.Button(actions_frame, text="Force Stop", command=self.force_stop_app).pack(fill=tk.X, pady=4)
        ttk.Button(actions_frame, text="Uninstall", command=self.uninstall_app).pack(fill=tk.X, pady=4)
        ttk.Button(actions_frame, text="Install APK", command=self.install_apk).pack(fill=tk.X, pady=4)
        ttk.Button(actions_frame, text="Copy Package Name", command=self.copy_package).pack(fill=tk.X, pady=4)

        status_bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=12, pady=6)

    def set_status(self, message):
        self.status_var.set(message)

    def refresh_devices(self):
        try:
            output = run_adb(["devices"])
        except Exception as exc:
            messagebox.showerror("ADB Error", str(exc))
            return

        device_ids = []
        for line in output.splitlines():
            if "\tdevice" in line:
                device_ids.append(line.split("\t")[0])

        self.device_combo["values"] = device_ids
        if device_ids:
            self.device_var.set(device_ids[0])
            self.set_status(f"Found {len(device_ids)} device(s)")
            self.refresh_packages()
        else:
            self.device_var.set("")
            self.package_list.delete(0, tk.END)
            self.set_status("No devices detected")

    def refresh_packages(self):
        device_id = self.device_var.get()
        if not device_id:
            self.set_status("Select a device first")
            return

        try:
            output = run_adb(["shell", "pm", "list", "packages"], device_id)
        except Exception as exc:
            messagebox.showerror("ADB Error", str(exc))
            return

        packages = [line.replace("package:", "") for line in output.splitlines() if line.startswith("package:")]
        packages.sort()
        self.all_packages = packages
        self.apply_filter()
        self.set_status(f"Loaded {len(packages)} packages")

    def apply_filter(self):
        if not hasattr(self, "all_packages"):
            return
        term = self.package_filter_var.get().lower()
        filtered = [pkg for pkg in self.all_packages if term in pkg.lower()]
        self.package_list.delete(0, tk.END)
        for pkg in filtered:
            self.package_list.insert(tk.END, pkg)

    def get_selected_package(self):
        selection = self.package_list.curselection()
        if not selection:
            messagebox.showwarning("Selection", "Select a package first")
            return None
        return self.package_list.get(selection[0])

    def launch_app(self):
        package = self.get_selected_package()
        if not package:
            return
        device_id = self.device_var.get()
        try:
            run_adb(["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"], device_id)
            self.set_status(f"Launched {package}")
        except Exception as exc:
            messagebox.showerror("ADB Error", str(exc))

    def force_stop_app(self):
        package = self.get_selected_package()
        if not package:
            return
        device_id = self.device_var.get()
        try:
            run_adb(["shell", "am", "force-stop", package], device_id)
            self.set_status(f"Stopped {package}")
        except Exception as exc:
            messagebox.showerror("ADB Error", str(exc))

    def uninstall_app(self):
        package = self.get_selected_package()
        if not package:
            return
        if not messagebox.askyesno("Confirm", f"Uninstall {package}?"):
            return
        device_id = self.device_var.get()
        try:
            run_adb(["uninstall", package], device_id)
            self.set_status(f"Uninstalled {package}")
            self.refresh_packages()
        except Exception as exc:
            messagebox.showerror("ADB Error", str(exc))

    def install_apk(self):
        apk_path = filedialog.askopenfilename(filetypes=[("APK files", "*.apk")])
        if not apk_path:
            return
        device_id = self.device_var.get()
        if not device_id:
            self.set_status("Select a device first")
            return
        try:
            run_adb(["install", "-r", apk_path], device_id)
            self.set_status(f"Installed {apk_path}")
            self.refresh_packages()
        except Exception as exc:
            messagebox.showerror("ADB Error", str(exc))

    def copy_package(self):
        package = self.get_selected_package()
        if not package:
            return
        self.clipboard_clear()
        self.clipboard_append(package)
        self.set_status(f"Copied {package}")


if __name__ == "__main__":
    app = AndroidAppController()
    app.mainloop()
