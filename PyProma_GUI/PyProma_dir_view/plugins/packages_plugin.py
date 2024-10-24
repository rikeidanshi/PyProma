import importlib.metadata
import os
import queue
import subprocess
import threading
import tkinter as tk
import tkinter.ttk as ttk
import urllib
import urllib.parse
import webbrowser

from PyProma_common.PyProma_templates import tab_template
from PyProma_dir_view.plugins.plugin_manager import RefreshMethod


class PackagesTab(tab_template.TabTemplate):
    NAME = "Packages"

    def __init__(self, master=None, main=None):
        super().__init__(master, main)
        self.tree_frame = tk.Frame(self, width=400, height=575)
        self.tree_frame.propagate(False)
        self.packages_tree = ttk.Treeview(
            self.tree_frame, show="headings", columns=("Packages", "Version"))
        self.packages_tree.heading(
            "Packages", text="Packages", anchor=tk.CENTER)
        self.packages_tree.heading(
            "Version", text="Version", anchor=tk.CENTER)
        self.packages_tree.pack(fill=tk.BOTH, expand=True)
        self.tree_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.install_frame = tk.Frame(self, width=400, height=575)
        self.install_frame.propagate(False)
        self.output_label = tk.Label(self.install_frame, text="Outputs")
        self.output_label.place(x=5, y=5)
        self.command_output = tk.Text(self.install_frame, width=55, height=20)
        self.command_output.place(x=0, y=30)
        values = ["pip install"]
        self.command_combo = ttk.Combobox(
            self.install_frame, values=values, state="readonly")
        self.command_combo.place(x=10, y=300)
        self.command_combo.current(0)
        self.command_text = tk.Entry(self.install_frame, width=30)
        self.command_text.place(x=155, y=301)
        self.command_text.bind("<Return>", self.install_package)
        self.run_command_button = tk.Button(
            self.install_frame, text="run", command=self.install_package)
        self.run_command_button.place(x=350, y=297)
        self.install_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self.search_label = tk.Label(self.install_frame, text="Search on PyPI")
        self.search_label.place(x=5, y=350)
        self.search_text = tk.Entry(self.install_frame, width=50)
        self.search_text.bind("<Return>", self.search_package)
        self.search_text.place(x=10, y=370)
        self.search_button = tk.Button(
            self.install_frame, text="search", command=self.search_package)
        self.search_button.place(x=320, y=364)

    @RefreshMethod
    def refresh(self):
        """this func gets python packages in environment.
        """
        if os.path.isdir(self.main.dir_path):
            self.packages_tree.delete(*self.packages_tree.get_children())
            site_packages_dir = os.path.join(
                self.main.dir_path, ".venv", "Lib", "site-packages")
            if os.path.isdir(site_packages_dir):
                packages = []
                for dist in importlib.metadata.distributions(
                        path=[site_packages_dir]):
                    packages.append((dist.name, dist.version))
                for package in packages:
                    self.packages_tree.insert("", tk.END, values=package)
                is_poetry_in = any(
                    package[0] == "poetry" for package in packages)
                if is_poetry_in:
                    self.command_combo["values"] = [
                        "poetry add", "pip install"]
                else:
                    self.command_combo["values"] = ["pip install"]
                self.command_combo.current(0)

    def install_package(self, _=None):
        if os.path.isdir(self.main.dir_path) and self.command_text.get():
            venv_path = os.path.join(
                self.main.dir_path, ".venv", "Scripts", "python.exe")
            if os.path.isfile(venv_path):
                tool = self.command_combo.get().split(" ")
                package = self.command_text.get()
                if package:
                    self.run_command([venv_path, "-m", *tool, package])

    def run_command(self, command: str | list):
        """This func runs command and displays outputs to command_output.

        Args:
            command (str | list): Command what you want to run.
        """

        def _run_command():
            _output_queue.put(" ".join(command)+"\n")
            try:
                self.run_command_button.config(state=tk.DISABLED)
                self.command_text.unbind_all("<Return>")
                process = subprocess.Popen(
                    args=command,
                    shell=True,
                    text=True,
                    cwd=self.main.dir_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)

                while True:
                    output = process.stdout.readline()
                    if output == "":
                        break
                    _output_queue.put(output)

            except subprocess.CalledProcessError as e:
                _output_queue.put(f"subprocess.CalledProcessError: {e}")
            except OSError as e:
                _output_queue.put(f"OSError: {e}")
            except Exception as e:
                _output_queue.put(f"ERROR: {e}")
            finally:
                _output_queue.put("DONE")
                self.run_command_button.config(state=tk.ACTIVE)
                self.command_text.bind("<Return>", self.install_package)
                self.main.refresh_main()

        def _update_output():
            while True:
                output = _output_queue.get()
                if output == "DONE":
                    break
                self.command_output.insert(tk.END, output)
                self.command_output.see(tk.END)

        _output_queue = queue.Queue()
        command_thread = threading.Thread(target=_run_command)
        command_thread.start()
        update_thread = threading.Thread(target=_update_output)
        update_thread.start()

    def search_package(self, event: tk.Event = None):
        package = urllib.parse.quote_plus(self.search_text.get())
        if package:
            webbrowser.open(f"https://pypi.org/search/?q={package}", new=2)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x575")
    packages_tab = PackagesTab(root)
    packages_tab.pack()
    root.mainloop()
