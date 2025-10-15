import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
from datetime import datetime
from pathlib import Path


class GitProductsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LeatherTek - Git Manager for products.json")
        self.root.geometry("900x700")

        self.products_file = "products.json"
        self.repo_path = Path.cwd()

        # Build UI
        self.build_ui()

        # Initial status check
        self.refresh_status()

    def build_ui(self):
        """Build the main UI"""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(
            title_frame,
            text="Git Manager - products.json",
            font=("Arial", 16, "bold")
        )
        title_label.pack()

        # Git Status Section
        status_frame = ttk.LabelFrame(self.root, text="Git Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

        # Refresh button
        ttk.Button(
            status_frame,
            text="Refresh Status",
            command=self.refresh_status
        ).pack(pady=5)

        # Product Info Section
        info_frame = ttk.LabelFrame(self.root, text="products.json Info", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.info_var = tk.StringVar(value="Loading...")
        info_label = ttk.Label(info_frame, textvariable=self.info_var, font=("Arial", 10))
        info_label.pack()

        # Commit Message Section
        commit_frame = ttk.LabelFrame(self.root, text="Commit Message", padding=10)
        commit_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(commit_frame, text="Enter commit message:").pack(anchor=tk.W)

        self.commit_var = tk.StringVar()
        self.commit_entry = ttk.Entry(commit_frame, textvariable=self.commit_var, width=80)
        self.commit_entry.pack(fill=tk.X, pady=5)

        # Quick message templates
        template_frame = ttk.Frame(commit_frame)
        template_frame.pack(fill=tk.X, pady=5)

        ttk.Label(template_frame, text="Quick templates:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            template_frame,
            text="Update products",
            command=lambda: self.commit_var.set("update: products.json with latest vehicle data changes")
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            template_frame,
            text="Add products",
            command=lambda: self.commit_var.set("feat: add new products to catalog")
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            template_frame,
            text="Fix products",
            command=lambda: self.commit_var.set("fix: correct product data in products.json")
        ).pack(side=tk.LEFT, padx=2)

        # Action Buttons Section
        action_frame = ttk.LabelFrame(self.root, text="Git Actions", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        button_container = ttk.Frame(action_frame)
        button_container.pack()

        # Individual action buttons
        self.add_button = ttk.Button(
            button_container,
            text="1. Git Add products.json",
            command=self.git_add,
            width=25
        )
        self.add_button.grid(row=0, column=0, padx=5, pady=5)

        self.commit_button = ttk.Button(
            button_container,
            text="2. Git Commit",
            command=self.git_commit,
            width=25
        )
        self.commit_button.grid(row=0, column=1, padx=5, pady=5)

        self.push_button = ttk.Button(
            button_container,
            text="3. Git Push",
            command=self.git_push,
            width=25
        )
        self.push_button.grid(row=0, column=2, padx=5, pady=5)

        # Combined action button
        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        self.all_button = ttk.Button(
            action_frame,
            text="Add + Commit + Push All",
            command=self.git_all,
            style="Accent.TButton"
        )
        self.all_button.pack(pady=5)

        # Output Section
        output_frame = ttk.LabelFrame(self.root, text="Command Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Load product info
        self.load_product_info()

    def run_git_command(self, command, show_output=True):
        """Run a git command and return output"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                shell=True
            )

            output = result.stdout + result.stderr

            if show_output:
                self.output_text.insert(tk.END, f"\n> {command}\n")
                self.output_text.insert(tk.END, output)
                self.output_text.insert(tk.END, "-" * 80 + "\n")
                self.output_text.see(tk.END)

            return result.returncode == 0, output
        except Exception as e:
            error_msg = f"Error running command: {str(e)}"
            if show_output:
                self.output_text.insert(tk.END, f"\nERROR: {error_msg}\n")
                self.output_text.see(tk.END)
            return False, error_msg

    def load_product_info(self):
        """Load and display products.json info"""
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                products = json.load(f)

            # Count products
            total = len(products)

            # Count by make
            makes = {}
            for p in products:
                make = p.get('make', 'Unknown')
                makes[make] = makes.get(make, 0) + 1

            info = f"Total Products: {total} | "
            info += " | ".join([f"{make}: {count}" for make, count in sorted(makes.items())])

            self.info_var.set(info)
        except Exception as e:
            self.info_var.set(f"Error loading products.json: {str(e)}")

    def refresh_status(self):
        """Refresh git status display"""
        self.status_text.delete(1.0, tk.END)

        # Get git status
        success, output = self.run_git_command("git status", show_output=False)

        if success:
            self.status_text.insert(tk.END, output)
        else:
            self.status_text.insert(tk.END, "Error getting git status\n")
            self.status_text.insert(tk.END, output)

        # Reload product info
        self.load_product_info()

    def git_add(self):
        """Stage products.json for commit"""
        self.output_text.delete(1.0, tk.END)

        success, output = self.run_git_command(f"git add {self.products_file}")

        if success:
            messagebox.showinfo("Success", f"{self.products_file} staged successfully!")
            self.refresh_status()
        else:
            messagebox.showerror("Error", f"Failed to stage {self.products_file}")

    def git_commit(self):
        """Commit staged changes"""
        commit_msg = self.commit_var.get().strip()

        if not commit_msg:
            messagebox.showerror("Error", "Please enter a commit message!")
            return

        self.output_text.delete(1.0, tk.END)

        # Escape quotes in commit message
        commit_msg = commit_msg.replace('"', '\\"')

        success, output = self.run_git_command(f'git commit -m "{commit_msg}"')

        if success:
            messagebox.showinfo("Success", "Changes committed successfully!")
            self.commit_var.set("")  # Clear commit message
            self.refresh_status()
        else:
            if "nothing to commit" in output.lower():
                messagebox.showwarning("Warning", "Nothing to commit. Stage changes first using 'Git Add'.")
            else:
                messagebox.showerror("Error", "Failed to commit changes")

    def git_push(self):
        """Push commits to remote"""
        self.output_text.delete(1.0, tk.END)

        # Check if there are commits to push
        success, output = self.run_git_command("git status", show_output=False)

        if "Your branch is up to date" in output and "nothing to commit" in output:
            messagebox.showinfo("Info", "Nothing to push. Repository is up to date.")
            return

        # Push to origin
        success, output = self.run_git_command("git push origin main")

        if success:
            messagebox.showinfo("Success", "Changes pushed to GitHub successfully!")
            self.refresh_status()
        else:
            # Try master branch if main fails
            if "main" in output and "error" in output.lower():
                success, output = self.run_git_command("git push origin master")
                if success:
                    messagebox.showinfo("Success", "Changes pushed to GitHub successfully!")
                    self.refresh_status()
                    return

            messagebox.showerror("Error", "Failed to push changes.\n\nCheck output for details.")

    def git_all(self):
        """Perform add, commit, and push in sequence"""
        commit_msg = self.commit_var.get().strip()

        if not commit_msg:
            messagebox.showerror("Error", "Please enter a commit message!")
            return

        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Starting Add -> Commit -> Push sequence...\n\n")

        # Step 1: Add
        self.output_text.insert(tk.END, "Step 1: Staging products.json...\n")
        success, output = self.run_git_command(f"git add {self.products_file}")

        if not success:
            messagebox.showerror("Error", "Failed at Step 1: Git Add")
            return

        # Step 2: Commit
        self.output_text.insert(tk.END, "\nStep 2: Committing changes...\n")
        commit_msg_escaped = commit_msg.replace('"', '\\"')
        success, output = self.run_git_command(f'git commit -m "{commit_msg_escaped}"')

        if not success:
            if "nothing to commit" in output.lower():
                messagebox.showwarning("Warning", "Nothing to commit. No changes detected in products.json.")
                return
            else:
                messagebox.showerror("Error", "Failed at Step 2: Git Commit")
                return

        # Step 3: Push
        self.output_text.insert(tk.END, "\nStep 3: Pushing to GitHub...\n")
        success, output = self.run_git_command("git push origin main")

        if not success:
            # Try master branch
            success, output = self.run_git_command("git push origin master")

        if success:
            messagebox.showinfo("Success",
                "All steps completed successfully!\n\n"
                f"- Added: {self.products_file}\n"
                f"- Committed: {commit_msg}\n"
                "- Pushed: to GitHub"
            )
            self.commit_var.set("")  # Clear commit message
            self.refresh_status()
        else:
            messagebox.showerror("Error", "Failed at Step 3: Git Push")


def main():
    root = tk.Tk()

    # Configure style
    style = ttk.Style()
    style.theme_use('default')

    app = GitProductsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
