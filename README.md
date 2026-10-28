# Lead Number Logger

A lightweight, modern desktop application built with Python and PyQt5 for logging, categorizing, and tracking customer phone numbers and sales leads. It utilizes a local SQLite database for fast, offline storage with zero external server dependencies.

---

## Features

* **Quick Entry & Validation:** Automatically normalizes phone inputs (supporting standard and Persian/Arabic numerals) and prevents duplicate entries across categories.
* **Category Management:** Group leads by industry or custom categories (e.g., *Mechanics*, *Restaurants*). Deleting a category safely reassigns its records to the default `General` group.
* **Interaction Tracking:** Log outreach statuses or custom notes (e.g., *Cold Call*, *Promo SMS*, *WhatsApp*) for single or multiple selected leads at once. Contacted records are visually highlighted in the table.
* **Live Filtering:** Instant search by phone digits and category filters to locate records in milliseconds.
* **CSV Export:** Export selected rows (phone number, category, status, and last contact date) to a UTF-8 CSV file for use in Excel, CRM, or bulk SMS panels.
* **Keyboard Shortcuts:** Press `Enter` to quickly log a number, double-click a row to log an interaction, or press `Delete` to remove selected records.
* **Modern Dark UI:** Clean, distraction-free interface styled with custom QSS.

---

## Prerequisites

Ensure you have Python 3.8 or higher installed on your system. The only required third-party package is `PyQt5` (`sqlite3` and `csv` are part of the Python standard library).

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hayoudi/lead-number-logger.git
   cd lead-number-logger
   ```

2. **Install dependencies:**
   ```bash
   pip install PyQt5
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

*(Note: On the first launch, the app will automatically create a local `leads.db` SQLite file in your project directory.)*

---

## Building a Standalone Executable (.exe)

If you want to run the application on Windows without needing Python installed, you can bundle it into a single executable file using `PyInstaller`:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller --noconsole --onefile --name "LeadLogger" main.py
   ```

The compiled standalone `.exe` file will be generated inside the `dist/` folder.

---

## License

This project is open-source and available under the [MIT License](LICENSE).
