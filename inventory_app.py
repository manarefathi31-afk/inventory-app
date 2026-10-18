# -*- coding: utf-8 -*-
"""
حركة السلع لمخزن مطعم
برنامج مخزون يعمل دون إنترنت
Windows 7 - 32 bit
"""

import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

APP_NAME = "حركة السلع لمخزن مطعم"
DB_NAME = "inventory_restaurant.db"


def get_database_path():
    """حفظ قاعدة البيانات بجانب البرنامج عند التشغيل، أو في مجلد المستخدم."""
    if getattr(sys, "frozen", False):
        folder = os.path.dirname(sys.executable)
    else:
        folder = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(folder, DB_NAME)


class RestaurantInventory:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1100x700")
        self.root.minsize(850, 550)
        self.root.configure(bg="#f3f5f9")

        self.db = sqlite3.connect(get_database_path())
        self.db.execute("PRAGMA foreign_keys = ON")

        self.create_database()
        self.setup_style()
        self.build_interface()
        self.refresh_items()
        self.refresh_statistics()

    def create_database(self):
        cursor = self.db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                unit TEXT NOT NULL DEFAULT 'وحدة',
                quantity REAL NOT NULL DEFAULT 0,
                min_quantity REAL NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT 'عام'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL DEFAULT 0,
                movement_date TEXT NOT NULL,
                note TEXT DEFAULT '',
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_type TEXT NOT NULL,
                people INTEGER NOT NULL,
                meal_date TEXT NOT NULL,
                note TEXT DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                address TEXT DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER,
                invoice_number TEXT DEFAULT '',
                invoice_date TEXT NOT NULL,
                total REAL NOT NULL DEFAULT 0,
                note TEXT DEFAULT ''
            )
        """)

        self.db.commit()

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            rowheight=30,
            font=("Arial", 10),
            background="white",
            fieldbackground="white"
        )

        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold"),
            background="#e8edf5"
        )

        style.configure(
            "TButton",
            font=("Arial", 10),
            padding=7
        )

    def build_interface(self):
        header = tk.Frame(self.root, bg="#263b63", height=85)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="حركة السلع لمخزن مطعم",
            font=("Arial", 22, "bold"),
            bg="#263b63",
            fg="white"
        ).pack(pady=(12, 0))

        tk.Label(
            header,
            text="إدارة المخزون وحركة المواد",
            font=("Arial", 10),
            bg="#263b63",
            fg="#dce6f7"
        ).pack()

        self.stats_frame = tk.Frame(self.root, bg="#f3f5f9")
        self.stats_frame.pack(fill="x", padx=12, pady=10)

        self.stat_items = self.create_stat_card(
            self.stats_frame, "عدد المواد", "0", "#3273dc"
        )
        self.stat_quantity = self.create_stat_card(
            self.stats_frame, "إجمالي الكميات", "0", "#16a085"
        )
        self.stat_value = self.create_stat_card(
            self.stats_frame, "قيمة المخزون", "0 دج", "#8e44ad"
        )

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.inventory_tab = tk.Frame(notebook, bg="#f3f5f9")
        self.movement_tab = tk.Frame(notebook, bg="#f3f5f9")
        self.meal_tab = tk.Frame(notebook, bg="#f3f5f9")
        self.supplier_tab = tk.Frame(notebook, bg="#f3f5f9")
        self.report_tab = tk.Frame(notebook, bg="#f3f5f9")

        notebook.add(self.inventory_tab, text="المخزون")
        notebook.add(self.movement_tab, text="حركة السلع")
        notebook.add(self.meal_tab, text="الوجبات")
        notebook.add(self.supplier_tab, text="الموردون")
        notebook.add(self.report_tab, text="التقارير")

        self.build_inventory_tab()
        self.build_movement_tab()
        self.build_meal_tab()
        self.build_supplier_tab()
        self.build_report_tab()

    def create_stat_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg="white", highlightbackground="#dce3ed",
                        highlightthickness=1)
        card.pack(side="right", fill="both", expand=True, padx=5)

        tk.Label(
            card, text=title, font=("Arial", 10),
            bg="white", fg="#65738a"
        ).pack(pady=(9, 3))

        label = tk.Label(
            card, text=value, font=("Arial", 16, "bold"),
            bg="white", fg=color
        )
        label.pack(pady=(0, 9))
        return label

    def build_inventory_tab(self):
        form = tk.LabelFrame(
            self.inventory_tab,
            text="إضافة مادة جديدة",
            bg="#f3f5f9",
            padx=10,
            pady=10
        )
        form.pack(fill="x", padx=10, pady=10)

        self.item_name = tk.StringVar()
        self.item_unit = tk.StringVar(value="كغ")
        self.item_quantity = tk.StringVar(value="0")
        self.item_minimum = tk.StringVar(value="0")
        self.item_price = tk.StringVar(value="0")
        self.item_category = tk.StringVar(value="مواد غذائية")

        fields = [
            ("اسم المادة", self.item_name, 18),
            ("الوحدة", self.item_unit, 10),
            ("الكمية الأولية", self.item_quantity, 10),
            ("الحد الأدنى", self.item_minimum, 10),
            ("سعر الوحدة", self.item_price, 10),
            ("التصنيف", self.item_category, 14)
        ]

        for column, (label, variable, width) in enumerate(fields):
            group = tk.Frame(form, bg="#f3f5f9")
            group.grid(row=0, column=column, padx=4, pady=4)

            tk.Label(
                group, text=label, bg="#f3f5f9", font=("Arial", 9)
            ).pack()

            tk.Entry(
                group, textvariable=variable, width=width,
                justify="right"
            ).pack()

        ttk.Button(
            form, text="إضافة المادة", command=self.add_item
        ).grid(row=1, column=0, columnspan=2, pady=10)

        search_frame = tk.Frame(self.inventory_tab, bg="#f3f5f9")
        search_frame.pack(fill="x", padx=10)

        tk.Label(
            search_frame, text="بحث عن مادة:",
            bg="#f3f5f9", font=("Arial", 10)
        ).pack(side="right", padx=5)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            justify="right", width=30
        )
        search_entry.pack(side="right", padx=5)
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_items())

        ttk.Button(
            search_frame, text="تحديث",
            command=self.refresh_items
        ).pack(side="left", padx=5)

        columns = (
            "id", "name", "category", "unit",
            "quantity", "price", "value", "minimum"
        )

        self.items_tree = ttk.Treeview(
            self.inventory_tab, columns=columns,
            show="headings"
        )

        headings = {
            "id": "الرقم",
            "name": "اسم المادة",
            "category": "التصنيف",
            "unit": "الوحدة",
            "quantity": "المتبقي",
            "price": "سعر الوحدة",
            "value": "القيمة",
            "minimum": "الحد الأدنى"
        }

        for column in columns:
            self.items_tree.heading(column, text=headings[column])
            self.items_tree.column(column, width=105, anchor="center")

        self.items_tree.column("name", width=180)
        self.items_tree.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = tk.Frame(self.inventory_tab, bg="#f3f5f9")
        buttons.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            buttons, text="حذف المادة المحددة",
            command=self.delete_item
        ).pack(side="right", padx=5)

        ttk.Button(
            buttons, text="تحديث الجدول",
            command=self.refresh_items
        ).pack(side="right", padx=5)

    def add_item(self):
        name = self.item_name.get().strip()
        unit = self.item_unit.get().strip() or "وحدة"
        category = self.item_category.get().strip() or "عام"

        if not name:
            messagebox.showwarning("تنبيه", "أدخل اسم المادة أولًا.")
            return

        try:
            quantity = float(self.item_quantity.get())
            minimum = float(self.item_minimum.get())
            price = float(self.item_price.get())

            if quantity < 0 or minimum < 0 or price < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "خطأ", "تأكد من إدخال كميات وأسعار صحيحة وغير سالبة."
            )
            return

        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO items
                (name, unit, quantity, min_quantity, price, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, unit, quantity, minimum, price, category))

            item_id = cursor.lastrowid

            if quantity > 0:
                cursor.execute("""
                    INSERT INTO movements
                    (item_id, movement_type, quantity, unit_price,
                     movement_date, note)
                    VALUES (?, 'دخول', ?, ?, ?, ?)
                """, (
                    item_id, quantity, price,
                    datetime.now().strftime("%Y-%m-%d"),
                    "الرصيد الافتتاحي"
                ))

            self.db.commit()

            self.item_name.set("")
            self.item_quantity.set("0")
            self.item_minimum.set("0")
            self.item_price.set("0")

            self.refresh_items()
            self.refresh_statistics()
            messagebox.showinfo("نجاح", "تمت إضافة المادة بنجاح.")

        except sqlite3.IntegrityError:
            messagebox.showerror("تنبيه", "اسم المادة موجود مسبقًا.")

    def delete_item(self):
        selected = self.items_tree.selection()

        if not selected:
            messagebox.showwarning("تنبيه", "حدد المادة التي تريد حذفها.")
            return

        item_id = self.items_tree.item(selected[0])["values"][0]

        confirm = messagebox.askyesno(
            "تأكيد الحذف",
            "هل تريد حذف المادة وسجل حركاتها؟"
        )

        if not confirm:
            return

        try:
            self.db.execute("DELETE FROM movements WHERE item_id=?", (item_id,))
            self.db.execute("DELETE FROM items WHERE id=?", (item_id,))
            self.db.commit()

            self.refresh_items()
            self.refresh_statistics()
            messagebox.showinfo("نجاح", "تم حذف المادة.")
        except sqlite3.Error as error:
            messagebox.showerror("خطأ", str(error))

    def refresh_items(self):
        if not hasattr(self, "items_tree"):
            return

        for row in self.items_tree.get_children():
            self.items_tree.delete(row)

        search = self.search_var.get().strip() if hasattr(self, "search_var") else ""

        rows = self.db.execute("""
            SELECT id, name, category, unit, quantity, price,
                   quantity * price, min_quantity
            FROM items
            WHERE name LIKE ?
            ORDER BY name
        """, ("%" + search + "%",)).fetchall()

        for row in rows:
            self.items_tree.insert("", "end", values=(
                row[0], row[1], row[2], row[3],
                self.format_number(row[4]),
                self.format_number(row[5]),
                self.format_number(row[6]),
                self.format_number(row[7])
            ))

    def refresh_statistics(self):
        row = self.db.execute("""
            SELECT COUNT(*), COALESCE(SUM(quantity), 0),
                   COALESCE(SUM(quantity * price), 0)
            FROM items
        """).fetchone()

        self.stat_items.config(text=str(row[0]))
        self.stat_quantity.config(text=self.format_number(row[1]))
        self.stat_value.config(
            text=self.format_number(row[2]) + " دج"
        )

    @staticmethod
    def format_number(value):
        try:
            number = float(value)
            if number.is_integer():
                return str(int(number))
            return "{:.2f}".format(number)
        except (ValueError, TypeError):
            return str(value)

    def build_movement_tab(self):
        form = tk.LabelFrame(
            self.movement_tab, text="تسجيل حركة سلعة",
            bg="#f3f5f9", padx=10, pady=10
        )
        form.pack(fill="x", padx=10, pady=10)

        self.move_item = tk.StringVar()
        self.move_type = tk.StringVar(value="دخول")
        self.move_quantity = tk.StringVar(value="1")
        self.move_price = tk.StringVar(value="0")
        self.move_date = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )
        self.move_note = tk.StringVar()

        tk.Label(form, text="المادة", bg="#f3f5f9").grid(row=0, column=0)
        self.move_combo = ttk.Combobox(
            form, textvariable=self.move_item, state="readonly", width=22
        )
        self.move_combo.grid(row=1, column=0, padx=5, pady=5)

        tk.Label(form, text="نوع الحركة", bg="#f3f5f9").grid(row=0, column=1)
        ttk.Combobox(
            form, textvariable=self.move_type,
            values=("دخول", "خروج"), state="readonly", width=12
        ).grid(row=1, column=1, padx=5, pady=5)

        for col, label, var, width in [
            (2, "الكمية", self.move_quantity, 10),
            (3, "سعر الوحدة", self.move_price, 10),
            (4, "التاريخ YYYY-MM-DD", self.move_date, 14),
            (5, "ملاحظة", self.move_note, 18)
        ]:
            tk.Label(form, text=label, bg="#f3f5f9").grid(row=0, column=col)
            tk.Entry(
                form, textvariable=var, width=width, justify="right"
            ).grid(row=1, column=col, padx=5, pady=5)

        ttk.Button(
            form, text="حفظ الحركة",
            command=self.record_movement
        ).grid(row=2, column=0, columnspan=2, pady=8)

        self.movement_tree = ttk.Treeview(
            self.movement_tab,
            columns=("date", "name", "type", "quantity", "price", "note"),
            show="headings"
        )

        for col, title in [
            ("date", "التاريخ"), ("name", "المادة"),
            ("type", "الحركة"), ("quantity", "الكمية"),
            ("price", "السعر"), ("note", "ملاحظة")
        ]:
            self.movement_tree.heading(col, text=title)
            self.movement_tree.column(col, anchor="center", width=130)

        self.movement_tree.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(
            self.movement_tab, text="تحديث الحركات",
            command=self.refresh_movements
        ).pack(pady=(0, 10))

        self.refresh_move_choices()
        self.refresh_movements()

    def refresh_move_choices(self):
        if hasattr(self, "move_combo"):
            self.move_combo["values"] = [
                "{} - {}".format(row[0], row[1])
                for row in self.db.execute(
                    "SELECT id, name FROM items ORDER BY name"
                ).fetchall()
            ]

    def record_movement(self):
        selected = self.move_item.get().strip()

        if not selected:
            messagebox.showwarning("تنبيه", "أضف مادة وحددها أولًا.")
            return

        try:
            item_id = int(selected.split(" - ", 1)[0])
            quantity = float(self.move_quantity.get())
            price = float(self.move_price.get())
            date_text = self.move_date.get().strip()

            datetime.strptime(date_text, "%Y-%m-%d")

            if quantity <= 0 or price < 0:
                raise ValueError

        except (ValueError, IndexError):
            messagebox.showerror(
                "خطأ", "تحقق من الكمية والسعر والتاريخ."
            )
            return

        item = self.db.execute(
            "SELECT quantity FROM items WHERE id=?", (item_id,)
        ).fetchone()

        if not item:
            messagebox.showerror("خطأ", "المادة غير موجودة.")
            return

        movement_type = self.move_type.get()
        old_quantity = item[0]

        if movement_type == "خروج" and quantity > old_quantity:
            messagebox.showerror(
                "رصيد غير كافٍ",
                "الكمية المتوفرة هي {} فقط.".format(
                    self.format_number(old_quantity)
                )
            )
            return

        new_quantity = (
            old_quantity + quantity
            if movement_type == "دخول"
            else old_quantity - quantity
        )

        try:
            self.db.execute("""
                INSERT INTO movements
                (item_id, movement_type, quantity, unit_price,
                 movement_date, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item_id, movement_type, quantity, price,
                date_text, self.move_note.get().strip()
            ))

            self.db.execute(
                "UPDATE items SET quantity=?, price=? WHERE id=?",
                (new_quantity, price, item_id)
            )

            self.db.commit()
            self.refresh_items()
            self.refresh_statistics()
            self.refresh_movements()
            self.refresh_move_choices()

            self.move_quantity.set("1")
            self.move_note.set("")

            messagebox.showinfo("نجاح", "تم تسجيل الحركة وتحديث المخزون.")

        except sqlite3.Error as error:
            self.db.rollback()
            messagebox.showerror("خطأ", str(error))

    def refresh_movements(self):
        if not hasattr(self, "movement_tree"):
            return

        for row in self.movement_tree.get_children():
            self.movement_tree.delete(row)

        rows = self.db.execute("""
            SELECT m.movement_date, i.name, m.movement_type,
                   m.quantity, m.unit_price, m.note
            FROM movements m
            JOIN items i ON i.id=m.item_id
            ORDER BY m.id DESC
        """).fetchall()

        for row in rows:
            self.movement_tree.insert("", "end", values=(
                row[0], row[1], row[2],
                self.format_number(row[3]),
                self.format_number(row[4]), row[5]
            ))

    def build_meal_tab(self):
        tk.Label(
            self.meal_tab,
            text="كشوف الوجبات",
            font=("Arial", 18, "bold"),
            bg="#f3f5f9",
            fg="#263b63"
        ).pack(pady=15)

        form = tk.LabelFrame(
            self.meal_tab, text="تسجيل وجبة",
            bg="#f3f5f9", padx=15, pady=15
        )
        form.pack(fill="x", padx=15)

        self.meal_type = tk.StringVar(value="غداء")
        self.meal_people = tk.StringVar(value="1")
        self.meal_date = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )
        self.meal_note = tk.StringVar()

        tk.Label(form, text="نوع الوجبة", bg="#f3f5f9").grid(row=0, column=0)
        ttk.Combobox(
            form, textvariable=self.meal_type,
            values=("غداء", "عشاء"), state="readonly", width=15
        ).grid(row=1, column=0, padx=10, pady=8)

        tk.Label(form, text="عدد الموقوفين", bg="#f3f5f9").grid(row=0, column=1)
        tk.Entry(
            form, textvariable=self.meal_people,
            justify="right", width=15
        ).grid(row=1, column=1, padx=10, pady=8)

        tk.Label(form, text="التاريخ YYYY-MM-DD", bg="#f3f5f9").grid(row=0, column=2)
        tk.Entry(
            form, textvariable=self.meal_date,
            justify="right", width=18
        ).grid(row=1, column=2, padx=10, pady=8)

        tk.Label(form, text="ملاحظة", bg="#f3f5f9").grid(row=0, column=3)
        tk.Entry(
            form, textvariable=self.meal_note,
            justify="right", width=22
        ).grid(row=1, column=3, padx=10, pady=8)

        ttk.Button(
            form, text="حفظ الوجبة",
            command=self.save_meal
        ).grid(row=2, column=0, columnspan=2, pady=10)

        self.meal_result = tk.Label(
            self.meal_tab, text="سعر الغداء: 130 دج | سعر العشاء: 185 دج",
            font=("Arial", 14, "bold"), bg="#f3f5f9", fg="#16a085"
        )
        self.meal_result.pack(pady=15)

        self.meal_tree = ttk.Treeview(
            self.meal_tab,
            columns=("date", "type", "people", "rate", "total", "note"),
            show="headings"
        )

        for col, title in [
            ("date", "التاريخ"), ("type", "الوجبة"),
            ("people", "عدد الموقوفين"), ("rate", "سعر الفرد"),
            ("total", "الإجمالي"), ("note", "ملاحظة")
        ]:
            self.meal_tree.heading(col, text=title)
            self.meal_tree.column(col, anchor="center", width=140)

        self.meal_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_meals()

    def save_meal(self):
        try:
            people = int(self.meal_people.get())
            date_text = self.meal_date.get().strip()
            datetime.strptime(date_text, "%Y-%m-%d")

            if people <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "خطأ", "أدخل عددًا صحيحًا موجبًا وتاريخًا بصيغة YYYY-MM-DD."
            )
            return

        self.db.execute("""
            INSERT INTO meal_records (meal_type, people, meal_date, note)
            VALUES (?, ?, ?, ?)
        """, (
            self.meal_type.get(), people, date_text,
            self.meal_note.get().strip()
        ))

        self.db.commit()
        self.refresh_meals()
        messagebox.showinfo("نجاح", "تم حفظ كشف الوجبة.")

    def refresh_meals(self):
        if not hasattr(self, "meal_tree"):
            return

        for row in self.meal_tree.get_children():
            self.meal_tree.delete(row)

        rows = self.db.execute("""
            SELECT meal_type, people, meal_date, note
            FROM meal_records
            ORDER BY meal_date DESC, id DESC
        """).fetchall()

        for meal_type, people, date_text, note in rows:
            rate = 130 if meal_type == "غداء" else 185
            self.meal_tree.insert("", "end", values=(
                date_text, meal_type, people, rate,
                people * rate, note
            ))

    def build_supplier_tab(self):
        form = tk.LabelFrame(
            self.supplier_tab, text="إضافة مورد",
            bg="#f3f5f9", padx=15, pady=15
        )
        form.pack(fill="x", padx=15, pady=15)

        self.supplier_name = tk.StringVar()
        self.supplier_phone = tk.StringVar()
        self.supplier_address = tk.StringVar()

        for col, title, var in [
            (0, "اسم المورد", self.supplier_name),
            (1, "الهاتف", self.supplier_phone),
            (2, "العنوان", self.supplier_address)
        ]:
            tk.Label(form, text=title, bg="#f3f5f9").grid(row=0, column=col)
            tk.Entry(
                form, textvariable=var,
                justify="right", width=25
            ).grid(row=1, column=col, padx=8, pady=8)

        ttk.Button(
            form, text="حفظ المورد",
            command=self.add_supplier
        ).grid(row=2, column=0, pady=8)

        self.supplier_tree = ttk.Treeview(
            self.supplier_tab,
            columns=("id", "name", "phone", "address"),
            show="headings"
        )

        for col, title in [
            ("id", "الرقم"), ("name", "اسم المورد"),
            ("phone", "الهاتف"), ("address", "العنوان")
        ]:
            self.supplier_tree.heading(col, text=title)
            self.supplier_tree.column(col, anchor="center", width=180)

        self.supplier_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_suppliers()

    def add_supplier(self):
        name = self.supplier_name.get().strip()

        if not name:
            messagebox.showwarning("تنبيه", "أدخل اسم المورد.")
            return

        self.db.execute("""
            INSERT INTO suppliers (name, phone, address)
            VALUES (?, ?, ?)
        """, (
            name,
            self.supplier_phone.get().strip(),
            self.supplier_address.get().strip()
        ))

        self.db.commit()
        self.supplier_name.set("")
        self.supplier_phone.set("")
        self.supplier_address.set("")
        self.refresh_suppliers()
        messagebox.showinfo("نجاح", "تم حفظ المورد.")

    def refresh_suppliers(self):
        if not hasattr(self, "supplier_tree"):
            return

        for row in self.supplier_tree.get_children():
            self.supplier_tree.delete(row)

        rows = self.db.execute("""
            SELECT id, name, phone, address
            FROM suppliers ORDER BY name
        """).fetchall()

        for row in rows:
            self.supplier_tree.insert("", "end", values=row)

    def build_report_tab(self):
        tk.Label(
            self.report_tab, text="تقارير المخزن",
            font=("Arial", 18, "bold"),
            bg="#f3f5f9", fg="#263b63"
        ).pack(pady=15)

        ttk.Button(
            self.report_tab, text="عرض ملخص المخزون",
            command=self.show_inventory_report
        ).pack(pady=8)

        ttk.Button(
            self.report_tab, text="عرض ملخص الوجبات",
            command=self.show_meal_report
        ).pack(pady=8)

        ttk.Button(
            self.report_tab, text="نسخ احتياطي لقاعدة البيانات",
            command=self.backup_database
        ).pack(pady=8)

        self.report_text = tk.Text(
            self.report_tab, height=18,
            font=("Arial", 11), wrap="word"
        )
        self.report_text.pack(fill="both", expand=True, padx=15, pady=15)

    def show_inventory_report(self):
        rows = self.db.execute("""
            SELECT name, quantity, unit, price, quantity * price
            FROM items ORDER BY name
        """).fetchall()

        total_value = sum(row[4] for row in rows)
        lines = ["تقرير المخزون", "=" * 45, ""]

        for name, quantity, unit, price, value in rows:
            lines.append(
                "{}: {} {} | سعر الوحدة: {} دج | القيمة: {} دج".format(
                    name, self.format_number(quantity), unit,
                    self.format_number(price), self.format_number(value)
                )
            )

        lines.extend([
            "",
            "عدد المواد: {}".format(len(rows)),
            "إجمالي قيمة المخزون: {} دج".format(
                self.format_number(total_value)
            )
        ])

        self.set_report_text("\n".join(lines))

    def show_meal_report(self):
        rows = self.db.execute("""
            SELECT meal_type, COUNT(*), SUM(people)
            FROM meal_records
            GROUP BY meal_type
        """).fetchall()

        total_cost = 0
        lines = ["ملخص الوجبات", "=" * 35, ""]

        for meal_type, count, people in rows:
            rate = 130 if meal_type == "غداء" else 185
            cost = people * rate
            total_cost += cost
            lines.append(
                "{}: عدد الكشوف {}، مجموع الموقوفين {}، الإجمالي {} دج".format(
                    meal_type, count, people, self.format_number(cost)
                )
            )

        lines.append("\nإجمالي الوجبات: {} دج".format(
            self.format_number(total_cost)
        ))

        self.set_report_text("\n".join(lines))

    def set_report_text(self, content):
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", content)

    def backup_database(self):
        from tkinter import filedialog
        import shutil

        path = filedialog.asksaveasfilename(
            title="حفظ نسخة احتياطية",
            defaultextension=".db",
            filetypes=[("قاعدة بيانات SQLite", "*.db")]
        )

        if not path:
            return

        try:
            self.db.commit()
            shutil.copy2(get_database_path(), path)
            messagebox.showinfo("نجاح", "تم حفظ النسخة الاحتياطية.")
        except OSError as error:
            messagebox.showerror("خطأ", str(error))

    def close(self):
        try:
            self.db.close()
        finally:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = RestaurantInventory(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
