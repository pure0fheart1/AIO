import sys
import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QListWidget, QListWidgetItem, QMessageBox, 
                            QFormLayout, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt

class ContactDialog(QDialog):
    def __init__(self, contact=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Contact" if contact is None else "Edit Contact")
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        self.name_input = QLineEdit(contact['name'] if contact else "")
        self.email_input = QLineEdit(contact['email'] if contact else "")
        self.phone_input = QLineEdit(contact['phone'] if contact else "")
        
        self.form_layout.addRow("Name:", self.name_input)
        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Phone:", self.phone_input)
        
        self.layout.addLayout(self.form_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout.addWidget(self.button_box)

    def get_contact_data(self):
        return {
            "name": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip()
        }

class ContactsManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.contacts = []
        self.contacts_file = "contacts.json" 
        self.setup_ui()
        self.load_contacts()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left panel: List of contacts
        left_panel = QVBoxLayout()
        self.contact_list_widget = QListWidget()
        self.contact_list_widget.currentItemChanged.connect(self.display_contact_details)
        
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        
        self.add_button.clicked.connect(self.add_contact)
        self.edit_button.clicked.connect(self.edit_contact)
        self.delete_button.clicked.connect(self.delete_contact)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        
        left_panel.addWidget(QLabel("Contacts:"))
        left_panel.addWidget(self.contact_list_widget)
        left_panel.addLayout(button_layout)
        
        # Right panel: Contact details (initially empty)
        right_panel = QVBoxLayout()
        self.details_label = QLabel("Select a contact to view details.")
        self.details_label.setAlignment(Qt.AlignTop)
        right_panel.addWidget(self.details_label)
        
        main_layout.addLayout(left_panel, 1) # Give list more space
        main_layout.addLayout(right_panel, 1)

    def load_contacts(self):
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, 'r') as f:
                    self.contacts = json.load(f)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Load Error", f"Could not load contacts from {self.contacts_file}. File might be corrupted.")
                self.contacts = []
            except Exception as e:
                 QMessageBox.critical(self, "Load Error", f"An unexpected error occurred loading contacts: {e}")
                 self.contacts = []
        else:
            self.contacts = [] # Start fresh if no file exists
        self.refresh_contact_list()

    def save_contacts(self):
        try:
            with open(self.contacts_file, 'w') as f:
                json.dump(self.contacts, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save contacts to {self.contacts_file}: {e}")

    def refresh_contact_list(self):
        self.contact_list_widget.clear()
        for i, contact in enumerate(self.contacts):
            item = QListWidgetItem(contact.get('name', 'Unnamed Contact'))
            item.setData(Qt.UserRole, i) # Store index in the item's data
            self.contact_list_widget.addItem(item)
        self.display_contact_details(None) # Clear details panel

    def display_contact_details(self, current_item, previous_item=None):
        # The previous_item argument is provided by the signal but not needed here.
        if current_item:
            index = current_item.data(Qt.UserRole)
            if 0 <= index < len(self.contacts):
                contact = self.contacts[index]
                details_text = f"<b>Name:</b> {contact.get('name', '')}<br>" \
                               f"<b>Email:</b> {contact.get('email', '')}<br>" \
                               f"<b>Phone:</b> {contact.get('phone', '')}"
                self.details_label.setText(details_text)
                self.edit_button.setEnabled(True)
                self.delete_button.setEnabled(True)
            else:
                 # Index out of bounds, should not happen ideally
                 self.details_label.setText("Error: Invalid contact selected.")
                 self.edit_button.setEnabled(False)
                 self.delete_button.setEnabled(False)
        else:
            self.details_label.setText("Select a contact to view details.")
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    def add_contact(self):
        dialog = ContactDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_contact_data = dialog.get_contact_data()
            if not new_contact_data['name']:
                 QMessageBox.warning(self, "Input Error", "Contact name cannot be empty.")
                 return
            self.contacts.append(new_contact_data)
            self.save_contacts()
            self.refresh_contact_list()
            # Select the newly added contact
            self.contact_list_widget.setCurrentRow(len(self.contacts) - 1)


    def edit_contact(self):
        current_item = self.contact_list_widget.currentItem()
        if not current_item:
            return
            
        index = current_item.data(Qt.UserRole)
        if not (0 <= index < len(self.contacts)):
             QMessageBox.critical(self, "Error", "Invalid contact index selected for editing.")
             return

        contact_to_edit = self.contacts[index]
        
        dialog = ContactDialog(contact=contact_to_edit, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_contact_data = dialog.get_contact_data()
            if not updated_contact_data['name']:
                 QMessageBox.warning(self, "Input Error", "Contact name cannot be empty.")
                 return
            self.contacts[index] = updated_contact_data
            self.save_contacts()
            self.refresh_contact_list()
            # Re-select the edited item
            self.contact_list_widget.setCurrentRow(index)


    def delete_contact(self):
        current_item = self.contact_list_widget.currentItem()
        if not current_item:
            return

        index = current_item.data(Qt.UserRole)
        if not (0 <= index < len(self.contacts)):
             QMessageBox.critical(self, "Error", "Invalid contact index selected for deletion.")
             return
             
        contact_name = self.contacts[index].get('name', 'this contact')
        reply = QMessageBox.question(self, 'Delete Contact', 
                                     f"Are you sure you want to delete '{contact_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.contacts[index]
            self.save_contacts()
            self.refresh_contact_list()

# Example usage (for testing standalone)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    contacts_widget = ContactsManager()
    contacts_widget.setWindowTitle('Contacts Manager Test')
    contacts_widget.setGeometry(100, 100, 600, 400)
    contacts_widget.show()
    sys.exit(app.exec_()) 