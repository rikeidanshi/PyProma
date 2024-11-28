"""
name: Git
version: "1.0.0"
author: rikeidanshi <rikeidanshi@duck.com>
type: Tab Menu
description: Supports Git operations.
dependencies:
    - gitpython: "3.1.43"
settings: null
"""

import json
import os
import re
import tkinter as tk
import tkinter.ttk as ttk
from textwrap import dedent
from tkinter import messagebox

import git
from github import Github
from PyProma_common.PyProma_templates import tab_template
from PyProma_dir_view.plugins.plugin_manager import RefreshMethod

json_path = "PyProma_settings.json"


class GitTab(tab_template.TabTemplate):
    NAME = "Git"

    def __init__(self, master=None, main=None):
        super().__init__(master, self)
        self.git_tabs = ttk.Notebook(self)
        self.git_tabs.enable_traversal()
        self.local = GitLocalTab(self, main)
        self.git_tabs.add(self.local, text="Local", padding=3)
        self.remote = GitRemoteTab(self, main)
        self.git_tabs.add(self.remote, text="Remote", padding=3)
        self.git_tabs.pack(anchor=tk.NW)

    @RefreshMethod
    def refresh(self):
        self.local.refresh()
        self.remote.refresh()


class GitLocalTab(tk.Frame):
    def __init__(self, master=None, main=None):
        self.master, self.main = master, main
        super().__init__(master, width=800, height=550)
        self.propagate(False)
        self.git_log_frame = tk.Frame(self, width=400, height=550)
        self.git_log_frame.propagate(False)
        self.git_commit_tree = ttk.Treeview(
            self.git_log_frame, show="headings",
            columns=("hash", "author", "date", "message"))
        self.git_commit_tree.heading("hash", text="hash", anchor=tk.CENTER)
        self.git_commit_tree.heading("author", text="author", anchor=tk.CENTER)
        self.git_commit_tree.heading("date", text="date", anchor=tk.CENTER)
        self.git_commit_tree.heading(
            "message", text="message", anchor=tk.CENTER)
        self.git_commit_tree.pack(fill=tk.BOTH, expand=True)
        self.git_log_frame.grid(row=0, column=0)
        self.git_staging_frame = tk.Frame(self, width=400, height=550)
        self.git_staging_frame.propagate(False)
        self.git_staged_txt = tk.Label(
            self.git_staging_frame, text="Staged Changes")
        self.git_staged_txt.place(x=5, y=0)
        self.git_staged_changes = ttk.Treeview(
            self.git_staging_frame, show="headings", height=8,
            columns=("file", "changes"))
        self.git_staged_changes.heading(
            "file", text="file", anchor=tk.CENTER)
        self.git_staged_changes.heading(
            "changes", text="changes", anchor=tk.CENTER)
        self.git_staged_changes.place(x=0, y=20)
        self.git_staged_changes.bind("<<TreeviewSelect>>", self.git_stage)
        self.git_unstaged_txt = tk.Label(
            self.git_staging_frame, text="Changes")
        self.git_unstaged_txt.place(x=5, y=210)
        self.git_unstaged_changes = ttk.Treeview(
            self.git_staging_frame, show="headings", height=8,
            columns=("file", "changes"))
        self.git_unstaged_changes.heading(
            "file", text="file", anchor=tk.CENTER)
        self.git_unstaged_changes.heading(
            "changes", text="changes", anchor=tk.CENTER)
        self.git_unstaged_changes.place(x=0, y=230)
        self.git_unstaged_changes.bind("<<TreeviewSelect>>", self.git_stage)
        self.commit_message = tk.Text(
            self.git_staging_frame, height=5)
        self.commit_message.insert(tk.END, "Commit message")
        self.commit_message.place(x=0, y=420)
        self.git_branches = ttk.Combobox(
            self.git_staging_frame, state=tk.DISABLED)
        self.git_branches.place(x=5, y=500)
        self.commit_button = tk.Button(
            self.git_staging_frame,
            text="Commit",
            command=self.git_commit,
            state=tk.DISABLED)
        self.commit_button.place(x=250, y=500)
        self.git_staging_frame.grid(row=0, column=1)

    def refresh(self):
        self.git_commit_tree.delete(*self.git_commit_tree.get_children())
        self.git_staged_changes.delete(
            *self.git_staged_changes.get_children())
        self.git_unstaged_changes.delete(
            *self.git_unstaged_changes.get_children())
        self.git_branches["values"] = []
        self.git_branches["state"] = tk.DISABLED
        self.git_branches.unbind("<<ComboboxSelected>>")
        self.commit_button["state"] = tk.DISABLED
        self.git_read_commits()
        self.git_read_diffs()
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            branches = [branch.name for branch in repo.branches]
            self.git_branches["values"] = branches
            self.git_branches["state"] = "readonly"
            self.git_branches.set(repo.active_branch)
            self.git_branches.bind(
                "<<ComboboxSelected>>", self.git_switch_branch)
            self.commit_button["state"] = tk.ACTIVE

    def git_read_commits(self):
        """this func reads git commit log and makes git tree.
        """
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            for commit in repo.iter_commits():
                self.git_commit_tree.insert(
                    "",
                    tk.END,
                    values=(
                        commit.hexsha,
                        commit.author.name,
                        commit.authored_datetime,
                        commit.message))
        else:
            self.git_commit_tree.insert(
                    "",
                    tk.END,
                    values=(
                        "this directory",
                        "is not",
                        "a git",
                        "repository"))

    def git_read_diffs(self):
        """this func reads git diffs and inserts into git_unstaged_changes.
        """
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            diffs = repo.index.diff(None)
            for diff in diffs:
                a = diff.a_path
                change_type = diff.change_type
                self.git_unstaged_changes.insert(
                    "", tk.END, values=(a, change_type))
            diffs = repo.index.diff("HEAD")
            for diff in diffs:
                a = diff.a_path
                change_type = diff.change_type
                self.git_staged_changes.insert(
                    "", tk.END, values=(a, change_type))

    def git_switch_branch(self, _: tk.Event):
        """this func switches local git branch

        Args:
            _ (tk.Event): tk.Event(ignored)
        """
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            try:
                repo.git.checkout(self.git_branches.get())
            except git.exc.GitCommandError as e:
                messagebox.showerror(
                    title="git.exc.GitCommandError", message=str(e))
            else:
                self.main.refresh_main()
            finally:
                self.git_branches.set(repo.active_branch)

    def git_stage(self, e: tk.Event):
        """this func stage(unstage)s files.

        Args:
            e (tk.Event): tkinter event object
        """
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            widget = e.widget
            selected_item = widget.selection()
            if len(selected_item) > 0:
                if widget == self.git_staged_changes:
                    try:
                        repo.index.reset(
                            paths=[widget.item(selected_item)["values"][0]])
                    except git.exc.GitCommandError as e:
                        messagebox.showerror(
                            title="git.exc.GitCommandError",
                            message=str(e))
                    else:
                        self.git_unstaged_changes.insert(
                            "", tk.END,
                            values=widget.item(selected_item)["values"])
                        widget.delete(selected_item)
                elif widget == self.git_unstaged_changes:
                    try:
                        repo.git.add(widget.item(selected_item)["values"][0])
                    except git.exc.GitCommandError as e:
                        messagebox.showerror(
                            title="git.exc.GitCommandError",
                            message=str(e))
                    else:
                        self.git_staged_changes.insert(
                            "", tk.END,
                            values=widget.item(selected_item)["values"])
                        widget.delete(selected_item)

    def git_commit(self):
        """this func commits staged diffs
        """
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            commit_message = self.commit_message.get(1., tk.END)
            staged_changes = repo.index.diff("HEAD")
            literal_message = commit_message.replace(" ", "").replace("\n", "")
            if (len(literal_message) > 0
                    and commit_message != "Commit message\n"):
                if len(staged_changes) == 0:
                    message = """\
                    There are no staged changes and so you cannot commit.
                    Would you like to stage all changes and commit directly?
                    """
                    if messagebox.askokcancel(
                            title="Confirm", message=dedent(message)):
                        repo.git.add(".")
                    else:
                        return
                try:
                    repo.index.commit(message=commit_message)
                except git.exc.CommandError as e:
                    messagebox.showerror(
                        title="git.exc.CommandError",
                        message=str(e))
                finally:
                    self.main.refresh_main()
            else:
                messagebox.showerror(
                    title="Commit message is Empty",
                    message="Please write commit message in entry box.")


