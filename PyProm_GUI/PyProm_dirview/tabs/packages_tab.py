import importlib.metadata
import os
import tkinter as tk
import tkinter.ttk as ttk

from PyProm_templates import tab_template


class PackagesTab(tab_template.TabTemplate):
    NAME = "Packages"

    def __init__(self, master=None, main=None):
        self.main = main
        super().__init__(master)
        self.packages_tree = ttk.Treeview(
            self, show="headings", columns=("Packages", "Version"))
        self.packages_tree.heading(
            "Packages", text="Packages", anchor=tk.CENTER)
        self.packages_tree.heading(
            "Version", text="Version", anchor=tk.CENTER)
        self.packages_tree.pack(fill=tk.BOTH, expand=True)

    def refresh(self):
        """this func gets python packages in environment.
        """
        if os.path.isdir(self.main.dir_path):
            site_packages_dir = os.path.join(
                self.main.dir_path, ".venv", "Lib", "site-packages")
            if os.path.isdir(site_packages_dir):
                packages = []
                for dist in importlib.metadata.distributions(
                        path=[site_packages_dir]):
                    packages.append((dist.name, dist.version))
                for package in packages:
                    self.packages_tree.insert("", tk.END, values=package)
