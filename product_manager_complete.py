import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import csv
import subprocess
from datetime import datetime
from pathlib import Path


class ProductManagerComplete:
    def __init__(self, root):
        self.root = root
        self.root.title("LeatherTek Product Manager + Git")
        self.root.geometry("1600x900")

        # Set window icon
        try:
            self.root.iconbitmap("leathertek.ico")
        except:
            pass  # If icon file not found, use default

        self.products_file = "products.json"
        self.repo_path = Path.cwd()
        self.products = []
        self.filtered_products = []
        self.current_product = None

        # Configure git remote automatically
        self.configure_git_remote()

        # Load existing products
        self.load_products()

        # Build UI
        self.build_ui()

        # Populate product list
        self.refresh_product_list()

    def configure_git_remote(self):
        """Auto-configure git remote to correct repository"""
        correct_remote = "https://github.com/leatherteck/products.git"

        try:
            # Check current remote
            result = subprocess.run(
                "git remote get-url origin",
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                shell=True
            )

            current_remote = result.stdout.strip()

            # If remote is different, update it
            if current_remote and current_remote != correct_remote:
                subprocess.run(
                    f'git remote set-url origin {correct_remote}',
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    shell=True
                )
        except:
            pass  # If git not configured, skip

    def load_products(self):
        """Load products from JSON file"""
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
                self.filtered_products = self.products.copy()
        except FileNotFoundError:
            self.products = []
            self.filtered_products = []
            messagebox.showwarning("File Not Found", f"{self.products_file} not found. Starting with empty list.")

    def save_products(self):
        """Save products to JSON file"""
        try:
            # Create backup
            backup_file = f"products_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)

            # Save main file
            with open(self.products_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Success", f"Products saved!\nBackup created: {backup_file}")

            # Refresh git status after save
            self.refresh_git_status()

            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
            return False

    def build_ui(self):
        """Build the main UI"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Product Management
        self.product_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.product_tab, text="Product Management")
        self.build_product_tab()

        # Tab 2: Git Manager
        self.git_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.git_tab, text="Git Manager")
        self.build_git_tab()

    def build_product_tab(self):
        """Build the product management tab"""
        # Main container with two panes
        main_paned = ttk.PanedWindow(self.product_tab, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Product list
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # Search/Filter section
        filter_frame = ttk.LabelFrame(left_frame, text="Search & Filter", padding=5)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_products())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)

        ttk.Label(filter_frame, text="Make:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.filter_make_var = tk.StringVar(value="All")
        make_combo = ttk.Combobox(filter_frame, textvariable=self.filter_make_var, state="readonly", width=28)
        make_combo.grid(row=1, column=1, sticky=tk.EW, padx=5)
        make_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_products())
        self.make_combo = make_combo

        filter_frame.columnconfigure(1, weight=1)

        # Product list
        list_frame = ttk.LabelFrame(left_frame, text="Products", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for products
        columns = ("Year", "Make", "Model", "Trim", "Design", "Price")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=20)

        self.tree.heading("#0", text="ID")
        self.tree.column("#0", width=50)

        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Year":
                self.tree.column(col, width=80)
            elif col == "Price":
                self.tree.column(col, width=80)
            else:
                self.tree.column(col, width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<<TreeviewSelect>>', self.on_product_select)

        # Right panel - Product details/form
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        # Form section
        form_frame = ttk.LabelFrame(right_frame, text="Product Details", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Form fields
        row = 0

        # Year
        ttk.Label(form_frame, text="Year/Range:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.year_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.year_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(form_frame, text="(e.g., 2023 or 2020-2023)", font=("", 8)).grid(row=row, column=2, sticky=tk.W)
        row += 1

        # Make
        ttk.Label(form_frame, text="Make:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.make_var = tk.StringVar()
        self.make_entry = ttk.Combobox(form_frame, textvariable=self.make_var, width=38)
        self.make_entry.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        row += 1

        # Model
        ttk.Label(form_frame, text="Model:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.model_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        row += 1

        # Trim
        ttk.Label(form_frame, text="Trim:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.trim_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.trim_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        row += 1

        # Design
        ttk.Label(form_frame, text="Design:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.design_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.design_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(form_frame, text="(e.g., Custom Design K1)", font=("", 8)).grid(row=row, column=2, sticky=tk.W)
        row += 1

        # Design Number
        ttk.Label(form_frame, text="Design Number:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.design_num_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.design_num_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(form_frame, text="(e.g., K2273-100)", font=("", 8)).grid(row=row, column=2, sticky=tk.W)
        row += 1

        # Price
        ttk.Label(form_frame, text="Price:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.price_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.price_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(form_frame, text="(e.g., $1895.00)", font=("", 8)).grid(row=row, column=2, sticky=tk.W)
        row += 1

        # Image URL
        ttk.Label(form_frame, text="Image URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.image_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.image_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        row += 1

        # Product URL
        ttk.Label(form_frame, text="Product URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.url_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        row += 1

        # Product Name (auto-generated)
        ttk.Label(form_frame, text="Product Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=40, state="readonly")
        name_entry.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(form_frame, text="(Auto-generated)", font=("", 8)).grid(row=row, column=2, sticky=tk.W)
        row += 1

        form_frame.columnconfigure(1, weight=1)

        # Auto-update product name when fields change
        for var in [self.design_var, self.make_var, self.model_var, self.trim_var, self.year_var]:
            var.trace('w', lambda *args: self.update_product_name())

        # Button section
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Add New Product", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Selected", command=self.update_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_form).pack(side=tk.LEFT, padx=5)

        # Bottom toolbar
        toolbar = ttk.Frame(self.product_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Save to JSON", command=self.save_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export GHL CSV", command=self.export_ghl_csv).pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(toolbar, textvariable=self.status_var, relief=tk.SUNKEN).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

    def build_git_tab(self):
        """Build the git manager tab"""
        # Title
        title_frame = ttk.Frame(self.git_tab)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(
            title_frame,
            text="Git Manager - products.json",
            font=("Arial", 16, "bold")
        )
        title_label.pack()

        # GitHub Account Section
        account_frame = ttk.LabelFrame(self.git_tab, text="GitHub Account", padding=10)
        account_frame.pack(fill=tk.X, padx=10, pady=5)

        # Account info display
        account_info_container = ttk.Frame(account_frame)
        account_info_container.pack(fill=tk.X, pady=5)

        ttk.Label(account_info_container, text="Logged in as:").pack(side=tk.LEFT, padx=5)
        self.git_user_var = tk.StringVar(value="Checking...")
        ttk.Label(account_info_container, textvariable=self.git_user_var, font=("", 10, "bold")).pack(side=tk.LEFT, padx=5)

        # Buttons container
        account_buttons = ttk.Frame(account_frame)
        account_buttons.pack(fill=tk.X, pady=5)

        ttk.Button(account_buttons, text="Refresh Account Info", command=self.check_git_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(account_buttons, text="Test Connection", command=self.test_git_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(account_buttons, text="Clear Credentials", command=self.clear_git_credentials).pack(side=tk.LEFT, padx=5)

        # Git Status Section
        status_frame = ttk.LabelFrame(self.git_tab, text="Git Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.git_status_text = scrolledtext.ScrolledText(
            status_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.git_status_text.pack(fill=tk.BOTH, expand=True)

        # Refresh button
        ttk.Button(
            status_frame,
            text="Refresh Status",
            command=self.refresh_git_status
        ).pack(pady=5)

        # Product Info Section
        info_frame = ttk.LabelFrame(self.git_tab, text="products.json Info", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.git_info_var = tk.StringVar(value="Loading...")
        info_label = ttk.Label(info_frame, textvariable=self.git_info_var, font=("Arial", 10))
        info_label.pack()

        # Commit Message Section
        commit_frame = ttk.LabelFrame(self.git_tab, text="Commit Message", padding=10)
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
        action_frame = ttk.LabelFrame(self.git_tab, text="Git Actions", padding=10)
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
        output_frame = ttk.LabelFrame(self.git_tab, text="Command Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.git_output_text = scrolledtext.ScrolledText(
            output_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.git_output_text.pack(fill=tk.BOTH, expand=True)

        # Initial git status
        self.refresh_git_status()

        # Check git user on startup
        self.check_git_user()

    def update_product_name(self):
        """Auto-generate product name from form fields"""
        design = self.design_var.get().strip()
        make = self.make_var.get().strip()
        model = self.model_var.get().strip()
        trim = self.trim_var.get().strip()
        year = self.year_var.get().strip()

        if design and make and model and trim and year:
            name = f"{design} for {make} {model} {trim} {year}"
            self.name_var.set(name)
        else:
            self.name_var.set("")

    def get_unique_makes(self):
        """Get unique makes from products"""
        makes = set()
        for p in self.products:
            if p.get('make'):
                makes.add(p['make'])
        return sorted(makes)

    def filter_products(self):
        """Filter products based on search and filters"""
        search_term = self.search_var.get().lower()
        filter_make = self.filter_make_var.get()

        self.filtered_products = []
        for p in self.products:
            # Make filter
            if filter_make != "All" and p.get('make') != filter_make:
                continue

            # Search term
            if search_term:
                searchable = f"{p.get('year', '')} {p.get('make', '')} {p.get('model', '')} {p.get('trim', '')} {p.get('design', '')} {p.get('designNumber', '')}".lower()
                if search_term not in searchable:
                    continue

            self.filtered_products.append(p)

        self.refresh_product_list()

    def refresh_product_list(self):
        """Refresh the product list display"""
        # Update make filter dropdown
        makes = ["All"] + self.get_unique_makes()
        self.make_combo['values'] = makes

        # Update make entry dropdown
        self.make_entry['values'] = self.get_unique_makes()

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate tree
        for idx, product in enumerate(self.filtered_products):
            values = (
                product.get('year', ''),
                product.get('make', ''),
                product.get('model', ''),
                product.get('trim', ''),
                product.get('design', ''),
                product.get('price', '')
            )
            self.tree.insert('', 'end', text=str(idx + 1), values=values, tags=(idx,))

        self.status_var.set(f"Showing {len(self.filtered_products)} of {len(self.products)} products")

        # Update git info
        self.update_git_info()

    def on_product_select(self, event):
        """Handle product selection"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        idx = int(item['tags'][0])
        product = self.filtered_products[idx]

        # Populate form
        self.year_var.set(product.get('year', ''))
        self.make_var.set(product.get('make', ''))
        self.model_var.set(product.get('model', ''))
        self.trim_var.set(product.get('trim', ''))
        self.design_var.set(product.get('design', ''))
        self.design_num_var.set(product.get('designNumber', ''))
        self.price_var.set(product.get('price', ''))
        self.image_var.set(product.get('image', ''))
        self.url_var.set(product.get('url', ''))
        self.name_var.set(product.get('name', ''))

        self.current_product = product

    def clear_form(self):
        """Clear all form fields"""
        self.year_var.set('')
        self.make_var.set('')
        self.model_var.set('')
        self.trim_var.set('')
        self.design_var.set('')
        self.design_num_var.set('')
        self.price_var.set('')
        self.image_var.set('')
        self.url_var.set('')
        self.name_var.set('')
        self.current_product = None
        self.tree.selection_remove(self.tree.selection())

    def validate_form(self):
        """Validate form fields"""
        required = {
            'Year': self.year_var.get(),
            'Make': self.make_var.get(),
            'Model': self.model_var.get(),
            'Trim': self.trim_var.get(),
            'Price': self.price_var.get(),
            'Image URL': self.image_var.get()
        }

        for field, value in required.items():
            if not value.strip():
                messagebox.showerror("Validation Error", f"{field} is required!")
                return False

        return True

    def add_product(self):
        """Add a new product"""
        if not self.validate_form():
            return

        product = {
            'year': self.year_var.get().strip(),
            'make': self.make_var.get().strip(),
            'model': self.model_var.get().strip(),
            'trim': self.trim_var.get().strip(),
            'name': self.name_var.get().strip(),
            'price': self.price_var.get().strip(),
            'image': self.image_var.get().strip(),
            'url': self.url_var.get().strip()
        }

        # Optional fields
        if self.design_var.get().strip():
            product['design'] = self.design_var.get().strip()
        if self.design_num_var.get().strip():
            product['designNumber'] = self.design_num_var.get().strip()

        self.products.append(product)
        self.filter_products()
        self.clear_form()
        messagebox.showinfo("Success", "Product added! Don't forget to save.")

    def update_product(self):
        """Update the selected product"""
        if not self.current_product:
            messagebox.showerror("Error", "No product selected!")
            return

        if not self.validate_form():
            return

        # Find and update
        for i, p in enumerate(self.products):
            if p is self.current_product:
                self.products[i] = {
                    'year': self.year_var.get().strip(),
                    'make': self.make_var.get().strip(),
                    'model': self.model_var.get().strip(),
                    'trim': self.trim_var.get().strip(),
                    'name': self.name_var.get().strip(),
                    'price': self.price_var.get().strip(),
                    'image': self.image_var.get().strip(),
                    'url': self.url_var.get().strip()
                }

                # Optional fields
                if self.design_var.get().strip():
                    self.products[i]['design'] = self.design_var.get().strip()
                if self.design_num_var.get().strip():
                    self.products[i]['designNumber'] = self.design_num_var.get().strip()

                break

        self.filter_products()
        self.clear_form()
        messagebox.showinfo("Success", "Product updated! Don't forget to save.")

    def delete_product(self):
        """Delete the selected product"""
        if not self.current_product:
            messagebox.showerror("Error", "No product selected!")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            self.products.remove(self.current_product)
            self.filter_products()
            self.clear_form()
            messagebox.showinfo("Success", "Product deleted! Don't forget to save.")

    def export_to_csv(self):
        """Export products to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['year', 'make', 'model', 'trim', 'design', 'designNumber', 'name', 'price', 'image', 'url']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for product in self.products:
                    writer.writerow(product)

            messagebox.showinfo("Success", f"Exported {len(self.products)} products to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def export_ghl_csv(self):
        """Export products in GHL/Shopify compatible format for bulk upload"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"products_bulk_upload_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'Handle', 'Title', 'Body (HTML)', 'Included in Online Store',
                    'Image Src', 'Option1 Name', 'Option1 Value', 'Option2 Name',
                    'Option2 Value', 'Option3 Name', 'Option3 Value', 'Variant Price',
                    'Variant Compare At Price', 'Track Inventory', 'Allow Out of Stock Purchases',
                    'Available Quantity', 'SKU', 'Weight Value', 'Weight Unit',
                    'Dimension Length', 'Dimension Width', 'Dimension Height', 'Dimension Unit',
                    'Product Label Enable', 'Label Title', 'Label Start Date', 'Label End Date',
                    'SEO Title', 'SEO Description'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for idx, product in enumerate(self.products):
                    price = product.get('price', '').replace('$', '').replace(',', '').strip()
                    design_num = product.get('designNumber', f'product-{idx}')
                    make = product.get('make', '').lower().replace(' ', '-')
                    model = product.get('model', '').lower().replace(' ', '-')
                    year = product.get('year', '').replace(' ', '-')
                    design_name = product.get('design', '').lower().replace(' ', '-').replace('design', '').strip('-')
                    handle = f"{design_num}-{make}-{model}-{year}-{design_name}-{idx}".lower()

                    body_html = f'<p><strong>Design Number: {design_num}</strong></p>'

                    trim = product.get('trim', '')
                    trim_with_design = f"{trim} {design_num}" if trim else design_num

                    row = {
                        'Handle': handle,
                        'Title': product.get('name', ''),
                        'Body (HTML)': body_html,
                        'Included in Online Store': 'TRUE',
                        'Image Src': product.get('image', ''),
                        'Option1 Name': 'Make',
                        'Option1 Value': product.get('make', ''),
                        'Option2 Name': 'Model',
                        'Option2 Value': product.get('model', ''),
                        'Option3 Name': 'Trim',
                        'Option3 Value': trim_with_design,
                        'Variant Price': price,
                        'Variant Compare At Price': '',
                        'Track Inventory': 'FALSE',
                        'Allow Out of Stock Purchases': 'TRUE',
                        'Available Quantity': '',
                        'SKU': design_num,
                        'Weight Value': '', 'Weight Unit': '',
                        'Dimension Length': '', 'Dimension Width': '',
                        'Dimension Height': '', 'Dimension Unit': '',
                        'Product Label Enable': 'FALSE',
                        'Label Title': '', 'Label Start Date': '', 'Label End Date': '',
                        'SEO Title': product.get('name', ''),
                        'SEO Description': ''
                    }

                    writer.writerow(row)

            messagebox.showinfo("Success", f"Exported {len(self.products)} products to GHL format!")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    # Git Methods
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
                self.git_output_text.insert(tk.END, f"\n> {command}\n")
                self.git_output_text.insert(tk.END, output)
                self.git_output_text.insert(tk.END, "-" * 80 + "\n")
                self.git_output_text.see(tk.END)

            return result.returncode == 0, output
        except Exception as e:
            error_msg = f"Error running command: {str(e)}"
            if show_output:
                self.git_output_text.insert(tk.END, f"\nERROR: {error_msg}\n")
                self.git_output_text.see(tk.END)
            return False, error_msg

    def update_git_info(self):
        """Update git product info"""
        try:
            total = len(self.products)
            makes = {}
            for p in self.products:
                make = p.get('make', 'Unknown')
                makes[make] = makes.get(make, 0) + 1

            info = f"Total Products: {total} | "
            info += " | ".join([f"{make}: {count}" for make, count in sorted(makes.items())])

            self.git_info_var.set(info)
        except Exception as e:
            self.git_info_var.set(f"Error: {str(e)}")

    def refresh_git_status(self):
        """Refresh git status display"""
        self.git_status_text.delete(1.0, tk.END)

        success, output = self.run_git_command("git status", show_output=False)

        if success:
            self.git_status_text.insert(tk.END, output)
        else:
            self.git_status_text.insert(tk.END, "Error getting git status\n")
            self.git_status_text.insert(tk.END, output)

        self.update_git_info()

    def git_add(self):
        """Stage products.json for commit"""
        self.git_output_text.delete(1.0, tk.END)

        success, output = self.run_git_command(f"git add {self.products_file}")

        if success:
            messagebox.showinfo("Success", f"{self.products_file} staged successfully!")
            self.refresh_git_status()
        else:
            messagebox.showerror("Error", f"Failed to stage {self.products_file}")

    def git_commit(self):
        """Commit staged changes"""
        commit_msg = self.commit_var.get().strip()

        if not commit_msg:
            messagebox.showerror("Error", "Please enter a commit message!")
            return

        self.git_output_text.delete(1.0, tk.END)

        commit_msg = commit_msg.replace('"', '\\"')

        success, output = self.run_git_command(f'git commit -m "{commit_msg}"')

        if success:
            messagebox.showinfo("Success", "Changes committed successfully!")
            self.commit_var.set("")
            self.refresh_git_status()
        else:
            if "nothing to commit" in output.lower():
                messagebox.showwarning("Warning", "Nothing to commit. Stage changes first using 'Git Add'.")
            else:
                messagebox.showerror("Error", "Failed to commit changes")

    def git_push(self):
        """Push commits to remote"""
        self.git_output_text.delete(1.0, tk.END)

        success, output = self.run_git_command("git status", show_output=False)

        if "Your branch is up to date" in output and "nothing to commit" in output:
            messagebox.showinfo("Info", "Nothing to push. Repository is up to date.")
            return

        success, output = self.run_git_command("git push origin main")

        if success:
            messagebox.showinfo("Success", "Changes pushed to GitHub successfully!")
            self.refresh_git_status()
        else:
            if "main" in output and "error" in output.lower():
                success, output = self.run_git_command("git push origin master")
                if success:
                    messagebox.showinfo("Success", "Changes pushed to GitHub successfully!")
                    self.refresh_git_status()
                    return

            messagebox.showerror("Error", "Failed to push changes.\n\nCheck output for details.")

    def git_all(self):
        """Perform add, commit, and push in sequence"""
        commit_msg = self.commit_var.get().strip()

        if not commit_msg:
            messagebox.showerror("Error", "Please enter a commit message!")
            return

        self.git_output_text.delete(1.0, tk.END)
        self.git_output_text.insert(tk.END, "Starting Add -> Commit -> Push sequence...\n\n")

        # Step 1: Add
        self.git_output_text.insert(tk.END, "Step 1: Staging products.json...\n")
        success, output = self.run_git_command(f"git add {self.products_file}")

        if not success:
            messagebox.showerror("Error", "Failed at Step 1: Git Add")
            return

        # Step 2: Commit
        self.git_output_text.insert(tk.END, "\nStep 2: Committing changes...\n")
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
        self.git_output_text.insert(tk.END, "\nStep 3: Pushing to GitHub...\n")
        success, output = self.run_git_command("git push origin main")

        if not success:
            success, output = self.run_git_command("git push origin master")

        if success:
            messagebox.showinfo("Success",
                "All steps completed successfully!\n\n"
                f"- Added: {self.products_file}\n"
                f"- Committed: {commit_msg}\n"
                "- Pushed: to GitHub"
            )
            self.commit_var.set("")
            self.refresh_git_status()
        else:
            messagebox.showerror("Error", "Failed at Step 3: Git Push")

    def check_git_user(self):
        """Check which GitHub user is currently logged in"""
        success, output = self.run_git_command("git config user.name", show_output=False)

        if success and output.strip():
            username = output.strip()
            # Also get email
            success_email, email_output = self.run_git_command("git config user.email", show_output=False)
            if success_email and email_output.strip():
                self.git_user_var.set(f"{username} ({email_output.strip()})")
            else:
                self.git_user_var.set(username)
        else:
            self.git_user_var.set("Not configured")

    def test_git_connection(self):
        """Test connection to GitHub"""
        self.git_output_text.delete(1.0, tk.END)
        self.git_output_text.insert(tk.END, "Testing connection to GitHub...\n\n")

        # Test remote connection
        success, output = self.run_git_command("git remote -v")

        if not success:
            messagebox.showerror("Connection Test Failed", "No git remotes configured.")
            return

        # Try to fetch from remote (dry run)
        self.git_output_text.insert(tk.END, "\nTesting authentication with remote...\n")
        success, output = self.run_git_command("git ls-remote origin HEAD")

        if success:
            messagebox.showinfo("Connection Test Successful",
                "Successfully connected to GitHub!\n\n"
                "Your credentials are working correctly."
            )
        else:
            messagebox.showerror("Connection Test Failed",
                "Failed to connect to GitHub.\n\n"
                "This could mean:\n"
                "1. You are not logged in\n"
                "2. Your credentials have expired\n"
                "3. Network issues\n\n"
                "Try using 'Clear Credentials' and push again\n"
                "to re-authenticate."
            )

    def clear_git_credentials(self):
        """Clear stored GitHub credentials"""
        if not messagebox.askyesno("Clear Credentials",
            "This will remove stored GitHub credentials from Windows Credential Manager.\n\n"
            "You will need to login again on your next push.\n\n"
            "Continue?"):
            return

        self.git_output_text.delete(1.0, tk.END)
        self.git_output_text.insert(tk.END, "Clearing GitHub credentials...\n\n")

        # Clear credentials using git credential helper
        commands = [
            'git credential-manager clear',
            'cmdkey /delete:git:https://github.com',
            'cmdkey /delete:LegacyGeneric:target=git:https://github.com'
        ]

        cleared = False
        for cmd in commands:
            success, output = self.run_git_command(cmd)
            if success or "deleted successfully" in output.lower():
                cleared = True

        if cleared:
            messagebox.showinfo("Credentials Cleared",
                "GitHub credentials have been cleared.\n\n"
                "On your next push, you will be prompted to login again."
            )
        else:
            messagebox.showinfo("Credentials Manager",
                "Attempted to clear credentials.\n\n"
                "You can also manually clear credentials:\n"
                "1. Press Windows + R\n"
                "2. Type: control /name Microsoft.CredentialManager\n"
                "3. Look for 'git:https://github.com'\n"
                "4. Click Remove"
            )


def main():
    root = tk.Tk()

    style = ttk.Style()
    style.theme_use('default')

    app = ProductManagerComplete(root)
    root.mainloop()


if __name__ == "__main__":
    main()
