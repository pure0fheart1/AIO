import os
import json
import csv
import numpy as np
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem, 
                            QSplitter, QInputDialog, QMessageBox, QFileDialog,
                            QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                            QFormLayout, QSpinBox, QTabWidget, QColorDialog,
                            QLineEdit, QCheckBox, QGroupBox, QRadioButton)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class ChartItem(QListWidgetItem):
    def __init__(self, title, chart_type, data_path, chart_config=None, parent=None):
        super().__init__(title, parent)
        
        self.title = title
        self.chart_type = chart_type
        self.data_path = data_path
        self.chart_config = chart_config or {}
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.setData(Qt.UserRole, {
            "title": title,
            "type": chart_type,
            "data_path": data_path,
            "config": self.chart_config,
            "created": self.created_date
        })

class DataVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Create directory for charts
        self.charts_directory = os.path.join(os.path.expanduser("~/Documents"), "VideoDownloader", "Charts")
        os.makedirs(self.charts_directory, exist_ok=True)
        
        # File for storing chart data
        self.charts_file = os.path.join(self.charts_directory, "charts.json")
        
        # Chart types
        self.chart_types = {
            "Line Chart": self.create_line_chart,
            "Bar Chart": self.create_bar_chart,
            "Pie Chart": self.create_pie_chart,
            "Scatter Plot": self.create_scatter_plot,
            "Histogram": self.create_histogram,
            "Box Plot": self.create_box_plot,
            "Area Chart": self.create_area_chart,
            "Heatmap": self.create_heatmap
        }
        
        self.setup_ui()
        self.load_charts()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header section
        header_layout = QHBoxLayout()
        title = QLabel("Data Visualizer")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        import_btn = QPushButton("Import Data")
        import_btn.clicked.connect(self.import_data)
        
        create_chart_btn = QPushButton("Create Chart")
        create_chart_btn.clicked.connect(self.create_chart)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(import_btn)
        header_layout.addWidget(create_chart_btn)
        
        layout.addLayout(header_layout)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Charts list panel (left)
        charts_panel = QWidget()
        charts_layout = QVBoxLayout(charts_panel)
        
        charts_header = QLabel("Saved Charts")
        charts_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        charts_layout.addWidget(charts_header)
        
        self.charts_list = QListWidget()
        self.charts_list.itemClicked.connect(self.on_chart_selected)
        self.charts_list.setMinimumWidth(200)
        charts_layout.addWidget(self.charts_list)
        
        # Chart actions
        chart_actions = QHBoxLayout()
        self.rename_chart_btn = QPushButton("Rename")
        self.rename_chart_btn.clicked.connect(self.rename_chart)
        
        self.delete_chart_btn = QPushButton("Delete")
        self.delete_chart_btn.clicked.connect(self.delete_chart)
        
        self.export_chart_btn = QPushButton("Export")
        self.export_chart_btn.clicked.connect(self.export_chart)
        
        chart_actions.addWidget(self.rename_chart_btn)
        chart_actions.addWidget(self.delete_chart_btn)
        chart_actions.addWidget(self.export_chart_btn)
        
        charts_layout.addLayout(chart_actions)
        
        # Chart display panel (right)
        chart_panel = QWidget()
        chart_layout = QVBoxLayout(chart_panel)
        
        # Chart configuration panel
        self.config_panel = QWidget()
        self.config_layout = QFormLayout(self.config_panel)
        
        # Chart title input
        self.chart_title_input = QLineEdit()
        self.chart_title_input.textChanged.connect(self.update_chart)
        self.config_layout.addRow("Chart Title:", self.chart_title_input)
        
        # Chart type selector
        self.chart_type_selector = QComboBox()
        self.chart_type_selector.addItems(list(self.chart_types.keys()))
        self.chart_type_selector.currentTextChanged.connect(self.update_chart)
        self.config_layout.addRow("Chart Type:", self.chart_type_selector)
        
        # Data info
        self.data_info_label = QLabel("No data loaded")
        self.config_layout.addRow("Data:", self.data_info_label)
        
        # X-axis selector
        self.x_axis_selector = QComboBox()
        self.config_layout.addRow("X-Axis:", self.x_axis_selector)
        
        # Y-axis selector
        self.y_axis_selector = QComboBox()
        self.config_layout.addRow("Y-Axis:", self.y_axis_selector)
        
        # Additional options will be added dynamically
        
        # Apply button
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self.update_chart)
        self.config_layout.addRow("", self.apply_btn)
        
        chart_layout.addWidget(self.config_panel)
        
        # Matplotlib figure
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        
        # Add panels to splitter
        splitter.addWidget(charts_panel)
        splitter.addWidget(chart_panel)
        
        # Set splitter ratios
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
        # Set initial button states
        self.update_button_states()

        # Current data and chart state
        self.current_data = None
        self.current_data_path = None
        self.current_chart_item = None
    
    def load_charts(self):
        """Load saved charts from JSON file"""
        self.charts_list.clear()
        
        if os.path.exists(self.charts_file):
            try:
                with open(self.charts_file, 'r') as f:
                    charts = json.load(f)
                
                for chart_data in charts:
                    item = ChartItem(
                        chart_data["title"],
                        chart_data["type"],
                        chart_data["data_path"],
                        chart_data.get("config", {})
                    )
                    self.charts_list.addItem(item)
            except Exception as e:
                print(f"Error loading charts: {str(e)}")
    
    def save_charts(self):
        """Save charts data to JSON file"""
        charts = []
        
        for i in range(self.charts_list.count()):
            item = self.charts_list.item(i)
            chart_data = item.data(Qt.UserRole)
            charts.append(chart_data)
        
        try:
            with open(self.charts_file, 'w') as f:
                json.dump(charts, f, indent=4)
        except Exception as e:
            print(f"Error saving charts: {str(e)}")
    
    def update_button_states(self):
        """Update button states based on selection"""
        has_chart = self.charts_list.currentItem() is not None
        has_data = self.current_data is not None
        
        self.rename_chart_btn.setEnabled(has_chart)
        self.delete_chart_btn.setEnabled(has_chart)
        self.export_chart_btn.setEnabled(has_chart)
        self.apply_btn.setEnabled(has_data)
    
    def import_data(self):
        """Import data from CSV/Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Determine file type and load data
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                QMessageBox.warning(self, "Warning", "Unsupported file format")
                return
            
            # Store data
            self.current_data = df
            self.current_data_path = file_path
            
            # Update UI
            self.data_info_label.setText(f"{os.path.basename(file_path)} ({len(df)} rows × {len(df.columns)} columns)")
            
            # Update column selectors
            self.x_axis_selector.clear()
            self.y_axis_selector.clear()
            
            for column in df.columns:
                self.x_axis_selector.addItem(column)
                self.y_axis_selector.addItem(column)
            
            # Select default columns
            if len(df.columns) > 1:
                self.x_axis_selector.setCurrentIndex(0)
                self.y_axis_selector.setCurrentIndex(1)
            
            # Update button states
            self.update_button_states()
            
            # Create initial chart
            self.update_chart()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
    
    def create_chart(self):
        """Create a new chart from the current data"""
        if not self.current_data_path:
            QMessageBox.warning(self, "Warning", "Please import data first")
            return
        
        # Get chart title
        title, ok = QInputDialog.getText(
            self,
            "New Chart",
            "Enter chart title:"
        )
        
        if not ok or not title:
            return
        
        # Get current configuration
        chart_type = self.chart_type_selector.currentText()
        
        config = {
            "title": self.chart_title_input.text(),
            "type": chart_type,
            "x_axis": self.x_axis_selector.currentText(),
            "y_axis": self.y_axis_selector.currentText()
        }
        
        # Create chart item
        item = ChartItem(
            title,
            chart_type,
            self.current_data_path,
            config
        )
        
        # Add to list and select it
        self.charts_list.addItem(item)
        self.charts_list.setCurrentItem(item)
        
        # Save charts
        self.save_charts()
        
        # Update UI
        self.update_button_states()
    
    def on_chart_selected(self, item):
        """Handle chart selection"""
        self.current_chart_item = item
        chart_data = item.data(Qt.UserRole)
        
        # Load data file
        try:
            file_path = chart_data["data_path"]
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                QMessageBox.warning(self, "Warning", "Unsupported file format")
                return
            
            # Store data
            self.current_data = df
            self.current_data_path = file_path
            
            # Update UI
            self.data_info_label.setText(f"{os.path.basename(file_path)} ({len(df)} rows × {len(df.columns)} columns)")
            
            # Update column selectors
            self.x_axis_selector.clear()
            self.y_axis_selector.clear()
            
            for column in df.columns:
                self.x_axis_selector.addItem(column)
                self.y_axis_selector.addItem(column)
            
            # Set values from configuration
            config = chart_data.get("config", {})
            
            if "title" in config:
                self.chart_title_input.setText(config["title"])
            else:
                self.chart_title_input.setText(item.text())
            
            if "type" in config:
                index = self.chart_type_selector.findText(config["type"])
                if index >= 0:
                    self.chart_type_selector.setCurrentIndex(index)
            
            if "x_axis" in config:
                index = self.x_axis_selector.findText(config["x_axis"])
                if index >= 0:
                    self.x_axis_selector.setCurrentIndex(index)
            
            if "y_axis" in config:
                index = self.y_axis_selector.findText(config["y_axis"])
                if index >= 0:
                    self.y_axis_selector.setCurrentIndex(index)
            
            # Update chart
            self.update_chart()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load chart data: {str(e)}")
    
    def update_chart(self):
        """Update chart based on current settings"""
        if not self.current_data_path:
            return
        
        try:
            # Clear the figure
            self.ax.clear()
            
            # Get chart type and call appropriate function
            chart_type = self.chart_type_selector.currentText()
            chart_func = self.chart_types.get(chart_type)
            
            if chart_func:
                x_column = self.x_axis_selector.currentText()
                y_column = self.y_axis_selector.currentText()
                title = self.chart_title_input.text()
                
                # Create chart
                chart_func(x_column, y_column, title)
                
                # Update canvas
                self.canvas.draw()
                
                # Update current chart item if available
                if self.current_chart_item:
                    config = {
                        "title": title,
                        "type": chart_type,
                        "x_axis": x_column,
                        "y_axis": y_column
                    }
                    
                    self.current_chart_item.setData(
                        Qt.UserRole,
                        {
                            "title": self.current_chart_item.text(),
                            "type": chart_type,
                            "data_path": self.current_data_path,
                            "config": config,
                            "created": self.current_chart_item.created_date
                        }
                    )
                    
                    self.save_charts()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update chart: {str(e)}")
    
    def rename_chart(self):
        """Rename the selected chart"""
        current_item = self.charts_list.currentItem()
        if not current_item:
            return
        
        # Get new title
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Chart",
            "Enter new title:",
            QLineEdit.Normal,
            current_item.text()
        )
        
        if ok and new_title:
            # Update item
            data = current_item.data(Qt.UserRole)
            data["title"] = new_title
            
            current_item.setText(new_title)
            current_item.setData(Qt.UserRole, data)
            
            # Save charts
            self.save_charts()
    
    def delete_chart(self):
        """Delete the selected chart"""
        current_item = self.charts_list.currentItem()
        if not current_item:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete chart '{current_item.text()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove item
            row = self.charts_list.row(current_item)
            self.charts_list.takeItem(row)
            
            # Save charts
            self.save_charts()
            
            # Clear current item
            if self.current_chart_item == current_item:
                self.current_chart_item = None
            
            # Update UI
            self.update_button_states()
    
    def export_chart(self):
        """Export the current chart as an image"""
        current_item = self.charts_list.currentItem()
        if not current_item:
            return
        
        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            os.path.join(self.charts_directory, f"{current_item.text()}.png"),
            "PNG Files (*.png);;JPEG Files (*.jpg);;SVG Files (*.svg);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Save figure
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Success", f"Chart exported to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export chart: {str(e)}")
    
    # Chart creation methods
    def create_line_chart(self, x_column, y_column, title):
        """Create a line chart"""
        x = self.current_data[x_column]
        y = self.current_data[y_column]
        
        self.ax.plot(x, y, marker='o', linestyle='-')
        self.ax.set_title(title)
        self.ax.set_xlabel(x_column)
        self.ax.set_ylabel(y_column)
        self.ax.grid(True)
    
    def create_bar_chart(self, x_column, y_column, title):
        """Create a bar chart"""
        x = self.current_data[x_column]
        y = self.current_data[y_column]
        
        self.ax.bar(x, y)
        self.ax.set_title(title)
        self.ax.set_xlabel(x_column)
        self.ax.set_ylabel(y_column)
        
        # Rotate x-labels if there are many categories
        if len(x) > 10:
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
    
    def create_pie_chart(self, x_column, y_column, title):
        """Create a pie chart"""
        # For pie charts, we need data grouping
        data = self.current_data.groupby(x_column)[y_column].sum()
        
        self.ax.pie(
            data.values, 
            labels=data.index, 
            autopct='%1.1f%%',
            startangle=90,
            shadow=True
        )
        self.ax.set_title(title)
        self.ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
    
    def create_scatter_plot(self, x_column, y_column, title):
        """Create a scatter plot"""
        x = self.current_data[x_column]
        y = self.current_data[y_column]
        
        self.ax.scatter(x, y)
        self.ax.set_title(title)
        self.ax.set_xlabel(x_column)
        self.ax.set_ylabel(y_column)
        self.ax.grid(True)
    
    def create_histogram(self, x_column, y_column, title):
        """Create a histogram (only uses x_column)"""
        x = self.current_data[x_column]
        
        self.ax.hist(x, bins=30, alpha=0.7, color='blue', edgecolor='black')
        self.ax.set_title(title)
        self.ax.set_xlabel(x_column)
        self.ax.set_ylabel('Frequency')
        self.ax.grid(True)
    
    def create_box_plot(self, x_column, y_column, title):
        """Create a box plot"""
        # For box plots, we group data if both x and y are provided
        if x_column != y_column:
            # Get unique categories in x_column
            categories = self.current_data[x_column].unique()
            
            # Prepare data for each category
            data = []
            labels = []
            
            for category in categories:
                values = self.current_data[self.current_data[x_column] == category][y_column].dropna()
                if len(values) > 0:
                    data.append(values)
                    labels.append(category)
            
            if data:
                self.ax.boxplot(data, labels=labels)
                self.ax.set_ylabel(y_column)
        else:
            # Simple box plot for a single column
            self.ax.boxplot(self.current_data[y_column].dropna())
            self.ax.set_ylabel(y_column)
        
        self.ax.set_title(title)
        self.ax.grid(True, axis='y')
    
    def create_area_chart(self, x_column, y_column, title):
        """Create an area chart"""
        x = self.current_data[x_column]
        y = self.current_data[y_column]
        
        self.ax.fill_between(x, y, alpha=0.4)
        self.ax.plot(x, y, 'k-', alpha=0.6)
        self.ax.set_title(title)
        self.ax.set_xlabel(x_column)
        self.ax.set_ylabel(y_column)
        self.ax.grid(True)
    
    def create_heatmap(self, x_column, y_column, title):
        """Create a heatmap (needs a third column for values)"""
        # For heatmaps, we need a pivot table
        try:
            # Find a numeric column that's not x or y for the values
            value_cols = [col for col in self.current_data.select_dtypes(include=np.number).columns 
                         if col not in [x_column, y_column]]
            
            if not value_cols:
                raise ValueError("No numeric column available for heatmap values")
            
            value_column = value_cols[0]
            
            # Create pivot table
            pivot_table = pd.pivot_table(
                self.current_data,
                values=value_column,
                index=y_column,
                columns=x_column,
                aggfunc=np.mean
            )
            
            # Create heatmap
            im = self.ax.imshow(pivot_table, cmap='viridis')
            
            # Add labels
            self.ax.set_xticks(np.arange(len(pivot_table.columns)))
            self.ax.set_yticks(np.arange(len(pivot_table.index)))
            self.ax.set_xticklabels(pivot_table.columns)
            self.ax.set_yticklabels(pivot_table.index)
            
            # Rotate x-labels
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add colorbar
            cbar = self.figure.colorbar(im, ax=self.ax)
            cbar.set_label(value_column)
            
            # Add title
            self.ax.set_title(title)
            
            self.figure.tight_layout()
            
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Cannot create heatmap: {str(e)}", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes)
            self.ax.set_title(title) 