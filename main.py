import sys
import os
import math
import base64
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QDialog, QPushButton, 
    QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,  QFileDialog,
    QDateEdit, QToolButton, QComboBox, QDoubleSpinBox, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsProxyWidget, QFrame, 
    QGridLayout, QGroupBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QSizePolicy, QListWidgetItem, QScrollArea, QListWidget, QMessageBox)

from PyQt5.QtGui import QPixmap,QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QDate, QPointF,QByteArray, QBuffer, QIODevice, pyqtSignal
from prints import PrintExportDialog, QuotationPreviewDialog, JobWorkPreviewDialog, CuttingJobPreviewDialog, PrintingJobPreviewDialog, RibCollarPrintDialog

MEDIA_ROOT = os.path.join(os.getcwd(), 'media')  # The main folder
TEMPLATE_DIR = os.path.join(MEDIA_ROOT, 'templates') # For blank shirt images (ComboBox source)
REFERENCE_DIR = os.path.join(MEDIA_ROOT, 'references') # For customer-uploaded photos (Gallery source) 

class ImageGalleryWindow(QDialog):
    image_selected = pyqtSignal(str)
    def __init__(self, media_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Uploaded Image Gallery")
        self.media_dir = media_dir  # Store the path for load_images()
        self.setGeometry(100, 100, 800, 600)
        
        main_layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_widget)
        scroll_area.setWidget(self.gallery_widget)
        
        self.load_images()
    
    def load_images(self):
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
        col_count = 4 
        row, col = 0, 0

        if not os.path.isdir(self.media_dir):
            self.gallery_layout.addWidget(QLabel("Error: Reference directory not found."), 0, 0)
            return

        for filename in os.listdir(self.media_dir):
            if filename.lower().endswith(image_extensions):
                image_path = os.path.join(self.media_dir, filename)                

                label = QLabel()
                pixmap = QPixmap(image_path)
                if pixmap.isNull():
                    continue

                scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.setToolTip(filename)
                
                # Click event for selecting the image
                label.mousePressEvent = lambda event, path=image_path: self._image_clicked(path)
                label.setCursor(Qt.PointingHandCursor)
                
                # 2. Icon Bar Widget (The overlay)
                icon_bar = QWidget()
                icon_layout = QHBoxLayout(icon_bar)
                icon_layout.setContentsMargins(0, 0, 5, 5) 
                icon_layout.setSpacing(2)
                
                # 🗑️ Delete Button
                delete_btn = QPushButton("🗑️")
                delete_btn.setStyleSheet("background-color: rgba(255, 255, 255, 180); border: 1px solid #AAA; border-radius: 10px; font-size: 14px; padding: 0;") 
                delete_btn.setFixedSize(30, 30) 
                delete_btn.setToolTip(f"Delete {filename}")
                delete_btn.clicked.connect(lambda checked, path=image_path: self._delete_image(path))
                
                # ⬇️ Download Button
                download_btn = QPushButton("⬇️") 
                download_btn.setStyleSheet("background-color: rgba(255, 255, 255, 180); border: 1px solid #AAA; border-radius: 10px; font-size: 14px; padding: 0;") 
                download_btn.setFixedSize(30, 30) 
                download_btn.setToolTip(f"Download {filename}")
                download_btn.clicked.connect(lambda checked, path=image_path: self._download_image(path))

                icon_layout.addStretch()
                icon_layout.addWidget(download_btn)
                icon_layout.addWidget(delete_btn)
                
                image_wrapper = QWidget() 
                wrapper_layout = QGridLayout(image_wrapper)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                wrapper_layout.setSpacing(0)
                wrapper_layout.addWidget(label, 0, 0)                
                wrapper_layout.addWidget(icon_bar, 0, 0, Qt.AlignTop | Qt.AlignRight) 
                image_wrapper.setFixedSize(scaled_pixmap.width(), scaled_pixmap.height())
                self.gallery_layout.addWidget(image_wrapper, row, col)
                                
                col += 1
                if col >= col_count:
                    col = 0
                    row += 1

    def _image_clicked(self, path):
        absolute_path = os.path.abspath(path) 
    
        self.image_selected.emit(absolute_path) # Emit the absolute path
        self.accept()

