import sys
import os
import time
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QComboBox, QTabWidget, QListWidget, QListWidgetItem,
                            QTimeEdit, QSpinBox, QFileDialog, QMessageBox, 
                            QProgressBar, QSlider, QCheckBox, QGroupBox, QGridLayout,
                            QListView, QFormLayout, QLineEdit, QDateTimeEdit)
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class DigitalClock(QLabel):
    """A digital clock widget showing current time"""
    def __init__(self, timezone=None, timezone_name=None, parent=None):
        super().__init__(parent)
        self.timezone = timezone  # For world clocks, can be None for local time
        self.timezone_name = timezone_name or "Local Time"
        
        # Set up appearance
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 36, QFont.Bold))
        self.setStyleSheet("color: #4a86e8;")
        
        # Start timer to update every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # Initial time display
        self.update_time()
    
    def update_time(self):
        """Update the displayed time"""
        if self.timezone:
            # World clock with specific timezone
            current_time = datetime.datetime.now(self.timezone)
        else:
            # Local time
            current_time = datetime.datetime.now()
            
        time_text = current_time.strftime("%H:%M:%S")
        date_text = current_time.strftime("%A, %B %d, %Y")
        
        self.setText(f"{self.timezone_name}<br>{time_text}<br><span style='font-size: 14px;'>{date_text}</span>")

