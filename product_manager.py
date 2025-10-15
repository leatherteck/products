import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime
from pathlib import Path


class ProductManager:
    def __init__(self, root):
        self.root = root
        self.root.title("LeatherTek Product Manager")
        self.root.geometry("1400x800")

        self.products_file = "products.json"
        self.products = []
        self.filtered_products = []
        self.current_product = None

        # Load existing products
        self.load_products()

        # Build UI
        self.build_ui()

        # Populate product list
        self.refresh_product_list()

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
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
            return False

    def build_ui(self):
        """Build the main UI"""
        # Main container with two panes
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
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

        # Description (for CSV export only)
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(form_frame, width=40, height=5, wrap=tk.WORD)
        self.description_text.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(form_frame, text="(One feature per line, for CSV export only)", font=("", 8)).grid(row=row, column=2, sticky=tk.NW)
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
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Save to JSON", command=self.save_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export GHL CSV", command=self.export_ghl_csv).pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(toolbar, textvariable=self.status_var, relief=tk.SUNKEN).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

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
        self.description_text.delete('1.0', tk.END)
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

        # Get description from text widget (if user has entered one)
        description_lines = self.description_text.get('1.0', tk.END).strip().split('\n')
        description_lines = [line.strip() for line in description_lines if line.strip()]

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                # GHL/Shopify bulk upload format matching your existing CSV
                fieldnames = [
                    'Handle',
                    'Title',
                    'Body (HTML)',
                    'Included in Online Store',
                    'Image Src',
                    'Option1 Name',
                    'Option1 Value',
                    'Option2 Name',
                    'Option2 Value',
                    'Option3 Name',
                    'Option3 Value',
                    'Variant Price',
                    'Variant Compare At Price',
                    'Track Inventory',
                    'Allow Out of Stock Purchases',
                    'Available Quantity',
                    'SKU',
                    'Weight Value',
                    'Weight Unit',
                    'Dimension Length',
                    'Dimension Width',
                    'Dimension Height',
                    'Dimension Unit',
                    'Product Label Enable',
                    'Label Title',
                    'Label Start Date',
                    'Label End Date',
                    'SEO Title',
                    'SEO Description'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for idx, product in enumerate(self.products):
                    # Extract price value
                    price = product.get('price', '').replace('$', '').replace(',', '').strip()

                    # Generate handle (unique identifier)
                    design_num = product.get('designNumber', f'product-{idx}')
                    make = product.get('make', '').lower().replace(' ', '-')
                    model = product.get('model', '').lower().replace(' ', '-')
                    year = product.get('year', '').replace(' ', '-')
                    design_name = product.get('design', '').lower().replace(' ', '-').replace('design', '').strip('-')
                    handle = f"{design_num}-{make}-{model}-{year}-{design_name}-{idx}".lower()

                    # Generate HTML body with description
                    body_html = f'<p><strong>Design Number: {design_num}</strong></p>'
                    if description_lines:
                        body_html += '<ul>'
                        for line in description_lines:
                            body_html += f'<li>{line}</li>'
                        body_html += '</ul>'

                    # SEO Description (plain text)
                    seo_description = '\n '.join(description_lines) if description_lines else ''

                    # Get trim with design number for Variant 3 (matching your format)
                    trim = product.get('trim', '')
                    trim_with_design = f"{trim} {design_num}" if trim else design_num

                    # Format row
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
                        'Weight Value': '',
                        'Weight Unit': '',
                        'Dimension Length': '',
                        'Dimension Width': '',
                        'Dimension Height': '',
                        'Dimension Unit': '',
                        'Product Label Enable': 'FALSE',
                        'Label Title': '',
                        'Label Start Date': '',
                        'Label End Date': '',
                        'SEO Title': product.get('name', ''),
                        'SEO Description': seo_description
                    }

                    writer.writerow(row)

            messagebox.showinfo("Success",
                f"Exported {len(self.products)} products to GHL/Shopify format!\n\n"
                f"File: {filename}\n\n"
                "Upload this CSV to GoHighLevel:\n"
                "1. Go to Sites > Funnels/Websites > Products\n"
                "2. Click 'Bulk Import'\n"
                "3. Upload this CSV file")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")


def main():
    root = tk.Tk()
    app = ProductManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
