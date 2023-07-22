import sys
import sqlite3
from hashlib import sha256
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QStackedLayout, QMainWindow, QToolBar,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog
)
from PyQt5.QtGui import QColor


# Create a SQLite database and connect to it
conn = sqlite3.connect('finance.db')
cursor = conn.cursor()

# Create the necessary tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        date DATE,
        category TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        category TEXT,
        amount REAL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        type TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        amount REAL
    )
''')

# Sample data for categories
cursor.execute('INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)', ('Bills', 'expense'))
cursor.execute('INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)', ('Groceries', 'expense'))
cursor.execute('INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)', ('Salary', 'income'))

# Close the database connection
conn.close()


class PersonalFinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Finance Manager')
        self.nav_class_map = {
            'Home': HomeScreen,
            'Add': AddScreen,
            'Stats': StatsScreen,
            'Budgets': BudgetsScreen,
            'Bills': BillsScreen,
            'Income': IncomeScreen,  # Add the IncomeScreen to the navigation
        }
        self.nav_index_map = {x[1]: x[0] for x in enumerate(self.nav_class_map.keys())}
        self.toolbar = QToolBar("Navigation")
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolbar)
        for key in self.nav_class_map.keys():
            self.toolbar.addAction(key).triggered.connect(self.on_click_method)
        self.toolbar.layout().setSpacing(50)

        self.initUI()


    def initUI(self):
        self.stackedLayout = QStackedLayout()
        for cls in self.nav_class_map.values():
            self.stackedLayout.addWidget(cls())

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.stackedLayout)

        central_widget = QWidget(self)
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def on_click_method(self):
        button_name = self.sender().text()
        self.stackedLayout.setCurrentIndex(self.nav_index_map[button_name])


class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.expenses = Expenses()
        self.bills = Bills()
        self.budgets = Budgets()

        label = QLabel('Expenses')
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(4)  # Update to 4 columns for id, category, amount, and date
        self.table_widget.setHorizontalHeaderLabels(["ID", "Category", "Amount", "Date"])  # Update header labels

        self.update_table()

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

    def update_table(self):
        self.table_widget.clearContents()
        expenses = self.expenses.get()
        self.table_widget.setRowCount(len(expenses))
        for row, (expense_id, category, amount, date) in enumerate(expenses):
            item_id = QTableWidgetItem(str(expense_id))  # Convert expense_id to string
            item_category = QTableWidgetItem(category)
            item_amount = QTableWidgetItem(str(amount))  # Convert amount to string
            item_date = QTableWidgetItem(date)
            self.table_widget.setItem(row, 0, item_id)
            self.table_widget.setItem(row, 1, item_category)
            self.table_widget.setItem(row, 2, item_amount)
            self.table_widget.setItem(row, 3, item_date)

            # Adding colorful background for better visibility
            if row % 2 == 0:
                item_id.setBackground(QColor(191, 235, 255))  # Light Blue
                item_category.setBackground(QColor(191, 235, 255))
                item_amount.setBackground(QColor(191, 235, 255))
                item_date.setBackground(QColor(191, 235, 255))
            else:
                item_id.setBackground(QColor(176, 224, 230))  # Powder Blue
                item_category.setBackground(QColor(176, 224, 230))
                item_amount.setBackground(QColor(176, 224, 230))
                item_date.setBackground(QColor(176, 224, 230))


class AddScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        label = QLabel('Add Expense')
        self.category_entry = QLineEdit()
        self.amount_entry = QLineEdit()
        self.date_entry = QLineEdit()

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_expense)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(QLabel('Category:'))
        layout.addWidget(self.category_entry)
        layout.addWidget(QLabel('Amount:'))
        layout.addWidget(self.amount_entry)
        layout.addWidget(QLabel('Date (YYYY-MM-DD):'))
        layout.addWidget(self.date_entry)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save_expense(self):
        category = self.category_entry.text()
        amount = self.amount_entry.text()
        date = self.date_entry.text()

        if not category or not amount or not date:
            QMessageBox.critical(self, 'Error', 'Please enter all fields.')
            return

        try:
            amount = float(amount)
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Invalid amount format.')
            return

        self.expenses = Expenses()
        self.expenses.add(category, amount, date)
        self.parent().parent().findChild(HomeScreen).update_table()
        self.category_entry.clear()
        self.amount_entry.clear()
        self.date_entry.clear()


class StatsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        label = QLabel('Statistics')
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class IncomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        label = QLabel('Add Income')
        self.income_entry = QLineEdit()

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_income)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(QLabel('Income Amount:'))
        layout.addWidget(self.income_entry)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save_income(self):
        income_amount = self.income_entry.text()

        if not income_amount:
            QMessageBox.critical(self, 'Error', 'Please enter the income amount.')
            return

        try:
            income_amount = float(income_amount)
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Invalid income amount format.')
            return

        self.budgets = Budgets()
        self.budgets.add('Income', income_amount)  # Add the income as a budget under 'Income' category
        self.update_budgets()
        self.income_entry.clear()

    def update_budgets(self):
        # Fetch the budgets again and update the table
        budgets = self.budgets.get_budgets()
        self.parent().parent().findChild(BudgetsScreen).update_budgets(budgets)


class BudgetsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.budgets = Budgets()

        label = QLabel('Budgets')
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Category", "Budget Amount", "Remaining Amount"])

        self.update_budgets()

        add_button = QPushButton('Add Budget')
        add_button.clicked.connect(self.add_budget)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.table_widget)
        layout.addWidget(add_button)
        self.setLayout(layout)

    def update_budgets(self, budgets=None):
        if budgets is None:
            budgets = self.budgets.get_budgets()

        self.table_widget.clearContents()
        self.table_widget.setRowCount(len(budgets))
        for row, (category, budget_amount) in enumerate(budgets):
            remaining_amount = self.budgets.get_remaining_amount(category)
            item_category = QTableWidgetItem(category)
            item_budget_amount = QTableWidgetItem(str(budget_amount))
            item_remaining_amount = QTableWidgetItem(str(remaining_amount))
            self.table_widget.setItem(row, 0, item_category)
            self.table_widget.setItem(row, 1, item_budget_amount)
            self.table_widget.setItem(row, 2, item_remaining_amount)

            # Adding colorful background for better visibility
            if row % 2 == 0:
                item_category.setBackground(QColor(191, 235, 255))  # Light Blue
                item_budget_amount.setBackground(QColor(191, 235, 255))
                item_remaining_amount.setBackground(QColor(191, 235, 255))
            else:
                item_category.setBackground(QColor(176, 224, 230))  # Powder Blue
                item_budget_amount.setBackground(QColor(176, 224, 230))
                item_remaining_amount.setBackground(QColor(176, 224, 230))

    def add_budget(self):
        category, ok = QInputDialog.getText(self, 'Add Budget', 'Enter the budget category:')
        if ok and category:
            amount, ok = QInputDialog.getDouble(self, 'Add Budget', 'Enter the budget amount:')
            if ok:
                self.budgets.add(category, amount)
                self.update_budgets()


class BillsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.bills = Bills()

        label = QLabel('Bills')
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Name", "Amount", "Actions"])

        self.update_table()

        add_button = QPushButton('Add Bill')
        add_button.clicked.connect(self.add_bill)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.table_widget)
        layout.addWidget(add_button)
        self.setLayout(layout)

    def update_table(self):
        self.table_widget.clearContents()
        bills = self.bills.get_bills()
        self.table_widget.setRowCount(len(bills))
        for row, (name, amount) in enumerate(bills):
            item_name = QTableWidgetItem(name)
            item_amount = QTableWidgetItem(str(amount))
            self.table_widget.setItem(row, 0, item_name)
            self.table_widget.setItem(row, 1, item_amount)

            # Adding colorful background for better visibility
            if row % 2 == 0:
                item_name.setBackground(QColor(191, 235, 255))  # Light Blue
                item_amount.setBackground(QColor(191, 235, 255))
            else:
                item_name.setBackground(QColor(176, 224, 230))  # Powder Blue
                item_amount.setBackground(QColor(176, 224, 230))

            # Adding delete button as an action for each row
            delete_button = QPushButton('Delete')
            delete_button.clicked.connect(lambda _, name=name: self.delete_bill(name))
            self.table_widget.setCellWidget(row, 2, delete_button)

    def add_bill(self):
        name, ok = QInputDialog.getText(self, 'Add Bill', 'Enter the bill name:')
        if ok and name:
            amount, ok = QInputDialog.getDouble(self, 'Add Bill', 'Enter the bill amount:')
            if ok:
                self.bills.add(name, amount)
                self.update_table()

    def delete_bill(self, name):
        reply = QMessageBox.question(self, 'Delete Bill', f"Are you sure you want to delete '{name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.bills.delete(name)
            self.update_table()
            QMessageBox.information(self, 'Delete Bill', f"'{name}' has been deleted.")

class Bills:
    def __init__(self, db_file='finance.db'):
        self.db_file = db_file

    def add(self, name, amount):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bills (name, amount) VALUES (?, ?)', (name, amount))
        conn.commit()
        conn.close()

    def delete(self, name):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bills WHERE name=?', (name,))
        conn.commit()
        conn.close()

    def update(self, name, amount):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('UPDATE bills SET amount=? WHERE name=?', (amount, name))
        conn.commit()
        conn.close()

    def get_bills(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT name, amount FROM bills')
        bills = cursor.fetchall()
        conn.close()
        return bills


class Budgets:
    def __init__(self, db_file='finance.db'):
        self.db_file = db_file

    def add(self, category, amount):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO budgets (category, amount) VALUES (?, ?)', (category, amount))
        conn.commit()
        conn.close()

    def delete(self, category):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM budgets WHERE category=?', (category,))
        conn.commit()
        conn.close()

    def update(self, category, amount):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('UPDATE budgets SET amount=? WHERE category=?', (amount, category))
        conn.commit()
        conn.close()

    def get_budgets(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT category, amount FROM budgets')
        budgets = cursor.fetchall()
        conn.close()
        return budgets
    
    
    def get_remaining_amount(self, category):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT amount FROM budgets WHERE category=?', (category,))
        budget_amount = cursor.fetchone()
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE category=?', (category,))
        total_expenses = cursor.fetchone()
        conn.close()

        budget_amount = budget_amount[0] if budget_amount and budget_amount[0] is not None else 0.0
        total_expenses = total_expenses[0] if total_expenses and total_expenses[0] is not None else 0.0

        remaining_amount = budget_amount - total_expenses
        return remaining_amount


class Expenses:
    def __init__(self, db_file='finance.db'):
        self.db_file = db_file

    def add(self, category, amount, date):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)', (category, amount, date))
        conn.commit()
        conn.close()

    def delete(self, expense_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
        conn.commit()
        conn.close()

    def update(self, expense_id, category, amount, date):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('UPDATE expenses SET category=?, amount=?, date=? WHERE id=?', (category, amount, date, expense_id))
        conn.commit()
        conn.close()

    def get(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT id, category, amount, date FROM expenses')
        expenses = cursor.fetchall()
        conn.close()
        return expenses



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PersonalFinanceApp()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())