class ItemInputDialog(QDialog):
    def __init__(self, parent=None, is_view_only=False):
        super().__init__(parent)
        self.is_view_only = is_view_only 
        self.setWindowTitle("Add New Item")

        self.setMinimumSize(1820, 350) 
        
        # Main layout is Vertical
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        
        # --- Helper function for label + widget (re-used logic) ---
        def create_field_layout(label_text, widget, input_width=120):
            field_layout = QHBoxLayout()
            field_layout.setSpacing(5)
            field_layout.setContentsMargins(0, 0, 0, 0)
            
            lbl = QLabel(label_text)
            lbl.setFixedWidth(65) # Fixed label width for alignment
            widget.setFixedWidth(input_width) # Fixed widget width

            widget.setStyleSheet("""
                QLineEdit, QComboBox {
                    border: 1px solid #000000; /* Solid Black Border */
                    border-radius: 0px;      /* Sharp corners */
                    padding: 2px;
                }
            """)
            
            field_layout.addWidget(lbl)
            field_layout.addWidget(widget)
            
            container = QWidget()
            container.setLayout(field_layout)
            return container # Return the widget container
            
        # --- Row 1 Layout (Horizontal) ---
        single_row_layout = QHBoxLayout()
        single_row_layout.setSpacing(30)
        
        # Fabric
        self.cloth_combo = QComboBox()
        self.cloth_combo.addItems(["Cotton", "Platted", "Jabro"])
        single_row_layout.addWidget(create_field_layout("Fabric:", self.cloth_combo))
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["T-shirt", "Track-pant", "Shorts"])
        single_row_layout.addWidget(create_field_layout("Type:", self.type_combo))

        # Color
        self.color_input = QLineEdit("red")
        single_row_layout.addWidget(create_field_layout("Color:", self.color_input, 100))
        
        # Size
        self.size_combo = QComboBox()
        self.size_combo.addItems(["S", "M", "L", "XL", "XXL"])
        single_row_layout.addWidget(create_field_layout("Size:", self.size_combo, 70))

        # 5. Quantity
        self.qty_input = QLineEdit("1")
        single_row_layout.addWidget(create_field_layout("QTY:", self.qty_input, 70)) # Smaller width
        
        # 6. Unit Price
        self.price_input = QLineEdit("200")
        single_row_layout.addWidget(create_field_layout("Unit Price:", self.price_input, 80)) # Smaller width
        
        # 7. Status Field
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pending", "Cutting", "Stretching", "Printing", "Completed"])
        single_row_layout.addWidget(create_field_layout("Status:", self.status_combo, 120))

        # 8. Barcode Field
        self.barcode_input = QLineEdit()
        barcode_field_widget = create_field_layout("Barcode:", self.barcode_input, 150)
        single_row_layout.addWidget(barcode_field_widget)

        # 9. Barcode Save Button
        self.barcode_save_btn = QPushButton("Save Barcode")
        self.barcode_save_btn.setFixedWidth(150) # Adjust width as needed
        self.barcode_save_btn.setStyleSheet("background-color: #CCCCFF;") # Give it a unique look
        #self.barcode_save_btn.hide()

        barcode_btn_layout = QHBoxLayout()
        barcode_btn_layout.setContentsMargins(0, 0, 0, 0)
        barcode_btn_layout.addWidget(self.barcode_save_btn)
        barcode_btn_container = QWidget()
        barcode_btn_container.setLayout(barcode_btn_layout)
        single_row_layout.addWidget(barcode_btn_container)

        single_row_layout.addStretch(1) # Pushes everything to the left
        self.main_layout.addLayout(single_row_layout)

        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText("Enter item-specific remark...")
        self.remark_input.setMinimumWidth(800) # Give it enough space
        self.remark_input.setStyleSheet("QLineEdit { border: 1px solid black; border-radius: 0px; padding: 4px 6px; }")

        remark_label = QLabel("Remark:")
        remark_label.setFixedWidth(70)
        remark_label.setStyleSheet("font-weight: bold;")
        
        remark_container_layout = QHBoxLayout()
        remark_container_layout.setContentsMargins(0, 0, 0, 0)
        remark_container_layout.addWidget(remark_label)
        remark_container_layout.addWidget(self.remark_input)
        remark_container_layout.addStretch(1)

        self.main_layout.addSpacing(15)
        self.main_layout.addLayout(remark_container_layout)

        if self.is_view_only:
            # Layout to hold the new action buttons
            action_buttons_layout = QHBoxLayout()
            action_buttons_layout.setSpacing(10)
            
            # Create the buttons (as instance attributes)
            self.job_btn = QPushButton("⚒️ STRETCHING")
            self.cut_btn = QPushButton("✂️ CUTTING")
            self.print_btn = QPushButton("🖨 PRINTING")
            
            for btn in [self.job_btn, self.cut_btn, self.print_btn]:
                btn.setFixedHeight(40)
                btn.setFixedWidth(150)
                btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #CCCCFF; 
                        font-weight: bold; 
                        border: 1px solid #000000;
                    }
                    QPushButton:hover {
                        background-color: #AAAAEE;
                    }
                """)
                action_buttons_layout.addWidget(btn)

            action_buttons_layout.addStretch(1) # Push buttons to the left

            # Add spacing above the new buttons and add the layout
            self.main_layout.addSpacing(25) 
            self.main_layout.addLayout(action_buttons_layout)
            self.main_layout.addStretch(1) # Final stretch to push everything up
            self.job_btn.clicked.connect(self._open_job_work_dialog)
            self.cut_btn.clicked.connect(self._open_cutting_dialog)

        if not self.is_view_only:
            self.main_layout.addSpacing(5)
            
            self.main_layout.addSpacing(20)
            self.done_button = QPushButton("Done")
            self.done_button.setFixedWidth(120)

            self.done_button.setStyleSheet("""
                QPushButton {
                    border: 1px solid #000000; 
                    border-radius: 0px;
                    padding: 5px; 
                    background-color: #f0f0f0; 
                }
                QPushButton:hover {
                    background-color: #e0e0e0; 
                }
            """)
            self.done_button.clicked.connect(self.accept) 
            
            done_layout = QHBoxLayout()
            done_layout.addStretch(1) # Push button to the right
            done_layout.addWidget(self.done_button)
            done_layout.addStretch(1) # Center the button

            self.main_layout.addLayout(done_layout)
        
    # Method to easily retrieve all data (Remains the same)
    def get_data(self):
        return {
            "Fabric": self.cloth_combo.currentText(),
            "Type": self.type_combo.currentText(),
            "Color": self.color_input.text(),
            "Size": self.size_combo.currentText(),
            "Qty": self.qty_input.text(),
            "Unit": self.price_input.text(),
            "Status": self.status_combo.currentText(),
            "Barcode": self.barcode_input.text(),
            "Remark": self.remark_input.text()
        }
    
    def _open_job_work_dialog(self):
        
        item_data = self.get_data() 
        try:
            quantity = float(item_data['Qty'])
            unit_price = float(item_data['Unit'])
            total_price = quantity * unit_price
        except ValueError:
            QMessageBox.warning(self, "Invalid Data", "Quantity and Unit Price must be valid numbers.")
            return

        product_details = f"{item_data['Fabric']} {item_data['Type']} ({item_data['Color']})"
        html_content = f"""
        <table style="width:100%; border-collapse: collapse;" class="item-table">
            <thead>
                <tr>
                    <th style="border: 1px solid #ddd;">Fabric</th>
                    <th style="border: 1px solid #ddd;">Type</th>
                    <th style="border: 1px solid #ddd;">Color</th>
                    <th style="border: 1px solid #ddd;">Size</th>
                    <th style="border: 1px solid #ddd;">Quantity</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd;">{item_data['Fabric']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Type']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Color']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Size']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Qty']}</td>
                </tr>
            </tbody>
        </table>
        """
        try:
            dialog = JobWorkPreviewDialog(self.parent(), html_content)
            dialog.exec()
        except NameError:
            QMessageBox.critical(self, "Error", "JobWorkPreviewDialog class not found. Ensure 'from prints import JobWorkPreviewDialog' is correct.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not launch Job Work Dialog: {e}")

    def _open_cutting_dialog(self):
        item_data = self.get_data() 
        
        try:
            quantity = float(item_data['Qty'])
        except ValueError:
            QMessageBox.warning(self, "Invalid Data", "Quantity and Unit Price must be valid numbers.")
            return

        html_content = f"""
        <table style="width:100%; border-collapse: collapse;" class="item-table">
            <thead>
                <tr>
                    <th style="border: 1px solid #ddd;">Fabric</th>
                    <th style="border: 1px solid #ddd;">Type</th>
                    <th style="border: 1px solid #ddd;">Color</th>
                    <th style="border: 1px solid #ddd;">Size</th>
                    <th style="border: 1px solid #ddd;">Quantity</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd;">{item_data['Fabric']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Type']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Color']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Size']}</td>
                    <td style="border: 1px solid #ddd;">{item_data['Qty']}</td>
                </tr>
            </tbody>
        </table>
        """
        
        try:
            dialog = CuttingJobPreviewDialog(self.parent(), html_content) 
            dialog.exec()
        except NameError:
            QMessageBox.critical(self, "Error", "CuttingJobPreviewDialog class not found. Check imports.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not launch Cutting Dialog: {e}")

    def _open_printing_dialog(self):
        item_data = self.get_data() 

        html_content = f"""
        <table style="width:100%; border-collapse: collapse;" class="item-table">
            <thead>
                <tr>
                    <th style="border: 1px solid #ddd;">Remark</th> 
                    </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd;">{item_data['Remark']}</td>
                </tr>
            </tbody>
        </table>
        """
        try:
            dialog = PrintingJobPreviewDialog(self.parent(), html_content) 
            dialog.exec()
        except NameError:
            QMessageBox.critical(self, "Error", "PrintingJobPreviewDialog class not found. Check imports.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not launch Printing Dialog: {e}")
            
class EmployeeDetailsDialog(QDialog):
    def __init__(self, item_type, current_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Employee Details")
        self.setMinimumSize(700, 350) 
        
        # Determine which fields are relevant based on item type
        # Assuming only T-Shirts need Printing and Collar details
        # Assuming only Track-Pants/Shorts need Stretching details
        self.item_type = item_type.lower()
        
        # Use existing data if editing, otherwise default to empty strings
        self.current_data = current_data if current_data is not None else {}
        
        main_layout = QVBoxLayout(self)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

        # --- Helper for fields ---
        def add_field(label_text, key, is_mandatory=True):
            h_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(200)
            
            # Use QComboBox for a few options or QLineEdit if names are free-form
            # We'll use QLineEdit for simplicity here, but QComboBox is better for fixed staff lists
            line_edit = QLineEdit(self.current_data.get(key, ""))
            line_edit.setPlaceholderText(f"Enter {label_text}")
            setattr(self, key.replace(" ", "_").lower() + "_input", line_edit)
            
            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)
            form_layout.addLayout(h_layout)
            return line_edit
            
        # 1. Cutting Employee (Always required)
        self.cutting_employee_input = add_field("Cutting Employee:", "Cutting Employee Name")
        
        # 2. Printing Employee (T-Shirt Specific, but generally included)
        self.printing_employee_input = add_field("Printing Employee:", "Printing Employee Name")
        
        # 3. RIB Collar Employee (T-Shirt Specific, but generally included)
        self.collar_employee_input = add_field("RIB Collar Employee:", "RIB Collar Employee Name")
        
        # 4. Stretching Employee (Often Pant/Short Specific, but generally included)
        self.stretching_employee_input = add_field("Stretching Employee:", "Stretching Employee Name")
        
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(20)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)
        
        main_layout.addLayout(button_layout)
        
    def get_employee_data(self):
        """Returns the data collected in this dialog."""
        return {
            "Cutting Employee Name": self.cutting_employee_input.text(),
            "Printing Employee Name": self.printing_employee_input.text(),
            "RIB Collar Employee Name": self.collar_employee_input.text(),
            "Stretching Employee Name": self.stretching_employee_input.text()
        }

class OrderForm(QWidget):
    REFERENCE_DIR = globals().get('REFERENCE_DIR')
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Order Form")
        self.setStyleSheet("background-color: #F5FFFA")
        self.reference_image_paths = []
        self.current_reference_image_path = None
    
        # ✅ सबसे पहले image और बाकी variables init करो
        self.image = None
        self.scene = None
        self.canvas = None
        self.entries = {}
        self._canvas_image_item = None
        self._total_items_sum = 0.0
        self._tax_percentage = 0.0
        self._tax_amount = 0.0
        self._grand_total = 0.0
        self.item_collar_flags = []

        # 🔹 Main vertical layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)

        # Toolbar
        toolbar = self.main_toolbar()
        self.main_layout.addWidget(toolbar, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Header
        header = self.header()
        self.main_layout.addWidget(header, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Product + Image Panel
        product_panel = self._product_and_image_panel()
        self.main_layout.addWidget(product_panel, alignment=Qt.AlignLeft | Qt.AlignTop)

       
        # Pehla row add karte hi dikhega
        item_box=self.create_item_selection_box()
        self.main_layout.addWidget(item_box)

        self.setup_tax_and_remark_fields()
      
        self.main_layout.addLayout(self.create_buttons_row())
        # Add row panel first

        self.main_layout.addStretch()

    def open_gallery(self):
        self.image_gallery_window = ImageGalleryWindow(self.REFERENCE_DIR, parent=self)
        
        self.image_gallery_window.image_selected.connect(self._set_current_reference_image) 
        
        result = self.image_gallery_window.exec_()
        
        if result == QDialog.Accepted and self.current_reference_image_path:
            print("Gallery closed. Path successfully set. Ready for quotation.")            
            self.generate_quotation_preview()

    def _get_reference_images_base64(self): # RENAMED FUNCTION
        base64_uris = []
        
        # --- ITERATE OVER THE LIST OF PATHS ---
        for path in self.reference_image_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        ext = os.path.splitext(path)[1].lower()
                        mime = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                        base64_uris.append(f"data:{mime};base64,{encoded_string}")
                except Exception as e:
                    print(f"Error converting reference image to base64: {e}") 
        # ---------------------------------------  
        return base64_uris # Returns a list of URI strings
        
    def _set_current_reference_image(self, image_path):
        self.current_reference_image_path = image_path 
        print(f"Reference image path set to: {self.current_reference_image_path}")

    def create_button(self, text, emoji, shortcut=None, size=(80, 80)):
        """ Helper to create styled buttons with emoji as icon (top) """
        btn = QToolButton()
        btn.setText(f"{emoji}\n{text}")   # Icon ऊपर, text नीचे
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setFixedSize(*size)

        # Shortcut
        if shortcut:
            btn.setShortcut(shortcut)

        # Styling
        btn.setStyleSheet("""
            QToolButton {
                background-color: #EEEEEE;
                color: #fc83a0;
                font-weight: bold;
                border: 1px solid #CCCCCC;
            }
            QToolButton:hover {
                background-color: #fc83a0;
                color: white;
            }
        """)
        return btn

    def main_toolbar(self):
        """
        Top panel with action buttons (NEW, EDIT, DELETE, SEARCH, etc.)
        """
        button_group = QWidget()

        # 🔹 Main horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(0)

        # 🔹 Sub-layout 1 (NEW/EDIT/DELETE/SEARCH – chipake)
        left_layout = QHBoxLayout()
        left_layout.setSpacing(1)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 🔹 Sub-layout 2 (TOP/BACK/NEXT/LAST – chipake)
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(1)
        mid_layout.setContentsMargins(0, 0, 0, 0)

        # 🔹 Sub-layout 3 (EXIT/TUTOR – chipake)
        right_layout = QHBoxLayout()
        right_layout.setSpacing(1)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Buttons with shortcuts
        self.new_btn = QPushButton("📄\n New-Ctrl+N");    self.new_btn.setShortcut("Ctrl+N")
        self.edit_btn = QPushButton("📝\n Modify-Ctrl+O");  self.edit_btn.setShortcut("Ctrl+E")
        self.delete_btn = QPushButton("🗑️\n Delete"); self.delete_btn.setShortcut("Ctrl+D")
        self.search_btn = QPushButton("🔍\n Search-Ctrl+F"); self.search_btn.setShortcut("Ctrl+F")
        self.search_btn.clicked.connect(self.open_search_window)
        self.print_btn = QPushButton("🖨\n Print-Ctrl+P"); self.print_btn.setShortcut("Ctrl+P")

        self.top_btn = QPushButton("▲\n Top")
        self.back_btn = QPushButton("◀\n Back");  self.back_btn.setShortcut("Alt+Left")
        self.next_btn = QPushButton("▶\n Next");  self.next_btn.setShortcut("Alt+Right")
        self.last_btn = QPushButton("▼\n Last")

        self.exit_btn = QPushButton("↩️\n Exit-Alt+F4");  self.exit_btn.setShortcut("Alt+F4")
        self.tutor_btn = QPushButton("❔\n TUTOR")
        self.upload_btn=QPushButton("Upload")
        self.previous_btn=QPushButton("previous")

       #Connections 

        self.upload_btn.clicked.connect(self._upload_reference_image) 
        self.previous_btn.clicked.connect(self._open_image_gallery) 
        self.print_btn.clicked.connect(self.open_print_dialog)
       # Common style
        button_style = """
            background-color: #EEEEEE; 
            color: #fc83a0; 
            font-weight: bold; 
            padding: 10px;
        """
        all_buttons = [
            self.new_btn, self.edit_btn, self.delete_btn, self.search_btn, self.print_btn,
            self.top_btn, self.back_btn, self.next_btn, self.last_btn,
            self.exit_btn, self.tutor_btn,self.upload_btn,self.previous_btn
        ]
        for btn in all_buttons:
            btn.setStyleSheet(button_style)

        # 🔹 Group 1 (left buttons)
        for btn in [self.new_btn, self.edit_btn, self.delete_btn, self.search_btn, self.print_btn]:
            btn.setFixedSize(150, 70)
            left_layout.addWidget(btn)

        # 🔹 Group 2 (mid buttons)
        for btn in [self.top_btn, self.back_btn, self.next_btn, self.last_btn]:
            btn.setFixedSize(80, 70)
            mid_layout.addWidget(btn)

        # 🔹 Group 3 (right buttons)
        for btn in [self.exit_btn, self.tutor_btn,self.upload_btn,self.previous_btn]:
            # btn.setFixedSize(150, 70)
            # right_layout.addWidget(btn)
            if btn in [self.upload_btn, self.previous_btn]:
                btn.setFixedSize(150, 40)  # height kam
            else:
                btn.setFixedSize(150, 70)  # normal height
            right_layout.addWidget(btn)

            if btn==self.tutor_btn:
                right_layout.addSpacing(20)

        # 🔹 Add layouts to main layout with spacing only between groups
        button_layout.addLayout(left_layout)
        button_layout.addSpacing(20)   # left & mid gap
        button_layout.addLayout(mid_layout)
        button_layout.addSpacing(20)   # mid & right gap
        button_layout.addLayout(right_layout)

        button_group.setLayout(button_layout)
        return button_group

    def header(self, parties=None):
        container = QWidget()
        main_layout = QVBoxLayout(container)

        button_style = """
            background-color: #EEEEEE; 
            color: #fc83a0; 
            font-weight: bold; 
            padding: 10px;
        """

        # ---------- 1st Row ----------
        row1 = QHBoxLayout()
        self.order_number = QLineEdit()
        self.order_number.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
      
        self.order_date = QDateEdit()
        self.order_date.setCalendarPopup(True)
        self.order_date.setDisplayFormat("dd-MM-yyyy")
        self.order_date.setDate(QDate.currentDate())
        self.order_date.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        
       
        self.delivery_date = QDateEdit()
        self.delivery_date.setCalendarPopup(True)
        self.delivery_date.setDisplayFormat("dd-MM-yyyy")
        self.delivery_date.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        
        
        self.barcode_number = QLineEdit()
        self.barcode_number.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        self.save_barcode_btn = QPushButton("Save Barcode")
        self.save_barcode_btn.setStyleSheet(button_style)
        
        self.gst_no = QLineEdit()
        self.gst_no.setFixedSize(200,30)
        self.gst_no.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        
        self.advance_paid = QDoubleSpinBox()
        self.advance_paid.setPrefix("₹ ")
        self.advance_paid.setMaximum(9999999)
        self.advance_paid.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")


        row1.addWidget(QLabel("Order No:"))
        row1.addWidget(self.order_number)
        row1.addWidget(QLabel("Order Date:"))
        row1.addWidget(self.order_date)
        row1.addWidget(QLabel("Delivery Date:"))
        row1.addWidget(self.delivery_date)
        row1.addWidget(QLabel("Barcode:"))
        row1.addWidget(self.barcode_number)
        row1.addWidget(self.save_barcode_btn)
        row1.addWidget(QLabel("GST No:"))
        row1.addWidget(self.gst_no)
        row1.addWidget(QLabel("Advance Paid:"))
        row1.addWidget(self.advance_paid)

        # ---------- 2nd Row ----------
        row2 = QHBoxLayout()
        self.party_name = QLineEdit()
        if parties:
            self.party_name.addItems(parties)
        self.party_name.setFixedSize(250,30)
        self.party_name.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        self.school_name = QLineEdit()
        self.school_name.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        # self.gst_no = QLineEdit()
        # self.gst_no.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        self.address = QLineEdit()
        self.address.setStyleSheet("background-color: white; border: 1px solid gray; padding: 3px;")
        self.address.setFixedHeight(30)

        row2.addWidget(QLabel("Party Name:"))
        row2.addWidget(self.party_name)
        row2.addWidget(QLabel("School Name:"))
        row2.addWidget(self.school_name)
        # row2.addWidget(QLabel("GST No:"))
        # row2.addWidget(self.gst_no)
        row2.addWidget(QLabel("Address:"))
        row2.addWidget(self.address)
        
        # Add all rows
        main_layout.addLayout(row1)
        main_layout.addLayout(row2)

        return container
    
    def _open_image_gallery(self):
        
        gallery = ImageGalleryWindow(media_dir=REFERENCE_DIR, parent=self)
        gallery.exec_() 

    def _upload_reference_image(self):
        
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        
        if path:
            temp_pixmap = QPixmap(path)            
            original_filename = os.path.basename(path)
            destination_path = os.path.join(REFERENCE_DIR, original_filename)             
            if temp_pixmap.isNull():
                print("Error: Could not load the image.")
                return

            if temp_pixmap.save(destination_path):
                print(f"Customer reference image saved to: {destination_path}")
                
                # --- CHANGE HERE: Append to the list ---
                if destination_path not in self.reference_image_paths:
                    self.reference_image_paths.append(destination_path)
                # ----------------------------------------
                
                print(f"Total reference images: {len(self.reference_image_paths)}") 
            else:
                print(f"Error: Could not save reference image to {destination_path}")
                        
    def _product_and_image_panel(self):
        """Middle row: left = product image canvas, right = options card"""
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setSpacing(30)  

        # LEFT PANEL
        left_layout = QVBoxLayout()
        top_bar = QHBoxLayout()

        lbl = QLabel("PRODUCT IMAGE :")
        lbl.setStyleSheet("border: none;") 
        lbl.setFixedWidth(170)
        self.cmb = QComboBox()
        self.display_to_filename_map = {}
        self.display_names = ["SELECT"] 
        if os.path.isdir(TEMPLATE_DIR):
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
            
            for filename in os.listdir(TEMPLATE_DIR):
                if filename.lower().endswith(image_extensions):
                    name_without_ext = os.path.splitext(filename)[0]
                    display_name = name_without_ext.upper()                    
                    self.display_names.append(display_name)
                    self.display_to_filename_map[display_name] = filename
        
        self.cmb.addItems(self.display_names)

        self.cmb.setFixedWidth(200)

        self.cmb.currentTextChanged.connect(self._change_image_from_select)

        btn_upload = QPushButton("+")
        btn_upload.setFixedWidth(80)
        btn_upload.setStyleSheet("background-color:#2563eb; color:white;")
        btn_upload.clicked.connect(self._upload_image)

        top_bar.addWidget(lbl)
        top_bar.addWidget(self.cmb)
        top_bar.addWidget(btn_upload)

        # Graphics canvas
        self.scene = QGraphicsScene()
        self.canvas = QGraphicsView(self.scene)
        self.canvas.setFixedSize(525, 300)
        self.canvas.setStyleSheet("background:#fafafa; border:1px solid #d1d5db;")

        left_layout.addLayout(top_bar)
        left_layout.addWidget(self.canvas)
        left_frame = QFrame()   # 👈 अब define कर दिया
        left_frame.setLayout(left_layout)
        left_frame.setFixedWidth(550)
        left_frame.setStyleSheet("background:white; border:1px solid #ddd;")
     
        # 🔹 RIGHT PANEL (Options)
       
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        build_option = self._build_options_panel()   # 👈 अब parent नको
        right_layout.addWidget(build_option)
        #right_frame.setFixedWidth(700)   # 👈 इथे width adjust करा
        # right_frame.setStyleSheet("background:white; border:1px solid #ddd;")

        main_layout.addWidget(left_frame)
        # main_layout.addWidget(second_frame)
        main_layout.addWidget(right_frame)
        default_file = "NEW REGULAR COLER.jpg"
        default_image_path = os.path.join(TEMPLATE_DIR, default_file)

        if os.path.exists(default_image_path):
            self.image = QPixmap(default_image_path)
            
            default_display_name = os.path.splitext(default_file)[0].upper()
            
            index = self.cmb.findText(default_display_name)
            if index != -1:
                self.cmb.setCurrentIndex(index)
                
        else:
            self.image = None
            self.cmb.setCurrentText("SELECT")
        self._render_image()

        return container
    
    def _change_image_from_select(self, display_name):
        if display_name == "SELECT" or not display_name:
            return
        filename = self.display_to_filename_map.get(display_name)
        if filename:
            image_path = os.path.join(TEMPLATE_DIR, filename)
            
            if os.path.exists(image_path):
                new_image = QPixmap(image_path)
                
                if not new_image.isNull():
                    self.image = new_image
                    self._render_image()

    def _build_options_panel(self):
        parent = QWidget()
        layout = QGridLayout(parent)

       
        INPUT_STYLE = """
            background-color: white;
            border: 1px solid gray;
            padding: 3px;
        """

        # --- Style Constants for Dimming ---
        DIM_COLOR = "#A9A9A9"
        NORMAL_COLOR = "#000000"
        DIM_INPUT_STYLE = f"""
            background-color: white;
            border: 1px solid {DIM_COLOR};
            color: {DIM_COLOR};
            padding: 3px;
        """

        GROUPBOX_STYLE = """
            QGroupBox {
                border: 1px solid #d1d5db; 
                border-radius: 4px; 
                margin-top: 15px; 
                padding-top: 20px; 
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                background-color: #F0FFF0;
                padding: 0 5px; 
                padding-bottom: 2px;
                margin-left: 5px; 
                margin-top: -1px; 
            }
        """

    # ========== Printing Options ==========
        default_prices = {'front': '5', 'back': '7', 'patch': '5', 'embroidery': '15', 'Dtf': '0', 'Front sablimation': '60', 'Back sablimation': '60'}
        sec_print = QGroupBox("Printing Options", parent)
        grid_print = QGridLayout(sec_print)
        sec_print.setStyleSheet(GROUPBOX_STYLE)
        sec_print.setMaximumWidth(350)
        #sec_print.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        sec_print.setContentsMargins(30,0,20,0)
        self.print_vars = {}
        keys = ['front', 'back', 'patch', 'embroidery', 'Dtf', 'Front sablimation', 'Back sablimation']

        for idx, key in enumerate(keys):
            default_price = default_prices.get(key, "0")
            cb = QCheckBox(key.upper())
            price_edit = QLineEdit(default_price)
            price_edit.setStyleSheet(INPUT_STYLE)
            price_edit.setEnabled(False)

            def toggle(state, entry=price_edit):
                entry.setEnabled(state == Qt.Checked)
                #if state != Qt.Checked:
                #    entry.setText("0.0")

            cb.stateChanged.connect(toggle)
            self.print_vars[key] = (cb, price_edit)

            grid_print.addWidget(cb, idx, 0)
            grid_print.addWidget(QLabel("Price"), idx, 1)
            grid_print.addWidget(price_edit, idx, 2)

        layout.addWidget(sec_print, 0, 0)

   # ========== Collar Options ==========
        sec1 = QGroupBox("Collar Options", parent)
        grid1 = QGridLayout(sec1)
        sec1.setStyleSheet(GROUPBOX_STYLE)
        #sec1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sec1.setMinimumWidth(250)
        sec1.setContentsMargins(20,0,50,0)
        sec1.move(sec1.x(), 10)

        self.collar_var = "self"
        self.collar_price_self = QLineEdit("0")
        self.collar_price_self.setFixedWidth(50)
        self.collar_price_rib = QLineEdit("10")
        self.collar_price_rib.setFixedWidth(50)
        self.collar_price_patti = QLineEdit("10")
        self.collar_price_patti.setFixedWidth(50)

        self.collar_cloth = QComboBox()
        self.collar_cloth.addItems(["Cotton", "Polyester", "Blended", "Other"])
        
        def _style_price_only(checked, lineedit):
            input_style = INPUT_STYLE if checked else DIM_INPUT_STYLE
            lineedit.setStyleSheet(input_style)

        # --- Self Collar ---
        self.rb_self = QCheckBox("Self Collar")
        self.rb_self.setChecked(True) 
        self.rb_self.toggled.connect(lambda checked: (setattr(self, "collar_var", "self") if checked else None,
            _style_price_only(checked, self.collar_price_self)
        ))
        grid1.addWidget(self.rb_self, 0, 0)
        grid1.addWidget(QLabel("Price"), 0, 1) 
        grid1.addWidget(self.collar_price_self, 0, 2)

        self.rb_rib = QCheckBox("RIB collar")
        self.rb_rib.toggled.connect(lambda checked: (setattr(self, "collar_var", "rib") if checked else None,
            _style_price_only(checked, self.collar_price_rib)
        ))
        grid1.addWidget(self.rb_rib, 1, 0)
        grid1.addWidget(QLabel("Price"), 1, 1)
        grid1.addWidget(self.collar_price_rib, 1, 2)
        self.rb_patti = QCheckBox("RIB Patti")
        
        self.rb_patti.toggled.connect(lambda checked: (setattr(self, "collar_var", "patti") if checked else None,
            _style_price_only(checked, self.collar_price_patti)
        ))
        grid1.addWidget(self.rb_patti, 2, 0)
        grid1.addWidget(QLabel("Price"), 2, 1)
        grid1.addWidget(self.collar_price_patti, 2, 2)

        layout.addWidget(sec1, 0, 1)
        
        self.rb_self.setStyleSheet(f"color: {NORMAL_COLOR};") 
        self.rb_rib.setStyleSheet(f"color: {NORMAL_COLOR};")
        self.rb_patti.setStyleSheet(f"color: {NORMAL_COLOR};")
        
        _style_price_only(self.rb_self.isChecked(), self.collar_price_self)
        _style_price_only(self.rb_rib.isChecked(), self.collar_price_rib)
        _style_price_only(self.rb_patti.isChecked(), self.collar_price_patti)

        # ========== Button and Style Options ==========
        sec_button = QGroupBox("Button Options", parent)
        grid_button = QGridLayout(sec_button)
        sec_button.setStyleSheet(GROUPBOX_STYLE)

        self.style_var = "button"
        self.rb_button = QCheckBox("BUTTON")
        self.rb_button.setFixedWidth(200)
        self.rb_button.setChecked(True)
        self.rb_button.toggled.connect(lambda: setattr(self, "style_var", "button"))
        grid_button.addWidget(self.rb_button, 0, 0)

        self.rb_plain = QRadioButton("PLAIN")
        # rb_plain.setChecked(True)
        self.rb_plain.toggled.connect(lambda: setattr(self, "style_var", "plain"))
        grid_button.addWidget(self.rb_plain, 1, 0)

        self.rb_box = QRadioButton("BOX")
        self.rb_box.toggled.connect(lambda: setattr(self, "style_var", "box"))
        grid_button.addWidget(self.rb_box, 2, 0)

        self.rb_vplus = QRadioButton("V+")
        self.rb_vplus.toggled.connect(lambda: setattr(self, "style_var", "vplus"))
        grid_button.addWidget(self.rb_vplus, 3, 0)

        layout.addWidget(sec_button,0,2)

        # ========== Track Pant Options (NEW SECTION) ==========

        sec_track = QGroupBox("Track Pant Options", parent)
        grid_track = QGridLayout(sec_track)
        sec_track.setStyleSheet(GROUPBOX_STYLE)
        sec_track.setContentsMargins(5, 5, 5, 5)
        sec_track.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sec_track.setContentsMargins(20,0,20,0)

        track_options = {
            'Dori': '0',
            '1 Piping': '2',
            '2 Piping': '6',
            'Other': '0'
        }
        self.track_vars = {}
        self.track_extra_vars = {} 

        for idx, (key, default_price) in enumerate(track_options.items()):
            cb = QCheckBox(key)
            price_edit = QLineEdit(default_price)
            price_edit.setStyleSheet(INPUT_STYLE)
            price_edit.setEnabled(True) 
            price_edit.setFixedWidth(60)

            # --- New Extra Input Box ---
            extra_edit = QLineEdit("")
            extra_edit.setPlaceholderText("")
            extra_edit.setStyleSheet(INPUT_STYLE)
            extra_edit.setFixedWidth(60)
            extra_edit.setEnabled(True) 

            def toggle_track_price(state, entry=price_edit, extra=extra_edit):
                entry.setEnabled(state == Qt.Checked)
                extra.setEnabled(state == Qt.Checked)

            cb.stateChanged.connect(toggle_track_price)
            self.track_vars[key] = (cb, price_edit)
            self.track_extra_vars[key] = extra_edit 

            grid_track.addWidget(cb, idx, 0)
            grid_track.addWidget(QLabel("Price"), idx, 1)
            grid_track.addWidget(price_edit, idx, 2) 
            grid_track.addWidget(extra_edit, idx, 3)

        layout.addWidget(sec_track, 0, 3) 

        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 0)
        layout.setColumnStretch(3, 0) 
        layout.setColumnStretch(4, 1)
       
        # Status layout
        COMBO_BOX_STYLE = """
            QComboBox {
                /* Define a clean, solid border */
                border: 1px solid #777; 
                border-radius: 3px;
            }
        """

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(2,2,2,2)
        status_layout.setSpacing(10) 

        status_label = QLabel("Status:")
        status_label.setMinimumWidth(50)
        font = status_label.font()
        font.setPointSize(11) 
        status_label.setFont(font)
        status_layout.addWidget(status_label)

        # Main status combo
        self.status_combo = QComboBox()
        self.status_combo.addItem("Pending")
        self.status_combo.addItem("Cutting")
        self.status_combo.addItem("Streching")
        self.status_combo.addItem("Printing")
        self.status_combo.addItem("Completed")
        self.status_combo.setFixedWidth(200)
        self.status_combo.setStyleSheet(COMBO_BOX_STYLE) 
        font = self.status_combo.font()
        font.setPointSize(11)
        self.status_combo.setFont(font)
        status_layout.addWidget(self.status_combo)

        status_layout.addStretch()

        # Sub-options list
        layout.addWidget(status_widget, 1, 0, 1, 4)

        # ===== Finally return parent =====
        return parent
                
    def _upload_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.image = QPixmap(path)
            self._render_image()

        # 3. Define the new filename for storage
        # We use the original file's name but ensure it's saved in MEDIA_DIR
        original_filename = os.path.basename(path)
        
        # Create a display name (e.g., "my_shirt.png" -> "MY_SHIRT")
        name_without_ext = os.path.splitext(original_filename)[0]
        display_name = name_without_ext.upper()
        
        # 4. Save the file permanently to MEDIA_DIR
        destination_path = os.path.join(TEMPLATE_DIR, original_filename)
        
        # Only save if the file isn't already there (or overwrite it)
        if not os.path.exists(destination_path) or path != destination_path:
            # We use the QPixmap's save method for reliable saving
            # NOTE: self.image is the QPixmap loaded from 'path'
            success = self.image.save(destination_path)
            
            if success:
                print(f"Image saved to: {destination_path}")
            else:
                print(f"Error: Could not save image to {destination_path}")
                return # Exit if saving failed

        # 5. Update the ComboBox and mapping dictionary
        if display_name not in self.display_names:
            # Update internal data structures
            self.display_names.append(display_name)
            self.display_to_filename_map[display_name] = original_filename
            
            # Update the ComboBox UI
            self.cmb.addItem(display_name)
            
        # 6. Set the ComboBox to the new image's name
        index = self.cmb.findText(display_name)
        if index != -1:
            self.cmb.setCurrentIndex(index)
   
    def _render_image(self):
        """Render centered scaled image into the canvas and reposition entries/arrows."""
        # ❌ scene.clear() मत करो → इससे entries delete हो जाती हैं
        for item in self.scene.items():
            if not isinstance(item, QGraphicsProxyWidget):
                self.scene.removeItem(item)

        w, h = self.canvas.width() - 4, self.canvas.height() - 4

        if self.image:
            pix = self.image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item = QGraphicsPixmapItem(pix)
            cx = (w - pix.width()) / 2
            cy = (h - pix.height()) / 2
            item.setPos(cx, cy)
            self.scene.addItem(item)
            self._canvas_image_item = item
        else:
            # Placeholder
            self.scene.addRect(5, 5, w - 10, h - 10, pen=QPen(QColor("#cbd5e1")))
            text_item = self.scene.addText("Upload T-Shirt Image")
            font = text_item.font()
            font.setPointSize(11)   # 👈 yaha size set karna hai (default ~9 hota hai)
            text_item.setFont(font)
            text_item.setPos(w / 2 - 100, h / 2 - 20)

        # Draw arrows + entries
        self._draw_arrows()

    def _draw_arrows(self):
        """Draw arrows and place entry boxes."""
        w, h = self.canvas.width(), self.canvas.height()
        pen = QPen(QColor("#1e40af"))
        pen.setWidth(2)

        def _draw_arrowhead(scene, pen, p1, p2):
            """Draws a V-shaped arrowhead at point p2, coming from p1."""
            ARROW_SIZE = 8
            
            # Calculate the angle of the line segment
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            angle = math.atan2(dy, dx)
            
            # Calculate the points for the arrowhead triangle
            p3 = QPointF(p2.x() - ARROW_SIZE * math.cos(angle - math.pi / 6),
                        p2.y() - ARROW_SIZE * math.sin(angle - math.pi / 6))
            p4 = QPointF(p2.x() - ARROW_SIZE * math.cos(angle + math.pi / 6),
                        p2.y() - ARROW_SIZE * math.sin(angle + math.pi / 6))
            
            # Create and draw the arrowhead lines
            scene.addLine(p2.x(), p2.y(), p3.x(), p3.y(), pen).setZValue(5)
            scene.addLine(p2.x(), p2.y(), p4.x(), p4.y(), pen).setZValue(5)

        # Note: Using QPointF objects for better geometry handling
        coords = {
            "collar": [QPointF(w / 2 - 80, 0.08 * h), QPointF(w / 2, 0.08 * h)],
            "left_sleeve": [QPointF(0.20 * w, 0.30 * h), QPointF(0.33 * w, 0.30 * h)],
            "right_sleeve": [QPointF(0.80 * w, 0.40 * h), QPointF(0.72 * w, 0.40 * h)],
            "center_right": [QPointF(0.75 * w, 0.70 * h), QPointF(0.60 * w, 0.70 * h)],
            "bottom_right_label": [QPointF(0.85 * w, 0.85 * h)], 
        }
        
        entry_offsets = {
            "collar": (-80, -20),
            "left_sleeve": (-85, -20), # Adjusted for potentially wider box
            "right_sleeve": (-20, -20),  # Adjusted for potentially wider box
            "center_right": (-40, -20),
            "bottom_right_label": (-40, -20), # Adjusted for wider box and far-right position
        }
        
        LINE_Z_VALUE = 5
        BOX_Z_VALUE = 10 

        for key, pts in coords.items():
            if key != "bottom_right_label":
                # 1. Draw lines and get the last line segment
                last_segment_p1 = None
                last_segment_p2 = None
                
                for i in range(len(pts) - 1):
                    p1 = pts[i]
                    p2 = pts[i + 1]
                    
                    line = self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), pen)
                    line.setZValue(LINE_Z_VALUE)
                    
                    # Keep track of the last segment drawn
                    last_segment_p1 = p1
                    last_segment_p2 = p2
                
                # 2. Draw the arrowhead at the end of the last line segment
                if last_segment_p1 and last_segment_p2:
                    _draw_arrowhead(self.scene, pen, last_segment_p1, last_segment_p2)


            # 3. Create the entry box (no change needed here)
            if key not in self.entries:
                entry = QLineEdit()
                entry.setFixedWidth(120) 
                entry.setAlignment(Qt.AlignCenter)
                proxy = QGraphicsProxyWidget()
                proxy.setWidget(entry)
                self.entries[key] = proxy
                self.scene.addItem(proxy)
            
            self.entries[key].setZValue(BOX_Z_VALUE)

            # 4. Set the position of the box
            frx, fry = pts[0].x(), pts[0].y() # Get coordinates from QPointF
            dx, dy = entry_offsets.get(key, (-40, -20))
            self.entries[key].setPos(frx + dx, fry + dy)

    def create_item_selection_box(self):
        group_box = QGroupBox("Item Selection")
        group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid gray; 
                border-radius: 4px;
                margin-top: 15px; 
                padding-top: 20px; 
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left; 
                background-color: #F0FFF0; 
                padding: 0 5px; 
                padding-bottom: 2px;
                margin-left: 5px; 
                margin-top: -1px; 
            }
        """)        
        
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(100)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_button = QPushButton("+Add")
        self.add_button.setStyleSheet("background-color:#87CEFA; min-width: 80px; min-height: 15px;")
        self.add_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) 
        self.add_button.clicked.connect(self._open_add_item_dialog) 
        
        top_layout.addStretch(1) 
        top_layout.addWidget(self.add_button)
        top_layout.addStretch(1)
        
        group_layout.addSpacing(10)
        group_layout.addLayout(top_layout)
        
        self.items_container = QTableWidget()
        self.items_container.setColumnCount(18) 
        
        self.items_container.setStyleSheet("""
        QTableWidget {
            gridline-color: gray; 
            border: 0px solid black; 
        }
        QTableWidget::item {
            border: 0.5px solid gray;
            background-color: #ffffff; 
        }
        QHeaderView::section {
            background-color:: gray; 
            border: 0.5px solid #000000;
            padding: 3px;
            font-weight: normal; 
            text-align: center;
        }
        """)
        
        self.items_container.setHorizontalHeaderLabels(
            ["Fabric", "Type", "Color", "Size", "Qty", "Unit", "Total price", "Status", "Action"]
        )
        self.items_container.verticalHeader().setVisible(False)
        self.items_container.setFixedHeight(120)

        self.items_container.setColumnWidth(0, 180)  # Fabric
        self.items_container.setColumnWidth(1, 200)  # Type
        self.items_container.setColumnWidth(2, 150)  # Color
        self.items_container.setColumnWidth(3, 100)  # Size
        self.items_container.setColumnWidth(4, 100)  # Qty
        self.items_container.setColumnWidth(5, 120)  # Unit
        self.items_container.setColumnWidth(6, 150)  # Total
        self.items_container.setColumnWidth(7, 180)  # NEW: Status
        self.items_container.setColumnWidth(8, 300)  # NEW: Action (for 3 buttons)
        # --- NEW FIX: Hide the three internal add-on columns (9, 10, 11) ---
        self.items_container.setColumnHidden(9, True)
        self.items_container.setColumnHidden(10, True)
        self.items_container.setColumnHidden(11, True)
        self.items_container.setColumnHidden(12, True)
        self.items_container.setColumnHidden(13, True)
        self.items_container.setColumnHidden(14, True) 
        self.items_container.setColumnHidden(15, True) 
        self.items_container.setColumnHidden(16, True) 
        self.items_container.setColumnHidden(17, True) 
        group_layout.addWidget(self.items_container)
       
        # --- Grand Total Label ---
        self.grand_total_label = QLabel("Grand Total: 0")
        self.grand_total_label.setFixedWidth(200)
        self.grand_total_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #000000;      
                background-color: #f9f9f9;                                                                                                       
            }
        """)
        grand_total_layout = QHBoxLayout()
        grand_total_layout.addSpacing(1200)  
        grand_total_layout.addWidget(self.grand_total_label)

        group_layout.addLayout(grand_total_layout)
        return group_box
    
    def _get_row_data(self, row):
        data = {}
        def get_safe_text(container, r, c):
            # Retrieve the QTableWidgetItem or None
            item = container.item(r, c)
            # Return the text if the item exists, otherwise return an empty string
            return item.text() if item is not None else ""
        
        data["Fabric"] = get_safe_text(self.items_container, row, 0)
        data["Type"] = get_safe_text(self.items_container, row, 1)
        data["Color"] = get_safe_text(self.items_container, row, 2)
        data["Size"] = get_safe_text(self.items_container, row, 3)
        data["Qty"] = get_safe_text(self.items_container, row, 4)
        data["Unit"] = get_safe_text(self.items_container, row, 5)
        data["Status"] = get_safe_text(self.items_container, row, 7)

        data["Total"] = get_safe_text(self.items_container, row, 6)
    
        # NEW: Hidden Add-ons (Columns 9, 10, 11) - Useful for a detailed view
        data["PrintAddOn"] = get_safe_text(self.items_container, row, 9)
        data["CollarAddOn"] = get_safe_text(self.items_container, row, 10)
        data["TrackAddOn"] = get_safe_text(self.items_container, row, 11)
        data["Barcode"] = get_safe_text(self.items_container, row, 12)
        data["Remark"] = get_safe_text(self.items_container, row, 13)
        data["Cutting Employee Name"] = get_safe_text(self.items_container, row, 14)
        data["Printing Employee Name"] = get_safe_text(self.items_container, row, 15)
        data["RIB Collar Employee Name"] = get_safe_text(self.items_container, row, 16)
        data["Stretching Employee Name"] = get_safe_text(self.items_container, row, 17)
                
        return data
    
    @staticmethod
    def _set_dialog_read_only(dialog, is_read_only=True):
        for widget in [dialog.color_input, dialog.qty_input, dialog.price_input, dialog.barcode_input, dialog.remark_input]:
            if isinstance(widget, QLineEdit):
                widget.setReadOnly(is_read_only)
        
        for combo in [dialog.cloth_combo, dialog.type_combo, dialog.size_combo, dialog.status_combo]:
            if isinstance(combo, QComboBox):
                combo.setDisabled(is_read_only) 
                
        if is_read_only:
             # Disconnect any existing 'accepted' connections first to ensure the new one works cleanly
            try:
                 dialog.accepted.disconnect() 
            except TypeError:
                pass # Ignore if nothing is connected
            dialog.accepted.connect(dialog.reject) # Makes the 'OK/Done' button behave like 'Close'
             
    def _job_work_action(self, row):
        pass
            
    def _view_item(self, row):
        print(f"Viewing details for item at row: {row}")

        current_data = self._get_row_data(row)
        
        dialog = ItemInputDialog(self, is_view_only=True) 
        dialog.setWindowTitle("View an Item") 
        
        dialog.cloth_combo.setCurrentText(current_data["Fabric"])
        dialog.type_combo.setCurrentText(current_data["Type"])
        dialog.color_input.setText(current_data["Color"])
        dialog.size_combo.setCurrentText(current_data["Size"])
        dialog.qty_input.setText(current_data["Qty"])
        dialog.price_input.setText(current_data["Unit"])
        dialog.status_combo.setCurrentText(current_data["Status"])
        dialog.barcode_input.setText(current_data["Barcode"])
        dialog.remark_input.setText(current_data["Remark"]) 
        dialog.barcode_save_btn.show()
        
        def save_barcode_only_in_view():
            new_barcode = dialog.barcode_input.text()
            item = self.items_container.item(row, 12)
            if item is None:
                from PyQt5.QtWidgets import QTableWidgetItem
                item = QTableWidgetItem(new_barcode)
                self.items_container.setItem(row, 12, item)
            else:
                item.setText(new_barcode) 
            print(f"Barcode for row {row} updated to: {new_barcode} from View Item dialog.")
            dialog.barcode_save_btn.setStyleSheet("background-color: lightgreen;")
            
            dialog.barcode_input.setReadOnly(True)
        try:
            dialog.barcode_save_btn.clicked.disconnect()
        except:
            pass 
            
        dialog.barcode_save_btn.clicked.connect(save_barcode_only_in_view)
        dialog.job_btn.clicked.connect(dialog._open_job_work_dialog)
        dialog.cut_btn.clicked.connect(dialog._open_cutting_dialog)
        dialog.print_btn.clicked.connect(dialog._open_printing_dialog)
            
        self._set_dialog_read_only(dialog, is_read_only=True)
        
        dialog.exec_()

    def _edit_item(self, row):        
        current_data = self._get_row_data(row)
        
        dialog = ItemInputDialog(self)
        dialog.setWindowTitle("Edit an Item") 
        
        dialog.cloth_combo.setCurrentText(current_data["Fabric"])
        dialog.type_combo.setCurrentText(current_data["Type"])
        dialog.color_input.setText(current_data["Color"])
        dialog.size_combo.setCurrentText(current_data["Size"])
        dialog.qty_input.setText(current_data["Qty"])
        dialog.price_input.setText(current_data["Unit"])
        dialog.status_combo.setCurrentText(current_data["Status"])
        dialog.barcode_input.setText(current_data["Barcode"]) 
        dialog.remark_input.setText(current_data["Remark"])
        dialog.barcode_save_btn.show()
        
        def save_barcode_only():
            new_barcode = dialog.barcode_input.text()
            item = self.items_container.item(row, 12)
            if item is None:
                item = QTableWidgetItem(new_barcode)
                self.items_container.setItem(row, 12, item)
            else:
                item.setText(new_barcode)     
            print(f"Barcode for row {row} updated to: {new_barcode}")
            dialog.barcode_save_btn.setStyleSheet("background-color: lightgreen;")
        try:
            dialog.barcode_save_btn.clicked.disconnect()
        except:
            pass  

        dialog.barcode_save_btn.clicked.connect(save_barcode_only)

        if dialog.exec_() == QDialog.Accepted:
            item_data = dialog.get_data()
            
            # 🌟 STEP 2: Open the Employee Dialog, passing existing data
            employee_dialog = EmployeeDetailsDialog(
                item_type=item_data["Type"], 
                current_data=current_data, # Pass existing data to pre-fill fields
                parent=self
            )
            
            if employee_dialog.exec_() == QDialog.Accepted:
                employee_data = employee_dialog.get_employee_data()
                
                # Combine the updated item data and employee data
                final_data = {**item_data, **employee_data}
                
                # Final update to the table
                self._update_item_row(row, final_data)

    def _update_item_row(self, row, data):
        try:
            qty = int(data["Qty"])
            unit = float(data["Unit"])
        except ValueError:
            print("Error: Quantity or Unit Price must be valid numbers. Update cancelled.")
            return
        
        type_text = data["Type"].lower()
        is_shirt_item = "t-shirt" in type_text 
        is_pant_item = "track-pant" in type_text or "shorts" in type_text
                
        printing_add_on_per_unit = 0.0
        collar_add_on_per_unit = 0.0
        track_add_on_per_unit = 0.0
        
        if is_shirt_item:
            printing_add_on_per_unit = self.get_total_printing_price()
            collar_add_on_per_unit = self.get_selected_collar_price()
            
        elif is_pant_item:
            track_add_on_per_unit = self.get_total_track_options_price()
                    
        add_ons = printing_add_on_per_unit + collar_add_on_per_unit + track_add_on_per_unit
        total = (unit + add_ons) * qty

        def safe_set_item(table, r, c, text):
            item = table.item(r, c)
            if item is None:
                item = QTableWidgetItem(text)
                table.setItem(r, c, item)
            else:
                item.setText(text)
            return item

        safe_set_item(self.items_container, row, 0, data["Fabric"])
        safe_set_item(self.items_container, row, 1, data["Type"])
        safe_set_item(self.items_container, row, 2, data["Color"])
        safe_set_item(self.items_container, row, 3, data["Size"])
        safe_set_item(self.items_container, row, 4, str(qty))
        safe_set_item(self.items_container, row, 5, f"{unit:.2f}")
        safe_set_item(self.items_container, row, 6, f"{total:.2f}") 
        safe_set_item(self.items_container, row, 7, data["Status"])
        safe_set_item(self.items_container, row, 12, data["Barcode"])
        safe_set_item(self.items_container, row, 13, data["Remark"])
        safe_set_item(self.items_container, row, 14, data["Cutting Employee Name"])
        safe_set_item(self.items_container, row, 15, data["Printing Employee Name"])
        safe_set_item(self.items_container, row, 16, data["RIB Collar Employee Name"])
        safe_set_item(self.items_container, row, 17, data["Stretching Employee Name"])
        
        # Columns 9-11 (Hidden add-ons data)
        safe_set_item(self.items_container, row, 9, f"{printing_add_on_per_unit:.2f}")
        safe_set_item(self.items_container, row, 10, f"{collar_add_on_per_unit:.2f}")
        safe_set_item(self.items_container, row, 11, f"{track_add_on_per_unit:.2f}")

        for col in range(8): 
            item = self.items_container.item(row, col)
            if item:
                item.setTextAlignment(Qt.AlignCenter)
        self._update_grand_total()

    def _delete_item(self): 
        button = self.sender()
        if not isinstance(button, QPushButton):
            return
        action_widget = button.parentWidget() 
        row_to_delete = -1
        for r in range(self.items_container.rowCount()):
            if self.items_container.cellWidget(r, 8) == action_widget:
                row_to_delete = r
                break        
        if row_to_delete == -1:
            print("Error: Could not determine row for delete action.")
            return    
        reply = QMessageBox.question(self, 'Confirm Delete',
            f"Are you sure you want to delete the item at row {row_to_delete}?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.items_container.removeRow(row_to_delete)
            self._update_grand_total()
            print(f"Item at row {row_to_delete} deleted.")
    
    def _open_add_item_dialog(self):
        dialog = ItemInputDialog(self)
        dialog.barcode_save_btn.show()

        def save_barcode_only():
            dialog.barcode_save_btn.setStyleSheet("background-color: lightgreen;")
            print(f"Barcode saved temporarily in dialog: {dialog.barcode_input.text()}")
        try:
            dialog.barcode_save_btn.clicked.disconnect()
        except:
            pass 
        dialog.barcode_save_btn.clicked.connect(save_barcode_only)
        if dialog.exec_() == QDialog.Accepted:
            item_data = dialog.get_data()
            employee_dialog = EmployeeDetailsDialog(
                item_type=item_data["Type"], 
                current_data=None, # No existing employee data for new item
                parent=self
            )            
            if employee_dialog.exec_() == QDialog.Accepted:
                employee_data = employee_dialog.get_employee_data()
                
                # Combine all data fields
                final_data = {**item_data, **employee_data}
                
                # Final save to the table
                self._add_item_row(final_data)
    
    def _add_item_row(self, data):
        row = self.items_container.rowCount()
        self.items_container.insertRow(row)

        try:
            qty = int(data["Qty"])
            unit = float(data["Unit"])
        except ValueError:
            print("Error: Quantity or Unit Price must be valid numbers.")
            self.items_container.removeRow(row)
            return
        
        # T-SHIRT FILTERING (Kept as is for add-on logic)
        type_text = data["Type"].lower() 
        is_shirt_item = "t-shirt" in type_text 
        is_pant_item = "track-pant" in type_text or "shorts" in type_text

        printing_add_on_per_unit = 0.0
        collar_add_on_per_unit = 0.0
        track_add_on_per_unit = 0.0 

        if is_shirt_item:
            printing_add_on_per_unit = self.get_total_printing_price()
            collar_add_on_per_unit = self.get_selected_collar_price()

        elif is_pant_item:
            track_add_on_per_unit = self.get_total_track_options_price()
        
        add_ons = printing_add_on_per_unit + collar_add_on_per_unit + track_add_on_per_unit
        total = (unit + add_ons) * qty

        # Fabric
        item = QTableWidgetItem(data["Fabric"])
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 0, item)

        # Type
        item = QTableWidgetItem(data["Type"])
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 1, item)

        # Color
        item = QTableWidgetItem(data["Color"])
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 2, item)

        # Size
        item = QTableWidgetItem(data["Size"])
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 3, item)

        # Qty
        item = QTableWidgetItem(str(qty))
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 4, item)

        # Unit
        item = QTableWidgetItem(f"{unit:.2f}")
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 5, item)

        # Total
        item = QTableWidgetItem(f"{total:.2f}")
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 6, item)

        # Status
        item = QTableWidgetItem(data["Status"])
        item.setTextAlignment(Qt.AlignCenter)
        self.items_container.setItem(row, 7, item)

        # Action Buttons
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 0, 5, 0)
        action_layout.setSpacing(5) 
        
        view_btn = QPushButton("👁️ View")
        edit_btn = QPushButton("✏️ Edit")
        delete_btn = QPushButton("🗑️ Delete")
        
        view_btn.clicked.connect(lambda checked, r=row: self._view_item(r))
        edit_btn.clicked.connect(lambda checked, r=row: self._edit_item(r))
        delete_btn.clicked.connect(self._delete_item)

        action_layout.addWidget(view_btn)
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)

        self.items_container.setCellWidget(row, 8, action_widget)

        item_print = QTableWidgetItem(f"{printing_add_on_per_unit:.2f}")
        self.items_container.setItem(row, 9, item_print) 

        item_collar = QTableWidgetItem(f"{collar_add_on_per_unit:.2f}")
        self.items_container.setItem(row, 10, item_collar)

        item_track = QTableWidgetItem(f"{track_add_on_per_unit:.2f}")
        self.items_container.setItem(row, 11, item_track)

        item_barcode = QTableWidgetItem(data["Barcode"])
        self.items_container.setItem(row, 12, item_barcode)

        item_remark = QTableWidgetItem(data["Remark"]) 
        self.items_container.setItem(row, 13, item_remark)

        self.items_container.setItem(row, 14, QTableWidgetItem(data["Cutting Employee Name"]))
        self.items_container.setItem(row, 15, QTableWidgetItem(data["Printing Employee Name"]))
        self.items_container.setItem(row, 16, QTableWidgetItem(data["RIB Collar Employee Name"]))
        self.items_container.setItem(row, 17, QTableWidgetItem(data["Stretching Employee Name"]))

        collar_type_flag = "NONE" 
    
        if is_shirt_item: 
            
            if hasattr(self, 'rb_rib') and self.rb_rib.isChecked(): 
                collar_type_flag = "RIB"
            elif hasattr(self, 'rb_patti') and self.rb_patti.isChecked():
                collar_type_flag = "PATTI"
            elif hasattr(self, 'rb_self') and self.rb_self.isChecked():
                collar_type_flag = "SELF"
                
        # Save the collar type flag in Column 18 (index 18)
        self.items_container.setItem(row, 18, QTableWidgetItem(collar_type_flag))
        
        if len(self.item_collar_flags) <= row:
            self.item_collar_flags.append(collar_type_flag)
        else:
            # यह केवल edit/replace के लिए होगा, लेकिन हम इसे सुरक्षित रूप से यहाँ सेट करते हैं
            self.item_collar_flags[row] = collar_type_flag

        if self.items_container.columnCount() < 19:
            self.items_container.setColumnCount(19)

        self.items_container.setColumnHidden(9, True)
        self.items_container.setColumnHidden(10, True)
        self.items_container.setColumnHidden(11, True) 
        self.items_container.setColumnHidden(12, True) 
        self.items_container.setColumnHidden(13, True)
        self.items_container.setColumnHidden(14, True) # Cutting
        self.items_container.setColumnHidden(15, True) # Printing
        self.items_container.setColumnHidden(16, True) # Collar
        self.items_container.setColumnHidden(17, True) # Stretching
        self.items_container.setColumnHidden(18, True) # NEW Collar Type Flag
        self._update_grand_total()

    def get_total_printing_price(self):
        total_print_price = 0.0
        for key, (checkbox, price_edit) in self.print_vars.items():
            if checkbox.isChecked():
                try:
                    price = float(price_edit.text())
                    total_print_price += price
                except ValueError:
                    print(f"Warning: Invalid price found for {key}.")
                    continue
        return total_print_price

    def get_selected_collar_price(self):
        collar_price = 0.0
        try:
            if self.rb_self.isChecked():
                collar_price = float(self.collar_price_self.text())

            elif self.rb_rib.isChecked():
                collar_price = float(self.collar_price_rib.text())

            elif self.rb_patti.isChecked():
                collar_price = float(self.collar_price_patti.text())

        except (ValueError, AttributeError):
            print("Warning: Invalid price found for selected collar option. Using price of 0.0.")
            collar_price = 0.0 

        return collar_price
    
    def get_total_track_options_price(self):
        total_track_price = 0.0
        for key, (checkbox, price_edit) in self.track_vars.items():
            if checkbox.isChecked():
                try:
                    price = float(price_edit.text())
                    total_track_price += price
                except ValueError:
                    print(f"Warning: Invalid price found for Track Option: {key}.")
                    continue
        return total_track_price

    def _get_collar_name(self):
        if hasattr(self, 'entries') and 'collar' in self.entries:
            collar_proxy = self.entries['collar']
            
            collar_widget = collar_proxy.widget() 
            
            if collar_widget and hasattr(collar_widget, 'text'):
                text = collar_widget.text().strip()
                if text:
                    return text
                return ""
            
        return "N/A"

    def _open_rib_collar_breakdown(self):
        rib_collar_data = self._gather_rib_collar_data()
        
        if not rib_collar_data['breakdown']:
            QMessageBox.information(self, "No RIB Collar Items", 
                                    "No items marked as 'RIB Collar' were found in the order table.", 
                                    QMessageBox.Ok)
            return
        collar_name = self._get_collar_name()
        dialog = RibCollarPrintDialog(self, breakdown_data=rib_collar_data, collar_name=collar_name)
        dialog.exec_()
        
    def _gather_rib_collar_data(self):
        breakdown = {} 
        unique_colors = set()
        total_qty = 0
        
        # Assuming self.items_container exists and is populated
        if not hasattr(self, 'items_container'):
            return {'breakdown': {}, 'colors': [], 'total_qty': 0}

        for row in range(self.items_container.rowCount()):
            collar_type_text = self.item_collar_flags[row].upper() if row < len(self.item_collar_flags) else ""
            
            type_item = self.items_container.item(row, 1) # Type is in column 1 (T-shirt)
            #collar_type_flag_item = self.items_container.item(row, 18)
            
            if (type_item and "t-shirt" in type_item.text().lower() and 
                collar_type_text == "RIB"):
                
                try:
                    size = self.items_container.item(row, 3).text()
                    qty = int(self.items_container.item(row, 4).text())
                    color = self.items_container.item(row, 2).text().strip()
                except (AttributeError, ValueError, TypeError):
                    continue

                key = (size, color)
                breakdown[key] = breakdown.get(key, 0) + qty
                unique_colors.add(color)
                total_qty += qty

        if not breakdown:
            # This will show the error message if no items pass the filter
            return {'breakdown': {}, 'colors': [], 'total_qty': 0}
        
        return {
            'breakdown': breakdown,
            'colors': sorted(list(unique_colors)),
            'total_qty': total_qty
        }

    def _calculate_item_total_price(self, unit_price, qty, printing_add_on_per_unit, collar_add_on_per_unit):        
        printing_add_on_per_unit = self.get_total_printing_price()
        collar_add_on_per_unit = self.get_selected_collar_price()       
        total = (unit_price + printing_add_on_per_unit + collar_add_on_per_unit) * qty
        return total
    
    def _recalculate_all_item_totals(self):
        """Recalculates the Total Price for all rows in the table and updates the Grand Total."""
        from PyQt5.QtWidgets import QTableWidgetItem
        
        for row in range(self.items_container.rowCount()):
            unit_price_item = self.items_container.item(row, 5) 
            qty_item = self.items_container.item(row, 4) 
            print_add_on_item = self.items_container.item(row, 9) 
            collar_add_on_item = self.items_container.item(row, 10)
            track_add_on_item = self.items_container.item(row, 11) 

            if unit_price_item and qty_item and print_add_on_item and collar_add_on_item and track_add_on_item:
                try:
                    unit_price = float(unit_price_item.text())
                    qty = int(qty_item.text())
                    printing_add_on_per_unit = float(print_add_on_item.text())
                    collar_add_on_per_unit = float(collar_add_on_item.text())
                    track_add_on_per_unit = float(track_add_on_item.text())

                    new_total_price = (unit_price + printing_add_on_per_unit + collar_add_on_per_unit + track_add_on_per_unit) * qty

                    total_price_item = self.items_container.item(row, 6)
                    if not total_price_item:
                        total_price_item = QTableWidgetItem()
                        self.items_container.setItem(row, 6, total_price_item)
                        
                    total_price_item.setText(f"{new_total_price:.2f}") 
                    total_price_item.setTextAlignment(Qt.AlignCenter) 

                except ValueError:
                    continue 
        self._update_grand_total()
        
    def _update_grand_total(self):
        self._total_items_sum = 0.0
        
        # 1. Calculate Subtotal (Total Items Price)
        for row in range(self.items_container.rowCount()):
            item = self.items_container.item(row, 6)  # Column 6 = Total price (unit + add-ons) * Qty
            if item:
                try:
                    # Use the class attribute
                    self._total_items_sum += float(item.text())
                except ValueError:
                    pass
                    
        # 2. Get Tax Rate
        tax_apply = self.tax_apply_combo.currentText()
        self._tax_percentage = 0.0
        if tax_apply == "Y":
            try:
                self._tax_percentage = float(self.tax_percentage_input.text())
            except ValueError:
                self._tax_percentage = 0.0
                
        # 3. Calculate Tax Amount and Grand Total
        tax_rate = self._tax_percentage / 100.0
        self._tax_amount = self._total_items_sum * tax_rate
        self._grand_total = self._total_items_sum + self._tax_amount
        
        # 4. Update UI Labels (The required fix is here)
        
        # Update the label that should show the subtotal
        if hasattr(self, 'total_items_price_label'):
            # FIX: Changed 'total_items_sum' to 'self._total_items_sum'
            self.total_items_price_label.setText(f"Total Items Price: {self._total_items_sum:.2f}")
        
        # Update the label that should show the tax breakdown
        if hasattr(self, 'tax_amount_label'):
            self.tax_amount_label.setText(f"Tax ({self._tax_percentage:.1f}%) @ {tax_apply}: {self._tax_amount:.2f}")

        # Update the Grand Total label (Final amount)
        # Note: This line is repeated in your original code, which is fine, but redundant.
        self.grand_total_label.setText(f"Grand Total: {self._grand_total:.2f}")
    def setup_tax_and_remark_fields(self):
        # This layout will hold both the Tax controls (on the left) 
        # and the Remark input (on the right).
        combined_row_layout = QHBoxLayout()
        combined_row_layout.setSpacing(20)
        
        # --- 1. TAX (GST) FIELDS ---
        tax_fields_layout = QHBoxLayout()
        tax_fields_layout.setSpacing(10)
        tax_fields_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tax Label
        tax_label = QLabel("TAX (GST):")
        tax_label.setFixedWidth(80) # Adjusted width
        tax_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tax_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        tax_fields_layout.addWidget(tax_label)

        # Y/N Selector
        self.tax_apply_combo = QComboBox()
        self.tax_apply_combo.addItems(["N", "Y"])
        self.tax_apply_combo.setFixedWidth(50)
        self.tax_apply_combo.setStyleSheet("border: 1px solid black; border-radius: 0px; padding: 2px;")
        tax_fields_layout.addWidget(self.tax_apply_combo)

        # Percentage Input Field
        self.tax_percentage_input = QLineEdit("0.0")
        self.tax_percentage_input.setPlaceholderText("Percentage (%)")
        self.tax_percentage_input.setFixedWidth(120)
        self.tax_percentage_input.setStyleSheet("border: 1px solid black; border-radius: 0px; padding: 4px 6px;")
        self.tax_percentage_input.setDisabled(True) # Disabled by default ("N" selected)
        tax_fields_layout.addWidget(self.tax_percentage_input)
        
        # Add the entire tax section to the combined row
        tax_section_widget = QWidget()
        tax_section_widget.setLayout(tax_fields_layout)
        combined_row_layout.addWidget(tax_section_widget)

        # Add a horizontal line or spacing to separate GST and REMARK visually
        combined_row_layout.addSpacing(40) 

        # --- 2. REMARK FIELD ---
        remark_fields_layout = QHBoxLayout()
        remark_fields_layout.setSpacing(10)
        remark_fields_layout.setContentsMargins(0, 0, 0, 0)

        remark_label = QLabel("REMARK:")
        remark_label.setFixedWidth(90) # Adjusted width
        remark_label.setAlignment(Qt.AlignCenter)
        remark_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid black;
                padding: 2px 4px;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """)
        
        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText("Enter remark here...")
        self.remark_input.setFixedWidth(500)
        self.remark_input.setStyleSheet("QLineEdit { border: 1px solid black; border-radius: 0px; padding: 4px 6px; }")

        remark_fields_layout.addWidget(remark_label)
        remark_fields_layout.addWidget(self.remark_input)

        # Add the entire remark section to the combined row
        remark_section_widget = QWidget()
        remark_section_widget.setLayout(remark_fields_layout)
        combined_row_layout.addWidget(remark_section_widget)

        # Add stretch to push everything to the left side
        combined_row_layout.addStretch(1)

        # Add the final combined layout to the main layout
        self.main_layout.addLayout(combined_row_layout)
        self.main_layout.addSpacing(10) # Add space after the combined row
        
        # --- CONNECTIVITY (REQUIRED for conditional logic) ---
        self.tax_apply_combo.currentTextChanged.connect(self._toggle_tax_percentage_field)
        self.tax_percentage_input.textChanged.connect(self._update_grand_total)

    def _toggle_tax_percentage_field(self, text):
        """Enables/Disables the tax percentage input based on the Y/N selection."""
        if text == "Y":
            self.tax_percentage_input.setDisabled(False)
            self.tax_percentage_input.setText("18.0") # Set default GST value
        else:
            self.tax_percentage_input.setDisabled(True)
            self.tax_percentage_input.setText("0.0") # Reset to zero when tax is off
        self._update_grand_total()

    def create_buttons_row(self):
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(1)    
        
        self.save_btn = QPushButton("💾\n SAVE")
        self.undo_btn=QPushButton("↩️\n CANCEL")
        self.quotatation_btn = QPushButton("💾\n QUOTATION")
        self.bill_btn = QPushButton("🧾\n GENERATE BILL")
        #self.job_btn = QPushButton("⚒️\n JOB WORK")
        self.rib_btn = QPushButton("🧵\n RIB COLLAR")
        #self.cut_btn = QPushButton("✂️\n CUTTING")
        #self.print_btn = QPushButton("🖨\n PRINTING")
        
        self.bill_btn.setFixedWidth(170)
        self.save_btn.setFixedWidth(140)
        self.undo_btn.setFixedWidth(140)
        self.quotatation_btn.setFixedWidth(140)
        #self.job_btn.setFixedWidth(140)
        self.rib_btn.setFixedWidth(140)
        #self.cut_btn.setFixedWidth(140)
        #self.print_btn.setFixedWidth(140)

        #Connect Buttons to functions
        self.quotatation_btn.clicked.connect(self.show_quotation_preview)
        self.rib_btn.clicked.connect(self._open_rib_collar_breakdown)

        buttons = [
            self.save_btn,self.undo_btn, self.quotatation_btn, self.bill_btn, self.rib_btn,
            #self.job_btn, self.rib_btn, self.cut_btn, self.print_btn
        ]

        for i, btn in enumerate(buttons):
            btn.setFixedHeight(60)
            btn.setStyleSheet(" background-color: #EEEEEE; "
           " color: #fc83a0;" 
            "font-weight: bold; "
            "padding:10px;")
            
            buttons_layout.addWidget(btn)
        
            # har button ke baad space chahiye (last ke baad nahi)
            if i < len(buttons) - 1:
                buttons_layout.addSpacing(1)  # yaha 30px gap set karo
        buttons_layout.addStretch()
        return buttons_layout
    
    def show_quotation_preview(self): 
        content_data = self._generate_item_table_html()
        dialog = QuotationPreviewDialog(self, content_data)
        dialog.exec_()
    
    def open_search_window(self):
        # नया window बनाओ
        self.search_window = QWidget()
        self.search_window.setWindowTitle("📋 Order List")
        self.search_window.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout(self.search_window)

        # Header
        header = QLabel("Select an Order from the list")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header, alignment=Qt.AlignCenter)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search...")
        layout.addWidget(self.search_input)

        # Order list
        self.list_widget = QListWidget()
        orders = [
            {"id": 1, "customer": "Ashwini", "total": 500},
            {"id": 2, "customer": "Rahul", "total": 700},
            {"id": 3, "customer": "Sneha", "total": 300},
        ]
        self.orders = orders
        for order in orders:
            item_text = f"Order {order['id']} | {order['customer']} | ₹{order['total']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, order)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # Close button
        close_btn = QPushButton("Close")
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        # Connections
        def filter_list(text):
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                item.setHidden(text.lower() not in item.text().lower())

        self.search_input.textChanged.connect(filter_list)
        close_btn.clicked.connect(self.search_window.close)

        def on_item_selected(item):
            order = item.data(Qt.UserRole)
            # 👇 main form ke fields fill
            self.party_name.setText(order["customer"])
            self.total_price_input.setText(str(order["total"]))
            self.search_window.close()

        self.list_widget.itemDoubleClicked.connect(on_item_selected)

        # Show new window
        self.search_window.show()

    def _generate_item_table_html(self):
        
        table = self.items_container 
        if table.rowCount() == 0:
            return "<p>No items added to the order.</p>"
        
        html = '<table class="item-table">\n'
        header_labels = []
        for col in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(col)
            if header_item is not None:
                header_labels.append(header_item.text())
            else:
                header_labels.append(f"Col {col+1}")
        
        html += '<tr><th>Fabric</th><th>Type</th><th>Color</th><th>Size</th><th>Qty</th><th>Unit Price</th><th>Total Price</th></tr>\n'
        
        for row in range(table.rowCount()):
            html += '<tr>'
            for col in range(table.columnCount()):
                item = table.item(row, col)
                text = item.text() if item is not None else ""
                html += f'<td>{text}</td>'
            html += '</tr>\n'
        
        html += '</table>'
        return html

    def open_print_dialog(self):
        item_table_html = self._generate_item_table_html()
        
        dialog = PrintExportDialog(content_data=item_table_html, parent=self)
        dialog.exec_()
    def _capture_canvas_as_base64(self):
        if not hasattr(self, 'canvas') or not self.canvas:
            return ""

        pixmap = QPixmap(self.canvas.size())
        pixmap.fill(Qt.white) # Ensure white background

        painter = QPainter(pixmap)
        self.canvas.render(painter) # Render the view content
        painter.end()

        # Convert Pixmap to Base64 URI
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG") 
        
        base64_data = byte_array.toBase64().data().decode()
        return f"data:image/png;base64,{base64_data}"
    
if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            font-size: 11pt;
            font-family: Arial;
        }
    """)
    window = OrderForm()
    window.show()
    sys.exit(app.exec_())