class WorldClockWidget(QWidget):
    """Widget for displaying multiple world clocks"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # World clock controls
        controls_layout = QHBoxLayout()
        
        # Timezone selector
        self.timezone_combo = QComboBox()
        self.populate_timezones()
        
        # Add button
        self.add_clock_button = QPushButton("Add Clock")
        self.add_clock_button.clicked.connect(self.add_world_clock)
        
        controls_layout.addWidget(QLabel("Add Timezone:"))
        controls_layout.addWidget(self.timezone_combo, 1)
        controls_layout.addWidget(self.add_clock_button)
        
        # Clock list section
        self.clock_list = QListWidget()
        self.clock_list.setMaximumHeight(200)
        
        # Remove clock button
        self.remove_clock_button = QPushButton("Remove Selected")
        self.remove_clock_button.clicked.connect(self.remove_world_clock)
        
        # Main local digital clock
        self.main_clock = DigitalClock()
        
        # Add default clocks
        self.add_default_clocks()
        
        # Add to layout
        layout.addWidget(self.main_clock)
        layout.addLayout(controls_layout)
        layout.addWidget(self.clock_list)
        layout.addWidget(self.remove_clock_button)
        layout.addStretch()
        
    def populate_timezones(self):
        """Populate the timezone dropdown with common timezones"""
        common_timezones = [
            ("US/Pacific", "Los Angeles (US/Pacific)"),
            ("US/Eastern", "New York (US/Eastern)"),
            ("Europe/London", "London (GMT/UTC)"),
            ("Europe/Paris", "Paris (CET)"),
            ("Asia/Tokyo", "Tokyo (JST)"),
            ("Asia/Shanghai", "Beijing (CST)"),
            ("Asia/Kolkata", "New Delhi (IST)"),
            ("Australia/Sydney", "Sydney (AEST)"),
            ("Pacific/Auckland", "Auckland (NZST)")
        ]
        
        for tz_code, tz_name in common_timezones:
            self.timezone_combo.addItem(tz_name, tz_code)
    
    def add_default_clocks(self):
        """Add a few default world clocks"""
        default_clocks = [
            ("US/Eastern", "New York"),
            ("Europe/London", "London"),
            ("Asia/Tokyo", "Tokyo")
        ]
        
        for tz_code, tz_name in default_clocks:
            try:
                timezone = datetime.timezone(datetime.timedelta(hours=0))  # Placeholder, would use pytz in real app
                item = QListWidgetItem(f"{tz_name} ({tz_code})")
                self.clock_list.addItem(item)
            except Exception as e:
                print(f"Error adding default clock {tz_name}: {e}")
    
    def add_world_clock(self):
        """Add a new world clock based on selected timezone"""
        selected_index = self.timezone_combo.currentIndex()
        if selected_index >= 0:
            tz_code = self.timezone_combo.itemData(selected_index)
            tz_name = self.timezone_combo.itemText(selected_index)
            
            try:
                timezone = datetime.timezone(datetime.timedelta(hours=0))  # Placeholder, would use pytz in real app
                item = QListWidgetItem(tz_name)
                self.clock_list.addItem(item)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not add timezone: {e}")
    
    def remove_world_clock(self):
        """Remove the selected world clock"""
        selected_items = self.clock_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.clock_list.takeItem(self.clock_list.row(item))

class TimerWidget(QWidget):
    """Timer (countdown) widget"""
    timer_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.remaining_seconds = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Timer display
        self.timer_display = QLabel("00:00:00")
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setFont(QFont("Arial", 48, QFont.Bold))
        self.timer_display.setStyleSheet("color: #4a86e8;")
        
        # Timer controls
        controls_layout = QHBoxLayout()
        
        # Time input
        time_layout = QHBoxLayout()
        
        self.hours_input = QSpinBox()
        self.hours_input.setRange(0, 23)
        self.hours_input.setSuffix(" hours")
        
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(0, 59)
        self.minutes_input.setSuffix(" min")
        
        self.seconds_input = QSpinBox()
        self.seconds_input.setRange(0, 59)
        self.seconds_input.setSuffix(" sec")
        
        time_layout.addWidget(self.hours_input)
        time_layout.addWidget(self.minutes_input)
        time_layout.addWidget(self.seconds_input)
        
        # Timer buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_timer)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.reset_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        
        self.preset_1min = QPushButton("1 min")
        self.preset_1min.clicked.connect(lambda: self.set_preset_time(0, 1, 0))
        
        self.preset_5min = QPushButton("5 min")
        self.preset_5min.clicked.connect(lambda: self.set_preset_time(0, 5, 0))
        
        self.preset_10min = QPushButton("10 min")
        self.preset_10min.clicked.connect(lambda: self.set_preset_time(0, 10, 0))
        
        self.preset_30min = QPushButton("30 min")
        self.preset_30min.clicked.connect(lambda: self.set_preset_time(0, 30, 0))
        
        preset_layout.addWidget(self.preset_1min)
        preset_layout.addWidget(self.preset_5min)
        preset_layout.addWidget(self.preset_10min)
        preset_layout.addWidget(self.preset_30min)
        
        # Add to main layout
        layout.addWidget(self.timer_display)
        layout.addLayout(time_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(preset_layout)
        layout.addStretch()
    
    def set_preset_time(self, hours, minutes, seconds):
        """Set the timer inputs to a preset time"""
        self.hours_input.setValue(hours)
        self.minutes_input.setValue(minutes)
        self.seconds_input.setValue(seconds)
    
    def start_timer(self):
        """Start the countdown timer"""
        hours = self.hours_input.value()
        minutes = self.minutes_input.value()
        seconds = self.seconds_input.value()
        
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        if total_seconds <= 0:
            QMessageBox.warning(self, "Invalid Time", "Please set a time greater than zero.")
            return
        
        # Set remaining time and max for progress calculations
        self.remaining_seconds = total_seconds
        self.max_seconds = total_seconds
        
        # Update UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText("Pause")
        self.hours_input.setEnabled(False)
        self.minutes_input.setEnabled(False)
        self.seconds_input.setEnabled(False)
        
        # Start timer to update every second
        self.timer.start(1000)
        self.update_timer_display()
    
    def pause_timer(self):
        """Pause or resume the timer"""
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Resume")
        else:
            self.timer.start(1000)
            self.pause_button.setText("Pause")
    
    def reset_timer(self):
        """Reset the timer to initial state"""
        self.timer.stop()
        self.remaining_seconds = 0
        
        # Reset UI
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("Pause")
        self.hours_input.setEnabled(True)
        self.minutes_input.setEnabled(True)
        self.seconds_input.setEnabled(True)
        
        self.progress_bar.setValue(0)
        self.timer_display.setText("00:00:00")
    
    def update_timer(self):
        """Update the timer every second"""
        self.remaining_seconds -= 1
        
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.timer_display.setText("00:00:00")
            self.progress_bar.setValue(100)
            
            # Emit finished signal
            self.timer_finished.emit()
            
            # Reset UI
            self.reset_timer()
            
            # Show timer finished message
            QMessageBox.information(self, "Timer Complete", "The timer has finished!")
            return
        
        # Update UI
        self.update_timer_display()
        
        # Update progress bar
        progress = 100 - int((self.remaining_seconds / self.max_seconds) * 100)
        self.progress_bar.setValue(progress)
    
    def update_timer_display(self):
        """Update the timer display with current remaining time"""
        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_display.setText(time_str)

class StopwatchWidget(QWidget):
    """Stopwatch widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.elapsed_msec = 0
        self.laps = []
        
        # Timer updating 10 times per second for centisecond precision
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stopwatch)
        self.timer.setInterval(100)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Stopwatch display
        self.stopwatch_display = QLabel("00:00:00.00")
        self.stopwatch_display.setAlignment(Qt.AlignCenter)
        self.stopwatch_display.setFont(QFont("Arial", 48, QFont.Bold))
        self.stopwatch_display.setStyleSheet("color: #4a86e8;")
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_stopwatch)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_stopwatch)
        self.pause_button.setEnabled(False)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_stopwatch)
        
        self.lap_button = QPushButton("Lap")
        self.lap_button.clicked.connect(self.record_lap)
        self.lap_button.setEnabled(False)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.lap_button)
        
        # Lap list
        lap_group = QGroupBox("Laps")
        lap_layout = QVBoxLayout()
        
        self.lap_list = QListWidget()
        self.clear_laps_button = QPushButton("Clear Laps")
        self.clear_laps_button.clicked.connect(self.clear_laps)
        
        lap_layout.addWidget(self.lap_list)
        lap_layout.addWidget(self.clear_laps_button)
        lap_group.setLayout(lap_layout)
        
        # Add to main layout
        layout.addWidget(self.stopwatch_display)
        layout.addLayout(controls_layout)
        layout.addWidget(lap_group)
    
    def start_stopwatch(self):
        """Start the stopwatch"""
        # If starting from zero
        if not self.timer.isActive() and self.elapsed_msec == 0:
            self.start_time = QDateTime.currentDateTime()
        
        # If resuming from pause
        elif not self.timer.isActive():
            # Adjust start time to account for elapsed time so far
            current_time = QDateTime.currentDateTime()
            time_diff = self.start_time.msecsTo(current_time) - self.elapsed_msec
            self.start_time = current_time.addMSecs(-time_diff)
        
        # Start timer
        self.timer.start()
        
        # Update UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.lap_button.setEnabled(True)
    
    def pause_stopwatch(self):
        """Pause the stopwatch"""
        self.timer.stop()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.start_button.setText("Resume")
        self.pause_button.setEnabled(False)
        self.lap_button.setEnabled(False)
    
    def reset_stopwatch(self):
        """Reset the stopwatch to zero"""
        self.timer.stop()
        self.elapsed_msec = 0
        self.stopwatch_display.setText("00:00:00.00")
        
        # Reset UI
        self.start_button.setEnabled(True)
        self.start_button.setText("Start")
        self.pause_button.setEnabled(False)
        self.lap_button.setEnabled(False)
    
    def update_stopwatch(self):
        """Update the stopwatch display"""
        current_time = QDateTime.currentDateTime()
        self.elapsed_msec = self.start_time.msecsTo(current_time)
        
        # Format time display
        hours = self.elapsed_msec // 3600000
        minutes = (self.elapsed_msec % 3600000) // 60000
        seconds = (self.elapsed_msec % 60000) // 1000
        msec = (self.elapsed_msec % 1000) // 10  # Show only centiseconds
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{msec:02d}"
        self.stopwatch_display.setText(time_str)
    
    def record_lap(self):
        """Record current time as a lap"""
        current_lap = self.elapsed_msec
        lap_number = len(self.laps) + 1
        
        # Calculate lap duration
        if self.laps:
            lap_duration = current_lap - self.laps[-1]["total_time"]
        else:
            lap_duration = current_lap
        
        # Add to laps list
        self.laps.append({
            "number": lap_number,
            "total_time": current_lap,
            "lap_time": lap_duration
        })
        
        # Format lap time for display
        total_hours = current_lap // 3600000
        total_minutes = (current_lap % 3600000) // 60000
        total_seconds = (current_lap % 60000) // 1000
        total_msec = (current_lap % 1000) // 10
        
        lap_hours = lap_duration // 3600000
        lap_minutes = (lap_duration % 3600000) // 60000
        lap_seconds = (lap_duration % 60000) // 1000
        lap_msec = (lap_duration % 1000) // 10
        
        total_time_str = f"{total_hours:02d}:{total_minutes:02d}:{total_seconds:02d}.{total_msec:02d}"
        lap_time_str = f"{lap_hours:02d}:{lap_minutes:02d}:{lap_seconds:02d}.{lap_msec:02d}"
        
        # Add to list widget
        self.lap_list.insertItem(0, f"Lap {lap_number}: {lap_time_str} (Total: {total_time_str})")
    
    def clear_laps(self):
        """Clear all recorded laps"""
        self.laps = []
        self.lap_list.clear()

