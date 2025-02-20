import json
import sqlite3
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QCoreApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QLineEdit, QCompleter, QCheckBox, QFileDialog, QMessageBox, QProgressDialog
)
from database import get_db_connection, initialize_database, batch_insert_user_transfers

CONFIG_PATH = Path.home() / ".local/share/showmyslskd/config.json"

class QueryUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ShowMySlskD - Query UI")
        self.setGeometry(100, 100, 800, 500)

        self.config = self.load_config()
        self.cancel_flag = [False]

        layout = QVBoxLayout()

        self.import_button = QPushButton("Import Data from slskd")
        self.import_button.clicked.connect(self.import_data_dialog)
        layout.addWidget(self.import_button)

        self.overwrite_checkbox = QCheckBox("Overwrite existing data")
        layout.addWidget(self.overwrite_checkbox)

        # Add Date Range Filter Label
        self.date_label = QLabel("Select a date range:")
        layout.addWidget(self.date_label)

        # Dropdown for date range selection
        self.date_dropdown = QComboBox()
        self.date_dropdown.addItems([
            "All Time",
            "Last 24 Hours",
            "Last 7 Days",
            "Last 30 Days"
        ])
        layout.addWidget(self.date_dropdown)

        # Add Search Label
        self.search_label = QLabel("Filter by Username or Artist:")
        layout.addWidget(self.search_label)

        # Search Field with Autocomplete
        self.search_input = QLineEdit()
        self.search_dropdown = QComboBox()
        self.search_dropdown.setEditable(True)  # Allows manual entry

        # Autocomplete setup
        self.completer = QCompleter(self.get_all_usernames_and_artists())
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_dropdown.setCompleter(self.completer)

        layout.addWidget(self.search_dropdown)

        self.query_label = QLabel("Select a query:")
        layout.addWidget(self.query_label)

        self.query_dropdown = QComboBox()
        self.query_dropdown.addItems([
            "Top 10 Users by Files Downloaded",
            "Top 10 Users by Data Downloaded (MB)",
            "Most Downloaded Artists",
            "Users with Most Errors",
            "Users with Most Canceled Transfers",
            "Total Data Transferred by Day",
            "Total Files Transferred by Day"
        ])
        layout.addWidget(self.query_dropdown)

        self.run_query_button = QPushButton("Run Query")
        self.run_query_button.clicked.connect(self.run_query)
        layout.addWidget(self.run_query_button)

        self.show_chart_button = QPushButton("Show Chart")
        self.show_chart_button.clicked.connect(self.show_chart)
        layout.addWidget(self.show_chart_button)

        self.chart_canvas = None
        self.progress = None  

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

    def get_all_usernames_and_artists(self):
        """Fetch all unique usernames and artist names for autocomplete."""
        if not self.config["output_db"] or not Path(self.config["output_db"]).exists():
            return []  # Return an empty list if the database is not set or missing

        conn = sqlite3.connect(self.config["output_db"])
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT DISTINCT Username FROM UserTransfers")
            usernames = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT Artist FROM UserTransfers")
            artists = [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            usernames, artists = [], []
        finally:
            conn.close()

        return usernames + artists  # Combine both lists


    def load_config(self):
        """Loads database paths from the configuration file."""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        return {"input_db": "", "output_db": ""}

    def save_config(self, input_db, output_db):
        """Ensures the config directory exists and saves database paths to the configuration file."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)  # ✅ Ensure the directory exists
        with open(CONFIG_PATH, "w") as f:
            json.dump({"input_db": input_db, "output_db": output_db}, f)


    def import_data_dialog(self):
        """Check config and prompt for database paths if needed."""
        if not self.config["input_db"] or not self.config["output_db"]:
            QMessageBox.information(self, "Configuration Required",
                                    "Please select the input and output database files.")

            input_db, _ = QFileDialog.getOpenFileName(self, "Select Input Database", "", "SQLite Files (*.db);;All Files (*)")
            if not input_db:
                return  # User canceled

            output_db, _ = QFileDialog.getSaveFileName(self, "Select Output Database", "", "SQLite Files (*.db);;All Files (*)")
            if not output_db:
                return  # User canceled

            self.config["input_db"] = input_db
            self.config["output_db"] = output_db
            self.save_config(input_db, output_db)

        # Confirm action before proceeding
        overwrite = self.overwrite_checkbox.isChecked()
        action = "Overwriting" if overwrite else "Adding data to"

        reply = QMessageBox.question(
            self, "Import Confirmation",
            f"Importing {self.config['input_db']} and {action} {self.config['output_db']}",
            QMessageBox.Ok | QMessageBox.Cancel
        )

        if reply == QMessageBox.Cancel:
            return  

        self.process_data(self.config["input_db"], self.config["output_db"], overwrite)


    def process_data(self, input_db, output_db, overwrite):
        """Starts the data import in a separate thread with progress updates."""
        self.cancel_flag = [False]

        self.progress = QProgressDialog("Importing data...", "Cancel", 0, 100, self)
        self.progress.setWindowTitle("Processing Data")
        self.progress.setMinimumDuration(500)
        self.progress.canceled.connect(self.cancel_import)

        self.worker = DataImportWorker(input_db, output_db, overwrite, self.cancel_flag)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.import_complete.connect(self.import_finished)
        self.worker.start()

    def cancel_import(self):
        """Handles user canceling the import."""
        self.cancel_flag[0] = True

    def update_progress(self, value):
        """Updates the progress bar."""
        if self.progress:
            self.progress.setValue(value)

    def import_finished(self, new_records, skipped_records):
        """Handles completion of data import and ensures the progress dialog closes."""
        
        if self.progress:
            self.progress.close()  # ✅ Close progress dialog
        
        QMessageBox.information(
            self, "Import Complete",
            f"\u2705 {new_records} new records added.\n\u274C {skipped_records} duplicates skipped."
        )


    def run_query(self):
        """Runs the selected query using the stored database paths and filters by date range and search input."""
        if not self.config["output_db"]:
            QMessageBox.warning(self, "Error", "No output database configured. Please import data first.")
            return

        conn = sqlite3.connect(self.config["output_db"])
        cursor = conn.cursor()

        selected_query = self.query_dropdown.currentText()
        selected_range = self.date_dropdown.currentText()
        search_term = self.search_dropdown.currentText().strip()

        # ✅ Define date filters correctly
        date_filter_map = {
            "All Time": "",
            "Last 24 Hours": "AND EndedAt >= datetime('now', '-1 day')",
            "Last 7 Days": "AND EndedAt >= datetime('now', '-7 days')",
            "Last 30 Days": "AND EndedAt >= datetime('now', '-30 days')"
        }
        date_filter = date_filter_map.get(selected_range, "")

        # ✅ Determine if search_term is a username or artist
        search_filter = ""

        if search_term:
            cursor.execute("SELECT COUNT(*) FROM UserTransfers WHERE Username = ?", (search_term,))
            is_username = cursor.fetchone()[0] > 0  # If there's a match, it's a username

            if is_username:
                search_filter = f"AND Username = '{search_term}'"
            else:
                search_filter = f"AND Artist = '{search_term}'"

        # ✅ Update queries to include search_filter dynamically
        query_map = {
            "Top 10 Users by Files Downloaded": f"""
                SELECT Username, COUNT(*) AS TotalFiles
                FROM UserTransfers
                WHERE 1=1 {date_filter} {search_filter}
                GROUP BY Username
                ORDER BY TotalFiles DESC
                LIMIT 10;
            """,
            "Top 10 Users by Data Downloaded (MB)": f"""
                SELECT Username, SUM(BytesTransferred) / (1024 * 1024) AS TotalDataMB
                FROM UserTransfers
                WHERE 1=1 {date_filter} {search_filter}
                GROUP BY Username
                ORDER BY TotalDataMB DESC
                LIMIT 10;
            """,
            "Most Downloaded Artists": f"""
                SELECT Artist, COUNT(*) AS TotalDownloads
                FROM UserTransfers
                WHERE 1=1 {date_filter} {search_filter}
                GROUP BY Artist
                ORDER BY TotalDownloads DESC
                LIMIT 10;
            """,
            "Users with Most Errors": f"""
                SELECT Username, COUNT(*) AS ErrorCount
                FROM UserTransfers
                WHERE State LIKE '%Errored%' {date_filter} {search_filter}
                GROUP BY Username
                ORDER BY ErrorCount DESC
                LIMIT 10;
            """,
            "Users with Most Canceled Transfers": f"""
                SELECT Username, COUNT(*) AS CancelCount
                FROM UserTransfers
                WHERE State LIKE '%Canceled%' {date_filter} {search_filter}
                GROUP BY Username
                ORDER BY CancelCount DESC
                LIMIT 10;
            """,
            "Total Data Transferred by Day": f"""
                SELECT DATE(EndedAt) AS TransferDate, SUM(BytesTransferred) / (1024 * 1024) AS TotalDataMB
                FROM UserTransfers
                WHERE 1=1 {date_filter} {search_filter}
                GROUP BY TransferDate
                ORDER BY TransferDate DESC;
            """,
            "Total Files Transferred by Day": f"""
                SELECT DATE(EndedAt) AS TransferDate, COUNT(*) AS TotalFiles
                FROM UserTransfers
                WHERE 1=1 {date_filter} {search_filter}
                GROUP BY TransferDate
                ORDER BY TransferDate DESC;
            """
        }

        sql_query = query_map[selected_query]

        cursor.execute(sql_query)
        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()

        self.table.setRowCount(len(results))
        self.table.setColumnCount(len(column_names))
        self.table.setHorizontalHeaderLabels(column_names)

        for row_idx, row_data in enumerate(results):
            for col_idx, col_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))


    def show_chart(self):
        """Generates a bar chart and embeds it in the UI instead of opening a new window."""
        rows = self.table.rowCount()
        cols = self.table.columnCount()

        if rows == 0:
            QMessageBox.warning(self, "No Data", "No data available to visualize.")
            return

        labels = []
        values = []

        for row in range(rows):
            labels.append(self.table.item(row, 0).text())  # First column as label
            values.append(float(self.table.item(row, 1).text()))  # Second column as value

        # ✅ Remove old chart if it exists
        if self.chart_canvas:
            self.chart_canvas.setParent(None)

        # ✅ Create a new figure and canvas
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(labels, values, color="skyblue")
        ax.set_xlabel("Category")
        ax.set_ylabel("Count")
        ax.set_title(self.query_dropdown.currentText())
        ax.set_xticks(range(len(labels)))  # ✅ Explicitly set tick positions
        ax.set_xticklabels(labels, rotation=45, ha="right")

        self.chart_canvas = FigureCanvas(fig)  # ✅ Embed Matplotlib figure in PySide6
        self.layout().addWidget(self.chart_canvas)  # ✅ Add chart to UI

        fig.canvas.draw()  # ✅ Ensure the figure is rendered properly

class DataImportWorker(QThread):
    """Background thread to import data without freezing the UI."""
    progress_updated = Signal(int)
    import_complete = Signal(int, int)

    def __init__(self, input_db, output_db, overwrite, cancel_flag):
        super().__init__()
        self.input_db = input_db
        self.output_db = output_db
        self.overwrite = overwrite
        self.cancel_flag = cancel_flag  

    def run(self):
        """Runs the data import in a separate thread and updates progress."""
        self.progress_updated.emit(0)
        QCoreApplication.processEvents()

        # ✅ Ensure the output database is initialized before processing
        initialize_database(self.output_db)

        conn_src = sqlite3.connect(self.input_db)
        conn_tgt = sqlite3.connect(self.output_db)
        src_cursor = conn_src.cursor()
        tgt_cursor = conn_tgt.cursor()

        self.progress_updated.emit(1)
        QCoreApplication.processEvents()

        # **SLOW OPERATION**: Counting total rows
        src_cursor.execute("SELECT COUNT(*) FROM Transfers WHERE Direction = 'Upload'")
        total_rows = src_cursor.fetchone()[0]

        self.progress_updated.emit(3)
        QCoreApplication.processEvents()

        if total_rows == 0:
            self.import_complete.emit(0, 0)
            return  # Nothing to process

        processed_rows = 0

        # **SLOW OPERATION**: Selecting all transfers
        src_cursor.execute("""
            SELECT Id, Username, Filename, Size, EndedAt, BytesTransferred, AverageSpeed, State
            FROM Transfers
            WHERE Direction = 'Upload' AND State LIKE 'Completed%' AND EndedAt IS NOT NULL
        """)

        self.progress_updated.emit(5)
        QCoreApplication.processEvents()

        transfers = []
        while True:
            batch = src_cursor.fetchmany(1000)
            if not batch or self.cancel_flag[0]:
                break

            transfers.extend(batch)
            processed_rows += len(batch)

            read_progress = 7 + int((processed_rows / total_rows) * 43)
            self.progress_updated.emit(min(read_progress, 50))
            QCoreApplication.processEvents()

        self.progress_updated.emit(50)
        QCoreApplication.processEvents()

        # ✅ Ensure the table exists before inserting data
        initialize_database(self.output_db)

        new_records, skipped_records = 0, 0
        processed_rows = 0  

        for i, transfer in enumerate(transfers):
            if self.cancel_flag[0]:  
                break  

            transfer_id, username, filename, size, ended_at, bytes_transferred, avg_speed, state = transfer
            artist = filename.split("/music/")[-1].split("/")[0] if "/music/" in filename else "Unknown"

            tgt_cursor.execute("SELECT COUNT(*) FROM UserTransfers WHERE Id = ?", (transfer_id,))
            if tgt_cursor.fetchone()[0] > 0:
                skipped_records += 1
            else:
                tgt_cursor.execute("""
                    INSERT INTO UserTransfers (Id, Username, Artist, Filename, Size, EndedAt, BytesTransferred, AverageSpeed, State)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (transfer_id, username, artist, filename, size, ended_at, bytes_transferred, avg_speed, state))
                new_records += 1

            processed_rows += 1

            write_progress = 50 + int((processed_rows / len(transfers)) * 50)
            self.progress_updated.emit(min(write_progress, 100))
            QCoreApplication.processEvents()

        conn_tgt.commit()
        conn_src.close()
        conn_tgt.close()

        if not self.cancel_flag[0]:
            self.import_complete.emit(new_records, skipped_records)