class GitRemoteTab(tk.Frame):
    def __init__(self, master=None, main=None):
        with open(json_path) as file:
            self.access_tokens = json.load(file)["tokens"]
        self.master, self.main = master, main
        super().__init__(master, width=800, height=550)
        self.propagate(False)
        self.remotes_label = tk.Label(self, text="remote:")
        self.remotes_label.pack()
        self.remotes_combo = ttk.Combobox(self, state=tk.DISABLED)
        self.remotes_combo.pack()
        self.branches_label = tk.Label(self, text="branch:")
        self.branches_label.pack()
        self.local_branches_combo = ttk.Combobox(self, state=tk.DISABLED)
        self.local_branches_combo.pack()
        self.pull_button = tk.Button(
            self, text="pull", state=tk.DISABLED, command=self.remote_pull)
        self.pull_button.pack()
        self.push_button = tk.Button(
            self, text="push", state=tk.DISABLED, command=self.remote_push)
        self.push_button.pack()
        self.fetch_button = tk.Button(
            self, text="fetch", state=tk.DISABLED, command=self.remote_fetch)
        self.fetch_button.pack()

    def refresh(self):
        self.remotes_combo["values"] = []
        self.remotes_combo["state"] = tk.DISABLED
        self.local_branches_combo["values"] = []
        self.local_branches_combo["state"] = tk.DISABLED
        self.pull_button["state"] = tk.DISABLED
        self.push_button["state"] = tk.DISABLED

        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            branches = [branch.name for branch in repo.branches]
            self.local_branches_combo["values"] = branches
            self.local_branches_combo.set(repo.active_branch)
            remote_name = [remote.name for remote in repo.remotes]
            if remote_name:
                if len(remote_name) > 1:
                    remote_name.append("ALL")
                self.remotes_combo["values"] = remote_name
                self.remotes_combo.set(remote_name[0])
                self.remotes_combo["state"] = "readonly"
                self.pull_button["state"] = tk.ACTIVE
                self.push_button["state"] = tk.ACTIVE
                remotes = repo.remote().urls
                github_pattern = r"https://github\.com/[^/]+/[^/]"
                github_remotes = [
                    url.removeprefix("https://github.com/")
                    for url in remotes if re.match(github_pattern, url)]
                if github_remotes and self.access_tokens["github"]:
                    github = Github(self.access_tokens["github"])
                    self.github_remotes = [
                        github.get_repo(remote_name)
                        for remote_name in github_remotes]
            self.local_branches_combo["state"] = tk.ACTIVE

    def remote_pull(self):
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            if self.remotes_combo.get() == "ALL":
                remote_names = [remote.name for remote in repo.remotes]
            else:
                remote_names = [self.remotes_combo.get()]
            for remote_name in remote_names:
                remote = repo.remote(remote_name)
                remote.pull(self.local_branches_combo.get())

    def remote_push(self):
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            if self.remotes_combo.get() == "ALL":
                remote_names = [remote.name for remote in repo.remotes]
            else:
                remote_names = [self.remotes_combo.get()]
            for remote_name in remote_names:
                remote = repo.remote(remote_name)
                remote.push(self.local_branches_combo.get())

    def remote_fetch(self):
        if os.path.isdir(git_path := os.path.join(self.main.dir_path, ".git")):
            repo = git.Repo(git_path)
            if self.remotes_combo.get() == "ALL":
                remote_names = [remote.name for remote in repo.remotes]
            else:
                remote_names = [self.remotes_combo.get()]
            for remote_name in remote_names:
                remote = repo.remote(remote_name)
                remote.fetch()


class GitMenu(tk.Menu):
    NAME = "Git"

    def __init__(self, master=None, main=None):
        self.main = main
        super().__init__(master, tearoff=False)
        self.add_command(
            label="Git Init", command=self.git_init)

    def git_init(self):
        """this func runs git init
        """
        if os.path.isdir(self.main.dir_path):
            git_path = os.path.join(self.main.dir_path, ".git")
            if not os.path.isdir(git_path):
                try:
                    git.Repo.init(self.main.dir_path)
                except git.exc.GitCommandError as e:
                    messagebox.showerror(
                        title="git.exc.GitError", message=str(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x575")
    git_tab = GitTab(root)
    git_tab.pack()
    root.mainloop()
