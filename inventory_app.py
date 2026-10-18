# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime

APP_NAME = "حركة السلع لمخزن مطعم"
DB_PATH = os.path.join(
    os.path.expanduser("~"),
    "inventory_restaurant.db"
)

# قاعدة البيانات المحلية
db = sqlite3.connect(DB_PATH)

db.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL DEFAULT 'وحدة',
    quantity REAL NOT NULL DEFAULT 0,
    min_quantity REAL NOT NULL DEFAULT 0
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    movement_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    date TEXT NOT NULL,
    note TEXT DEFAULT '',
    FOREIGN KEY(item_id) REFERENCES items(id)
)
""")

db.commit()

# النافذة الرئيسية
root = tk.Tk()
root.title(APP_NAME)
root.geometry("1100x700")
root.minsize(850, 550)
root.configure(bg="#F4F7FB")

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#FFFFFF",
    foreground="#263445",
    rowheight=32,
    fieldbackground="#FFFFFF",
    font=("Arial", 11)
)

style.configure(
    "Treeview.Heading",
    background="#E8EFF8",
    foreground="#203864",
    font=("Arial", 11, "bold"),
    padding=8
)

style.map(
    "Treeview",
    background=[("selected", "#D8E8FF")],
    foreground=[("selected", "#152C50")]
)

# رأس البرنامج
header = tk.Frame(root, bg="#FFFFFF", height=80)
header.pack(fill="x", padx=12, pady=(12, 6))
header.pack_propagate(False)

title = tk.Label(
    header,
    text="حركة السلع لمخزن مطعم",
    font=("Arial", 22, "bold"),
    bg="#FFFFFF",
    fg="#203864",
    anchor="e"
)
title.pack(side="right", padx=20, pady=18)

subtitle = tk.Label(
    header,
    text="نظام إدارة المخزون",
    font=("Arial", 10),
    bg="#FFFFFF",
    fg="#718096"
)
subtitle.pack(side="left", padx=20)

# بطاقات الإحصائيات
stats = tk.Frame(root, bg="#F4F7FB")
stats.pack(fill="x", padx=12, pady=6)

def make_card(parent, caption, color):
    card = tk.Frame(
        parent,
        bg="#FFFFFF",
        highlightbackground="#E1E8F0",
        highlightthickness=1
    )

    tk.Label(
        card,
        text=caption,
        bg="#FFFFFF",
        fg="#718096",
        font=("Arial", 10, "bold")
    ).pack(pady=(12, 3))

    value = tk.Label(
        card,
        text="0",
        bg="#FFFFFF",
        fg=color,
        font=("Arial", 21, "bold")
    )
    value.pack(pady=(0, 12))

    return card, value

card1, total_items_label = make_card(
    stats, "عدد المواد", "#2878D0"
)
card2, total_quantity_label = make_card(
    stats, "إجمالي الرصيد", "#15966A"
)
card3, low_stock_label = make_card(
    stats, "مواد منخفضة", "#D97706"
)

for card in (card1, card2, card3):
    card.pack(side="right", expand=True, fill="x", padx=5)

# منطقة المحتوى
content = tk.Frame(root, bg="#F4F7FB")
content.pack(fill="both", expand=True, padx=12, pady=8)

# نموذج إضافة مادة
form = tk.LabelFrame(
    content,
    text="  إضافة مادة جديدة  ",
    bg="#FFFFFF",
    fg="#203864",
    font=("Arial", 12, "bold"),
    padx=12,
    pady=12
)
form.pack(fill="x", pady=(0, 10))

tk.Label(
    form, text="اسم المادة",
    bg="#FFFFFF"
).grid(row=0, column=5, padx=6, pady=5)

name_entry = ttk.Entry(form, width=20)
name_entry.grid(row=1, column=5, padx=6, pady=5)

tk.Label(
    form, text="الوحدة",
    bg="#FFFFFF"
).grid(row=0, column=4, padx=6, pady=5)

unit_entry = ttk.Entry(form, width=12)
unit_entry.insert(0, "كلغ")
unit_entry.grid(row=1, column=4, padx=6, pady=5)

tk.Label(
    form, text="الرصيد الافتتاحي",
    bg="#FFFFFF"
).grid(row=0, column=3, padx=6, pady=5)

quantity_entry = ttk.Entry(form, width=14)
quantity_entry.insert(0, "0")
quantity_entry.grid(row=1, column=3, padx=6, pady=5)

tk.Label(
    form, text="الحد الأدنى",
    bg="#FFFFFF"
).grid(row=0, column=2, padx=6, pady=5)

minimum_entry = ttk.Entry(form, width=12)
minimum_entry.insert(0, "0")
minimum_entry.grid(row=1, column=2, padx=6, pady=5)

def refresh():
    for row in table.get_children():
        table.delete(row)

    rows = db.execute("""
        SELECT id, name, unit, quantity, min_quantity
        FROM items
        ORDER BY name
    """).fetchall()

    total_quantity = sum(row[3] for row in rows)
    low_stock = sum(
        1 for row in rows
        if row[3] <= row[4]
    )

    for row in rows:
        table.insert("", "end", values=(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4]
        ))

    total_items_label.config(text=str(len(rows)))
    total_quantity_label.config(
        text=f"{total_quantity:g}"
    )
    low_stock_label.config(text=str(low_stock))

def add_item():
    name = name_entry.get().strip()
    unit = unit_entry.get().strip() or "وحدة"

    if not name:
        messagebox.showwarning(
            "تنبيه", "أدخل اسم المادة أولًا"
        )
        return

    try:
        quantity = float(quantity_entry.get())
        minimum = float(minimum_entry.get())

        if quantity < 0 or minimum < 0:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "خطأ", "أدخل كميات صحيحة غير سالبة"
        )
        return

    try:
        cursor = db.execute("""
            INSERT INTO items
            (name, unit, quantity, min_quantity)
            VALUES (?, ?, ?, ?)
        """, (name, unit, quantity, minimum))

        item_id = cursor.lastrowid

        if quantity > 0:
            db.execute("""
                INSERT INTO movements
                (item_id, movement_type, quantity, date, note)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item_id,
                "رصيد افتتاحي",
                quantity,
                datetime.now().strftime("%Y-%m-%d"),
                "الرصيد عند إنشاء المادة"
            ))

        db.commit()

    except sqlite3.IntegrityError:
        messagebox.showerror(
            "خطأ", "هذه المادة مسجلة مسبقًا"
        )
        return

    name_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)
    quantity_entry.insert(0, "0")

    refresh()

    messagebox.showinfo(
        "نجاح", "تمت إضافة المادة بنجاح"
    )

ttk.Button(
    form,
    text="إضافة المادة",
    command=add_item
).grid(row=1, column=1, padx=10, pady=5)

# جدول المواد
table_frame = tk.Frame(content, bg="#FFFFFF")
table_frame.pack(fill="both", expand=True)

columns = (
    "id", "name", "unit",
    "quantity", "minimum"
)

table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

headers = {
    "id": "الرقم",
    "name": "اسم المادة",
    "unit": "الوحدة",
    "quantity": "الرصيد المتبقي",
    "minimum": "الحد الأدنى"
}

for col in columns:
    table.heading(col, text=headers[col], anchor="e")
    table.column(col, width=140, anchor="center")

table.column("name", width=260)

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=table.yview
)
table.configure(yscrollcommand=scrollbar.set)

table.pack(side="right", fill="both", expand=True)
scrollbar.pack(side="left", fill="y")

def close_app():
    db.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)

refresh()
root.mainloop()
