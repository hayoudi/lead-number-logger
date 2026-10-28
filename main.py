import csv
import re
import sqlite3
import sys
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QRegExp
from PyQt5.QtGui import QFont, QRegExpValidator, QColor, QKeyEvent
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QAbstractItemView, QFileDialog, QComboBox,
    QInputDialog, QMessageBox, QDialog
)

STYLESHEET = """
QMainWindow {
    background-color: #12131C;
}
QWidget {
    color: #E2E8F0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QFrame#CardFrame {
    background-color: #1E202E;
    border: 1px solid #2B2D42;
    border-radius: 12px;
}
QLineEdit, QComboBox {
    background-color: #161824;
    border: 1px solid #2B2D42;
    border-radius: 6px;
    padding: 8px 12px;
    color: #FFFFFF;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #6366F1;
    background-color: #191B28;
}
QComboBox QAbstractItemView {
    background-color: #1E202E;
    border: 1px solid #2B2D42;
    selection-background-color: #4F46E5;
    selection-color: #FFFFFF;
    padding: 4px;
}
QPushButton#PrimaryBtn {
    background-color: #6366F1;
    color: #FFFFFF;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
}
QPushButton#PrimaryBtn:hover {
    background-color: #4F46E5;
}
QPushButton#AddCatBtn {
    background-color: #27273A;
    color: #A5B4FC;
    border: 1px solid #4F46E5;
    border-radius: 6px;
    font-weight: bold;
    font-size: 15px;
    padding: 6px 12px;
}
QPushButton#AddCatBtn:hover {
    background-color: #4F46E5;
    color: #FFFFFF;
}
QPushButton#DelCatBtn {
    background-color: #27273A;
    color: #F87171;
    border: 1px solid #EF4444;
    border-radius: 6px;
    font-weight: bold;
    padding: 6px 12px;
}
QPushButton#DelCatBtn:hover {
    background-color: #EF4444;
    color: #FFFFFF;
}
QPushButton#ContactBtn {
    background-color: #064E3B;
    color: #6EE7B7;
    font-weight: bold;
    border: 1px solid #10B981;
    border-radius: 6px;
    padding: 8px 14px;
}
QPushButton#ContactBtn:hover {
    background-color: #10B981;
    color: #FFFFFF;
}
QPushButton#DeleteBtn {
    background-color: #381A22;
    color: #FDA4AF;
    font-weight: bold;
    border: 1px solid #E11D48;
    border-radius: 6px;
    padding: 8px 12px;
}
QPushButton#DeleteBtn:hover {
    background-color: #E11D48;
    color: #FFFFFF;
}
QPushButton#ExportBtn {
    background-color: #1A3636;
    color: #2DD4BF;
    font-weight: bold;
    border: 1px solid #14B8A6;
    border-radius: 6px;
    padding: 8px 12px;
}
QPushButton#ExportBtn:hover {
    background-color: #14B8A6;
    color: #FFFFFF;
}
QTableWidget {
    background-color: #161824;
    border: 1px solid #2B2D42;
    border-radius: 8px;
    gridline-color: #232636;
    selection-background-color: #312E81;
    selection-color: #FFFFFF;
}
QHeaderView::section {
    background-color: #1E202E;
    color: #94A3B8;
    padding: 10px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #2B2D42;
}
QLabel#StatusBanner {
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}
QMessageBox, QInputDialog, QDialog {
    background-color: #1A1C29;
}
QMessageBox QLabel, QInputDialog QLabel, QDialog QLabel {
    color: #F1F5F9;
    font-size: 13px;
}
QMessageBox QPushButton, QInputDialog QPushButton, QDialog QPushButton {
    background-color: #27273A;
    color: #E2E8F0;
    border: 1px solid #3B3E5B;
    border-radius: 6px;
    padding: 6px 16px;
    min-width: 75px;
    font-weight: bold;
}
QMessageBox QPushButton:hover, QInputDialog QPushButton:hover, QDialog QPushButton:hover {
    background-color: #4F46E5;
    color: #FFFFFF;
}
"""