class AlarmWidget(QWidget):
    """Alarm clock widget with media support"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.alarms = []
        
        # Media player for alarms
        self.media_player = QMediaPlayer(self)
        
        # Timer to check alarms (checks every second)
        self.alarm_check_timer = QTimer(self)
        self.alarm_check_timer.timeout.connect(self.check_alarms)
        self.alarm_check_timer.start(1000)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Alarm list
        self.alarm_group = QGroupBox("Active Alarms")
        alarm_group_layout = QVBoxLayout()
        
        self.alarm_list = QListWidget()
        self.alarm_list.itemDoubleClicked.connect(self.edit_alarm)
        
        # Alarm controls
        alarm_buttons = QHBoxLayout()
        
        self.add_alarm_button = QPushButton("Add Alarm")
        self.add_alarm_button.clicked.connect(self.add_alarm)
        
        self.edit_alarm_button = QPushButton("Edit")
        self.edit_alarm_button.clicked.connect(self.edit_selected_alarm)
        
        self.remove_alarm_button = QPushButton("Remove")
        self.remove_alarm_button.clicked.connect(self.remove_alarm)
        
        alarm_buttons.addWidget(self.add_alarm_button)
        alarm_buttons.addWidget(self.edit_alarm_button)
        alarm_buttons.addWidget(self.remove_alarm_button)
        
        alarm_group_layout.addWidget(self.alarm_list)
        alarm_group_layout.addLayout(alarm_buttons)
        self.alarm_group.setLayout(alarm_group_layout)
        
        # Set alarm panel
        alarm_settings = QGroupBox("Set Alarm")
        alarm_settings_layout = QFormLayout()
        
        # Time setting
        self.alarm_time_edit = QTimeEdit()
        self.alarm_time_edit.setDisplayFormat("HH:mm")
        self.alarm_time_edit.setTime(QTime.currentTime().addSecs(60))  # Default to 1 minute from now
        
        # Alarm name
        self.alarm_name_edit = QLineEdit()
        self.alarm_name_edit.setPlaceholderText("Alarm Name")
        
        # Repeat options
        repeat_layout = QHBoxLayout()
        self.repeat_monday = QCheckBox("Mon")
        self.repeat_tuesday = QCheckBox("Tue")
        self.repeat_wednesday = QCheckBox("Wed")
        self.repeat_thursday = QCheckBox("Thu")
        self.repeat_friday = QCheckBox("Fri")
        self.repeat_saturday = QCheckBox("Sat")
        self.repeat_sunday = QCheckBox("Sun")
        
        repeat_layout.addWidget(self.repeat_monday)
        repeat_layout.addWidget(self.repeat_tuesday)
        repeat_layout.addWidget(self.repeat_wednesday)
        repeat_layout.addWidget(self.repeat_thursday)
        repeat_layout.addWidget(self.repeat_friday)
        repeat_layout.addWidget(self.repeat_saturday)
        repeat_layout.addWidget(self.repeat_sunday)
        
        # Custom alarm sound
        sound_layout = QHBoxLayout()
        
        self.alarm_sound_path = QLineEdit()
        self.alarm_sound_path.setReadOnly(True)
        self.alarm_sound_path.setPlaceholderText("Default Alarm Sound")
        
        self.browse_sound_button = QPushButton("Browse...")
        self.browse_sound_button.clicked.connect(self.browse_alarm_sound)
        
        sound_layout.addWidget(self.alarm_sound_path)
        sound_layout.addWidget(self.browse_sound_button)
        
        # Save button
        self.save_alarm_button = QPushButton("Save Alarm")
        self.save_alarm_button.clicked.connect(self.save_alarm)
        
        # Add to form layout
        alarm_settings_layout.addRow("Time:", self.alarm_time_edit)
        alarm_settings_layout.addRow("Name:", self.alarm_name_edit)
        alarm_settings_layout.addRow("Repeat:", repeat_layout)
        alarm_settings_layout.addRow("Sound:", sound_layout)
        alarm_settings_layout.addRow(self.save_alarm_button)
        
        alarm_settings.setLayout(alarm_settings_layout)
        
        # Add all to main layout
        layout.addWidget(self.alarm_group)
        layout.addWidget(alarm_settings)
    
    def browse_alarm_sound(self):
        """Open file dialog to select alarm sound or video"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Alarm Sound or Video",
            "",
            "Media Files (*.mp3 *.wav *.mp4 *.avi *.mkv);;All Files (*)"
        )
        
        if file_path:
            self.alarm_sound_path.setText(file_path)
    
    def add_alarm(self):
        """Add a new alarm"""
        # Reset form
        self.alarm_time_edit.setTime(QTime.currentTime().addSecs(60))
        self.alarm_name_edit.clear()
        self.alarm_sound_path.clear()
        
        # Uncheck repeat options
        self.repeat_monday.setChecked(False)
        self.repeat_tuesday.setChecked(False)
        self.repeat_wednesday.setChecked(False)
        self.repeat_thursday.setChecked(False)
        self.repeat_friday.setChecked(False)
        self.repeat_saturday.setChecked(False)
        self.repeat_sunday.setChecked(False)
    
    def save_alarm(self):
        """Save the current alarm settings"""
        # Get alarm settings
        alarm_time = self.alarm_time_edit.time()
        alarm_name = self.alarm_name_edit.text() or f"Alarm {len(self.alarms) + 1}"
        alarm_sound = self.alarm_sound_path.text() or "default"
        
        # Get repeat days
        repeat_days = []
        if self.repeat_monday.isChecked():
            repeat_days.append(0)  # Monday is 0
        if self.repeat_tuesday.isChecked():
            repeat_days.append(1)
        if self.repeat_wednesday.isChecked():
            repeat_days.append(2)
        if self.repeat_thursday.isChecked():
            repeat_days.append(3)
        if self.repeat_friday.isChecked():
            repeat_days.append(4)
        if self.repeat_saturday.isChecked():
            repeat_days.append(5)
        if self.repeat_sunday.isChecked():
            repeat_days.append(6)
        
        # Create alarm data
        alarm_data = {
            "name": alarm_name,
            "time": alarm_time.toString("HH:mm"),
            "sound": alarm_sound,
            "repeat_days": repeat_days,
            "active": True,
            "id": len(self.alarms)
        }
        
        # Add to alarms list
        self.alarms.append(alarm_data)
        
        # Add to UI list
        self.update_alarm_list()
        
        # Show confirmation
        QMessageBox.information(self, "Alarm Set", f"Alarm '{alarm_name}' set for {alarm_time.toString('HH:mm')}")
    
    def update_alarm_list(self):
        """Update the alarm list widget"""
        self.alarm_list.clear()
        
        for alarm in self.alarms:
            time_str = alarm["time"]
            name = alarm["name"]
            
            # Show repeat days
            repeat_text = ""
            if alarm["repeat_days"]:
                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                repeat_days = [days[day] for day in alarm["repeat_days"]]
                repeat_text = f" (Repeats: {', '.join(repeat_days)})"
            
            status = "Active" if alarm["active"] else "Inactive"
            
            item = QListWidgetItem(f"{name} - {time_str}{repeat_text} - {status}")
            item.setData(Qt.UserRole, alarm["id"])
            
            self.alarm_list.addItem(item)
    
    def edit_selected_alarm(self):
        """Edit the selected alarm"""
        selected_items = self.alarm_list.selectedItems()
        if selected_items:
            self.edit_alarm(selected_items[0])
    
    def edit_alarm(self, item):
        """Edit an existing alarm"""
        alarm_id = item.data(Qt.UserRole)
        
        for alarm in self.alarms:
            if alarm["id"] == alarm_id:
                # Populate form with alarm data
                self.alarm_time_edit.setTime(QTime.fromString(alarm["time"], "HH:mm"))
                self.alarm_name_edit.setText(alarm["name"])
                self.alarm_sound_path.setText(alarm["sound"] if alarm["sound"] != "default" else "")
                
                # Set repeat checkboxes
                self.repeat_monday.setChecked(0 in alarm["repeat_days"])
                self.repeat_tuesday.setChecked(1 in alarm["repeat_days"])
                self.repeat_wednesday.setChecked(2 in alarm["repeat_days"])
                self.repeat_thursday.setChecked(3 in alarm["repeat_days"])
                self.repeat_friday.setChecked(4 in alarm["repeat_days"])
                self.repeat_saturday.setChecked(5 in alarm["repeat_days"])
                self.repeat_sunday.setChecked(6 in alarm["repeat_days"])
                
                # Remove the alarm (will be replaced when saving)
                self.alarms.remove(alarm)
                break
    
    def remove_alarm(self):
        """Remove the selected alarm"""
        selected_items = self.alarm_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            alarm_id = item.data(Qt.UserRole)
            
            for alarm in self.alarms[:]:
                if alarm["id"] == alarm_id:
                    self.alarms.remove(alarm)
                    break
            
            self.update_alarm_list()
    
    def check_alarms(self):
        """Check if any alarms should trigger"""
        current_time = QTime.currentTime()
        current_day = datetime.datetime.now().weekday()  # 0 is Monday
        
        for alarm in self.alarms:
            if not alarm["active"]:
                continue
                
            alarm_time = QTime.fromString(alarm["time"], "HH:mm")
            
            # Check if alarm should trigger (within 1 minute)
            is_time_match = (alarm_time.hour() == current_time.hour() and 
                            alarm_time.minute() == current_time.minute())
            
            # Check if today is in repeat days or no repeat days set
            is_day_match = not alarm["repeat_days"] or current_day in alarm["repeat_days"]
            
            if is_time_match and is_day_match:
                self.trigger_alarm(alarm)
    
    def trigger_alarm(self, alarm):
        """Trigger the alarm with sound"""
        # Set alarm to inactive to prevent continuous triggering
        alarm["active"] = False
        self.update_alarm_list()
        
        # Get alarm sound
        sound_path = alarm["sound"]
        if sound_path and sound_path != "default":
            try:
                # Play custom sound/video
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))
                self.media_player.play()
            except Exception as e:
                print(f"Error playing alarm sound: {e}")
                # Fall back to system beep
                QApplication.beep()
        else:
            # Default system beep
            QApplication.beep()
        
        # Show alarm notification
        QMessageBox.information(self, "Alarm", f"Alarm: {alarm['name']}")
        
        # If this is a repeating alarm, re-activate it
        if alarm["repeat_days"]:
            alarm["active"] = True
            self.update_alarm_list()

class ClockWidget(QWidget):
    """Main clock widget containing all clock functions"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.clock_tab = WorldClockWidget()
        self.timer_tab = TimerWidget()
        self.stopwatch_tab = StopwatchWidget()
        self.alarm_tab = AlarmWidget()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.clock_tab, "Clock")
        self.tab_widget.addTab(self.timer_tab, "Timer")
        self.tab_widget.addTab(self.stopwatch_tab, "Stopwatch")
        self.tab_widget.addTab(self.alarm_tab, "Alarm")
        
        # Connect timer finished signal to alarm
        self.timer_tab.timer_finished.connect(self.on_timer_finished)
        
        # Add to layout
        layout.addWidget(self.tab_widget)
    
    def on_timer_finished(self):
        """Handle timer finished signal"""
        QApplication.beep()  # System beep
        
        # Could also play custom sound here
        # self.alarm_tab.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))
        # self.alarm_tab.media_player.play()

# For standalone testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClockWidget()
    window.setWindowTitle("Clock")
    window.resize(600, 500)
    window.show()
    sys.exit(app.exec_()) 