class LeadDatabase:
    def __init__(self, db_path="leads.db"):
        self.db_path = db_path
        self._init_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)

            cur.execute("SELECT COUNT(*) FROM categories")
            if cur.fetchone()[0] == 0:
                default_cats = [("General",), ("Clients",), ("Partners",)]
                cur.executemany("INSERT INTO categories (name) VALUES (?)", default_cats)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL UNIQUE,
                    category_id INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    contact_type TEXT DEFAULT 'None',
                    last_contact TEXT DEFAULT '-',
                    is_contacted INTEGER DEFAULT 0,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            conn.commit()

    @staticmethod
    def clean_phone(phone: str) -> str:
        num_map = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        cleaned = phone.strip().translate(num_map)
        return re.sub(r"[^\d]", "", cleaned)

    def get_categories(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM categories ORDER BY id ASC")
            return cur.fetchall()

    def add_category(self, name: str):
        name = name.strip()
        if not name:
            return False, "Category name cannot be empty.", None
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                conn.commit()
                return True, f"Category '{name}' created.", cur.lastrowid
        except sqlite3.IntegrityError:
            return False, "Category already exists.", None

    def delete_category(self, cat_id: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM categories WHERE id = ?", (cat_id,))
            row = cur.fetchone()
            if not row:
                return False, "Category not found."

            _, cat_name = row
            if cat_name == "General":
                return False, "The default 'General' category cannot be deleted."

            cur.execute("SELECT id FROM categories WHERE name = 'General'")
            default_row = cur.fetchone()
            default_id = default_row[0] if default_row else 1

            cur.execute("UPDATE leads SET category_id = ? WHERE category_id = ?", (default_id, cat_id))
            cur.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            conn.commit()
            return True, f"Category '{cat_name}' deleted. Leads moved to General."

    def add_lead(self, raw_phone: str, category_id: int):
        phone = self.clean_phone(raw_phone)
        if not (7 <= len(phone) <= 15):
            return False, f"Invalid phone length ({len(phone)} digits). Expected 7 to 15 digits."

        today = datetime.now().strftime("%Y-%m-%d")

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT l.phone, c.name 
                FROM leads l 
                LEFT JOIN categories c ON l.category_id = c.id 
                WHERE l.phone = ?
            """, (phone,))
            existing = cur.fetchone()

            if existing:
                cat_name = existing[1] or "General"
                return False, f"Number {phone} is already logged under '{cat_name}'."

            try:
                cur.execute("""
                    INSERT INTO leads (phone, category_id, created_at, contact_type, last_contact, is_contacted) 
                    VALUES (?, ?, ?, 'None', '-', 0)
                """, (phone, category_id, today))
                conn.commit()
                return True, f"Number {phone} added successfully."
            except sqlite3.Error as e:
                return False, f"Database error: {e}"

    def log_interaction(self, lead_ids: list, note: str):
        if not lead_ids:
            return False, "No leads selected."

        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                placeholders = ",".join("?" for _ in lead_ids)
                params = [note, today, 1] + lead_ids
                cur.execute(f"""
                    UPDATE leads 
                    SET contact_type = ?, last_contact = ?, is_contacted = ? 
                    WHERE id IN ({placeholders})
                """, params)
                conn.commit()
                return True, f"Updated interaction status for {len(lead_ids)} lead(s)."
        except sqlite3.Error as e:
            return False, f"Failed to log interaction: {e}"

    def delete_leads(self, lead_ids: list):
        if not lead_ids:
            return False, "No leads selected."
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                placeholders = ",".join("?" for _ in lead_ids)
                cur.execute(f"DELETE FROM leads WHERE id IN ({placeholders})", lead_ids)
                conn.commit()
                return True, f"Deleted {len(lead_ids)} record(s)."
        except sqlite3.Error as e:
            return False, f"Database error: {e}"

    def fetch_all(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT l.id, l.phone, COALESCE(c.name, 'General'), 
                       l.created_at, l.contact_type, l.last_contact, 
                       l.is_contacted, l.category_id
                FROM leads l 
                LEFT JOIN categories c ON l.category_id = c.id 
                ORDER BY l.id DESC
            """)
            return cur.fetchall()


class InteractionDialog(QDialog):
    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Interaction")
        self.setFixedSize(360, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        label = QLabel(f"Interaction note for {count} selected lead(s):")
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(label)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("e.g., Cold call, SMS campaign, WhatsApp...")
        layout.addWidget(self.note_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("background-color: #10B981; color: white; border: none;")
        self.save_btn.clicked.connect(self.accept)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def get_note(self) -> str:
        return self.note_input.text().strip()


class LeadTable(QTableWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.parent_window.delete_selected_leads()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = LeadDatabase()
        self.setWindowTitle("Lead Number Logger")
        self.resize(980, 700)
        self.setMinimumSize(800, 550)

        self._build_ui()
        self.reload_categories()
        self.reload_table()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Lead Number Logger")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF;")

        self.count_badge = QLabel("Total: 0")
        self.count_badge.setStyleSheet("""
            background-color: #27273A; 
            color: #818CF8; 
            padding: 5px 12px; 
            border-radius: 10px;
            font-weight: bold;
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.count_badge)
        main_layout.addLayout(header)

        self.status_banner = QLabel("")
        self.status_banner.setObjectName("StatusBanner")
        self.status_banner.setFixedHeight(38)
        self.status_banner.setAlignment(Qt.AlignCenter)
        self.clear_status()
        main_layout.addWidget(self.status_banner)

        input_card = QFrame()
        input_card.setObjectName("CardFrame")
        card_layout = QVBoxLayout(input_card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        form_label = QLabel("Add New Lead")
        form_label.setStyleSheet("color: #94A3B8; font-weight: 600;")
        card_layout.addWidget(form_label)

        input_row = QHBoxLayout()

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number (e.g., 09123456789)")
        self.phone_input.setMaxLength(15)
        self.phone_input.setValidator(QRegExpValidator(QRegExp(r"^[0-9۰-۹]{0,15}$"), self.phone_input))
        self.phone_input.returnPressed.connect(self.add_lead)

        self.category_combo = QComboBox()
        self.category_combo.setToolTip("Select Category")

        self.add_cat_btn = QPushButton("+")
        self.add_cat_btn.setObjectName("AddCatBtn")
        self.add_cat_btn.setToolTip("New Category")
        self.add_cat_btn.setCursor(Qt.PointingHandCursor)
        self.add_cat_btn.clicked.connect(self.create_category)

        self.del_cat_btn = QPushButton("-")
        self.del_cat_btn.setObjectName("DelCatBtn")
        self.del_cat_btn.setToolTip("Delete Selected Category")
        self.del_cat_btn.setCursor(Qt.PointingHandCursor)
        self.del_cat_btn.clicked.connect(self.remove_category)

        self.add_btn = QPushButton("Add Lead")
        self.add_btn.setObjectName("PrimaryBtn")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_lead)

        input_row.addWidget(self.phone_input, stretch=3)
        input_row.addWidget(self.category_combo, stretch=2)
        input_row.addWidget(self.add_cat_btn)
        input_row.addWidget(self.del_cat_btn)
        input_row.addWidget(self.add_btn, stretch=1)
        card_layout.addLayout(input_row)
        main_layout.addWidget(input_card)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search phone numbers...")
        self.search_input.textChanged.connect(self.filter_table)

        self.filter_combo = QComboBox()
        self.filter_combo.currentIndexChanged.connect(self.filter_table)

        self.contact_btn = QPushButton("Log Contact")
        self.contact_btn.setObjectName("ContactBtn")
        self.contact_btn.setCursor(Qt.PointingHandCursor)
        self.contact_btn.clicked.connect(self.log_contact)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("DeleteBtn")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.clicked.connect(self.delete_selected_leads)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setObjectName("ExportBtn")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_csv)

        toolbar.addWidget(self.search_input, stretch=3)
        toolbar.addWidget(self.filter_combo, stretch=2)
        toolbar.addWidget(self.contact_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.export_btn)
        main_layout.addLayout(toolbar)

        self.table = LeadTable(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Phone Number", "Category", "Date Added", "Last Action", "Last Contact"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.cellDoubleClicked.connect(lambda r, c: self.log_contact())

        main_layout.addWidget(self.table)

    def clear_status(self):
        self.status_banner.setText("")
        self.status_banner.setStyleSheet("background-color: transparent; border: 1px solid transparent;")

    def show_status(self, ok: bool, msg: str):
        if ok:
            self.status_banner.setStyleSheet(
                "background-color: #064E3B; color: #34D399; border: 1px solid #059669; border-radius: 6px;"
            )
        else:
            self.status_banner.setStyleSheet(
                "background-color: #4C0519; color: #FB7185; border: 1px solid #E11D48; border-radius: 6px;"
            )
        self.status_banner.setText(msg)
        QTimer.singleShot(4000, self.clear_status)

    def reload_categories(self):
        categories = self.db.get_categories()
        current_id = self.category_combo.currentData()

        self.category_combo.clear()
        for cid, name in categories:
            self.category_combo.addItem(name, cid)

        if current_id:
            idx = self.category_combo.findData(current_id)
            if idx != -1:
                self.category_combo.setCurrentIndex(idx)

        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem("All Categories", None)
        for cid, name in categories:
            self.filter_combo.addItem(name, cid)
        self.filter_combo.blockSignals(False)

    def create_category(self):
        name, ok = QInputDialog.getText(self, "New Category", "Category name:")
        if ok and name.strip():
            success, msg, new_id = self.db.add_category(name)
            self.show_status(success, msg)
            if success:
                self.reload_categories()
                idx = self.category_combo.findData(new_id)
                if idx != -1:
                    self.category_combo.setCurrentIndex(idx)

    def remove_category(self):
        cat_id = self.category_combo.currentData()
        cat_name = self.category_combo.currentText()
        if not cat_id:
            return

        if cat_name == "General":
            self.show_status(False, "Default category 'General' cannot be deleted.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Category",
            f"Delete category '{cat_name}'?\nAssigned leads will be moved to 'General'.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_category(cat_id)
            self.show_status(success, msg)
            if success:
                self.reload_categories()
                self.reload_table()

    def add_lead(self):
        raw_phone = self.phone_input.text().strip()
        if not raw_phone:
            self.show_status(False, "Please enter a phone number.")
            return

        cat_id = self.category_combo.currentData()
        success, msg = self.db.add_lead(raw_phone, cat_id)
        self.show_status(success, msg)

        if success:
            self.phone_input.clear()
            self.reload_table()

        self.phone_input.setFocus()

    def get_selected_rows(self) -> list:
        rows = set()
        for r in self.table.selectedRanges():
            for row_idx in range(r.topRow(), r.bottomRow() + 1):
                rows.add(row_idx)
        return sorted(rows)

    def log_contact(self):
        rows = self.get_selected_rows()
        if not rows:
            self.show_status(False, "Select at least one lead from the table.")
            return

        dialog = InteractionDialog(len(rows), self)
        if dialog.exec_() == QDialog.Accepted:
            note = dialog.get_note() or "Contacted"
            lead_ids = [int(self.table.item(r, 0).text()) for r in rows if self.table.item(r, 0)]

            if lead_ids:
                success, msg = self.db.log_interaction(lead_ids, note)
                self.show_status(success, msg)
                if success:
                    self.reload_table()

    def delete_selected_leads(self):
        rows = self.get_selected_rows()
        if not rows:
            self.show_status(False, "Select at least one lead to delete.")
            return

        lead_ids = [int(self.table.item(r, 0).text()) for r in rows if self.table.item(r, 0)]
        prompt = (
            f"Delete number '{self.table.item(rows[0], 1).text()}'?"
            if len(rows) == 1
            else f"Permanently delete {len(rows)} selected leads?"
        )

        reply = QMessageBox.warning(
            self, "Confirm Delete", prompt, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_leads(lead_ids)
            self.show_status(success, msg)
            if success:
                self.reload_table()

    def export_csv(self):
        rows = self.get_selected_rows()
        if not rows:
            self.show_status(False, "Select the rows you want to export.")
            return

        default_name = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", default_name, "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Phone Number", "Category", "Date Added", "Last Action", "Last Contact"])
                for r in rows:
                    row_data = [self.table.item(r, col).text() for col in range(1, 6)]
                    writer.writerow(row_data)

            self.show_status(True, f"Exported {len(rows)} lead(s) to CSV.")
        except OSError as e:
            self.show_status(False, f"Export failed: {e}")

    def reload_table(self):
        records = self.db.fetch_all()
        self.table.setRowCount(0)

        for idx, (lid, phone, cat_name, created, action, last_contact, contacted, cat_id) in enumerate(records):
            self.table.insertRow(idx)

            items = [
                QTableWidgetItem(str(lid)),
                QTableWidgetItem(phone),
                QTableWidgetItem(cat_name),
                QTableWidgetItem(created),
                QTableWidgetItem(action),
                QTableWidgetItem(last_contact),
            ]
            items[2].setData(Qt.UserRole, cat_id)

            color = QColor("#34D399") if contacted else QColor("#E2E8F0")
            if contacted:
                font = items[1].font()
                font.setBold(True)
                items[1].setFont(font)

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(color)
                self.table.setItem(idx, col, item)

        self.count_badge.setText(f"Total: {len(records)}")
        self.filter_table()

    def filter_table(self):
        query = self.db.clean_phone(self.search_input.text())
        cat_id = self.filter_combo.currentData()

        for r in range(self.table.rowCount()):
            phone_item = self.table.item(r, 1)
            cat_item = self.table.item(r, 2)

            match_query = (query in phone_item.text()) if (query and phone_item) else True
            match_cat = (cat_item.data(Qt.UserRole) == cat_id) if (cat_id is not None and cat_item) else True

            self.table.setRowHidden(r, not (match_query and match_cat))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
