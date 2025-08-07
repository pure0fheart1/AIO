from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QScrollArea, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QIcon
import os
import json

CONFIG_DIR = os.path.expanduser("~/.aisuite")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class NavigationTree(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # To call methods like switch_to_page

        self.settings = QSettings("AISuite", "AppConfig") # Using QSettings for simplicity now, will move to json

        self._create_widgets()
        self._create_layout()
        self._create_connections()
        
        self.load_config() # Load expansion states and last page
        self.populate_tree()
        self.apply_initial_state()

    def _create_widgets(self):
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(15) # Adjust as needed
        self.tree_widget.setIconSize(QSize(16, 16)) # Chevron icon size

        # Scroll Area for the tree
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.tree_widget)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


    def _create_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

    def _create_connections(self):
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.itemExpanded.connect(self.save_expansion_state)
        self.tree_widget.itemCollapsed.connect(self.save_expansion_state)

    def _get_config(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {} # Return default if malformed
        return {}

    def _save_config(self, config_data):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def load_config(self):
        config = self._get_config()
        self.expanded_items_config = config.get("expanded_items", {})
        self.last_page_path_config = config.get("last_page_path", None)
        self.sidebar_collapsed_config = config.get("sidebar_collapsed", False)


    def save_expansion_state(self, item=None): # item can be passed but not always needed
        config = self._get_config()
        expanded_state = {}
        for i in range(self.tree_widget.topLevelItemCount()):
            top_item = self.tree_widget.topLevelItem(i)
            expanded_state[top_item.text(0)] = top_item.isExpanded()
        config["expanded_items"] = expanded_state
        self._save_config(config)

    def save_last_page(self, page_path_str):
        config = self._get_config()
        config["last_page_path"] = page_path_str
        self._save_config(config)
        self.last_page_path_config = page_path_str # Update internal state

    def save_sidebar_collapsed_state(self, collapsed):
        config = self._get_config()
        config["sidebar_collapsed"] = collapsed
        self._save_config(config)
        self.sidebar_collapsed_config = collapsed

    def get_item_path(self, item):
        path = [item.text(0)]
        parent = item.parent()
        while parent:
            path.insert(0, parent.text(0))
            parent = parent.parent()
        return "/".join(path)

    def find_item_by_path(self, path_str):
        parts = path_str.split("/")
        current_items = [self.tree_widget.topLevelItem(i) for i in range(self.tree_widget.topLevelItemCount())]
        
        found_item = None
        for part_index, part in enumerate(parts):
            item_found_at_level = False
            for item in current_items:
                if item and item.text(0) == part:
                    found_item = item
                    if part_index < len(parts) - 1: # If not the last part, get children
                        current_items = [found_item.child(i) for i in range(found_item.childCount())]
                    item_found_at_level = True
                    break
            if not item_found_at_level:
                return None
        return found_item

    def on_item_clicked(self, item, column):
        # Only leaf nodes (pages) should trigger page changes
        if item.childCount() == 0:
            page_widget_name = item.data(0, Qt.UserRole) # Store actual widget reference or name
            if page_widget_name and hasattr(self.parent_window, 'pages_map') and page_widget_name in self.parent_window.pages_map:
                target_widget = self.parent_window.pages_map[page_widget_name]["widget"]
                if target_widget:
                    self.parent_window.switch_to_page(target_widget)
                    self.save_last_page(self.get_item_path(item))
            elif page_widget_name: # For new stubbed pages
                print(f"Info: Page {page_widget_name} selected but not fully implemented yet.")
                # Potentially switch to a placeholder page or show a message
                self.save_last_page(self.get_item_path(item))


    def populate_tree(self):
        self.tree_widget.clear()
        
        # New logical folder structure
        structure = {
            "Tools": ["YouTube Downloader", "Universal Downloader", "Website Extractor", "Text Editor", "Text-to-Audio", "Audio Recorder", "Vocabulary Learner", "ChatGPT"],
            "Productivity": ["Projects", "Documents", "Script Prompts", "Checklists", "Transcripts", "Bookmarks", "Info Library"],
            "Creative": ["Image Gallery", "Video Player", "Games"],
            "Automation": ["Automator", "Auto-Organise"], # Renamed Task Automation
            "Analytics": ["Crypto Tracker", "Social Media"],
            "Finances": ["Budget Tracker", "Income Tracker"], # New
            "System": ["Settings", "Clock"]
        }

        # Mapping display names to actual widget names/keys used in main_window.pages
        # This will need to be updated as pages are moved to their own files.
        # For now, it reflects the keys in `self.pages` dictionary in VideoDownloader class
        self.page_name_to_widget_key = {
            "YouTube Downloader": "YouTube Downloader",
            "Universal Downloader": "Universal Downloader",
            "Website Extractor": "Website Extractor",
            "Text Editor": "Text Editor",
            "Text-to-Audio": "Text to Audio", # Key in main.py is "Text to Audio"
            "Audio Recorder": "Audio Recorder",
            "Vocabulary Learner": "Vocabulary Learner",
            "ChatGPT": "ChatGPT",
            "Projects": "Projects",
            "Documents": "Documents",
            "Script Prompts": "Script Prompts",
            "Checklists": "Checklists",
            "Transcripts": "Transcripts",
            "Bookmarks": "Bookmarks",
            "Info Library": "Info Library",
            "Image Gallery": "Image Gallery",
            "Video Player": "Video Player",
            "Games": "Games",
            "Automator": "Task Automation", # Original key for "Task Automation"
            "Auto-Organise": "Auto-Organise",
            "Crypto Tracker": "Crypto Tracker",
            "Social Media": "Social Media",
            "Budget Tracker": "Budget Tracker", # New page
            "Income Tracker": "Income Tracker", # New page
            "Settings": "Settings",
            "Clock": "Clock"
        }


        for top_level_name, children in structure.items():
            parent_item = QTreeWidgetItem(self.tree_widget, [top_level_name])
            parent_item.setIcon(0, QIcon.fromTheme("folder")) # Placeholder, use QStyle later for chevrons
            parent_item.setExpanded(self.expanded_items_config.get(top_level_name, False))

            for child_name in children:
                child_item = QTreeWidgetItem(parent_item, [child_name])
                widget_key = self.page_name_to_widget_key.get(child_name)
                
                # Try to get icon from main window's page definition
                icon = QIcon()
                if hasattr(self.parent_window, 'pages_map') and widget_key in self.parent_window.pages_map:
                     icon_name = self.parent_window.pages_map[widget_key].get("icon_name")
                     if icon_name:
                         icon = QIcon.fromTheme(icon_name)
                
                if not icon.isNull():
                    child_item.setIcon(0, icon)
                else:
                    # Fallback icon if main window or page doesn't have one specified yet
                    child_item.setIcon(0, QIcon.fromTheme("document-new")) # Placeholder

                child_item.setData(0, Qt.UserRole, widget_key) # Store widget key

        self.tree_widget.expandAll() # Temp for testing, will use saved state

    def apply_initial_state(self):
        # Expand items based on config
        for i in range(self.tree_widget.topLevelItemCount()):
            top_item = self.tree_widget.topLevelItem(i)
            if self.expanded_items_config.get(top_item.text(0), False):
                top_item.setExpanded(True)
            else:
                top_item.setExpanded(False)
        
        # Select last opened page
        if self.last_page_path_config:
            item_to_select = self.find_item_by_path(self.last_page_path_config)
            if item_to_select:
                self.tree_widget.setCurrentItem(item_to_select)
                # Also trigger the page switch if the parent window is fully set up
                if hasattr(self.parent_window, 'stacked_widget') and item_to_select.childCount() == 0:
                     page_widget_name = item_to_select.data(0, Qt.UserRole)
                     if page_widget_name and hasattr(self.parent_window, 'pages_map') and page_widget_name in self.parent_window.pages_map:
                         target_widget = self.parent_window.pages_map[page_widget_name]["widget"]
                         if target_widget:
                             self.parent_window.switch_to_page(target_widget, force_switch=True)


    def set_icons_only_mode(self, icons_only):
        """
        Switches the sidebar to an icons-only mode or back.
        """
        self.icons_only_mode = icons_only
        if icons_only:
            self.tree_widget.setIndentation(5) # Smaller indentation
            for i in range(self.tree_widget.topLevelItemCount()):
                top_item = self.tree_widget.topLevelItem(i)
                top_item.setText(0, "") # Hide text for top-level
                # For children, we might want to show tooltips or handle differently
                for j in range(top_item.childCount()):
                    child_item = top_item.child(j)
                    original_text = self.page_name_to_widget_key.get(child_item.data(0, Qt.UserRole), child_item.data(0, Qt.UserRole))
                    child_item.setToolTip(0, original_text or "") # Show original text as tooltip
                    child_item.setText(0, "") # Hide text
            self.setFixedWidth(60) # Arbitrary width for icons-only
        else:
            self.tree_widget.setIndentation(15)
            # Repopulate to restore text, or store original text and restore
            self.populate_tree() # This re-adds text
            self.apply_initial_state() # Re-apply expansion and selection
            self.setMinimumWidth(200) # Restore default width
            self.setMaximumWidth(400) # Example max width

        self.save_sidebar_collapsed_state(icons_only)


    def update_page_map_and_icons(self, pages_map):
        """
        Call this after the main window has fully initialized its pages_map.
        This method will update the icons in the tree based on the final
        page configurations.
        """
        if not hasattr(self, 'page_name_to_widget_key'): # Ensure populated first
            return

        for i in range(self.tree_widget.topLevelItemCount()):
            top_item = self.tree_widget.topLevelItem(i)
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                display_name = child_item.text(0) # This is how it was originally set
                
                # Find the original display name if it was cleared by icons_only_mode
                # This is a bit tricky because populate_tree might run after icons_only_mode
                # We need a reliable way to get the display name to look up the widget_key.
                # The UserRole data should hold the widget_key.
                
                widget_key = child_item.data(0, Qt.UserRole)

                icon = QIcon()
                if widget_key and pages_map and widget_key in pages_map:
                    icon_name = pages_map[widget_key].get("icon_name")
                    if icon_name:
                        new_icon = QIcon.fromTheme(icon_name)
                        if not new_icon.isNull():
                            icon = new_icon
                        else:
                            print(f"Sidebar: Icon '{icon_name}' for '{widget_key}' not found, using fallback.")
                            icon = QIcon.fromTheme("application-x-executable") # A generic fallback
                    else: # No icon_name specified
                         icon = QIcon.fromTheme("text-x-generic") # Fallback if no icon name
                else: # widget_key not in map or map not ready
                    icon = QIcon.fromTheme("unknown")


                if not icon.isNull():
                    child_item.setIcon(0, icon)
                # else:
                    # print(f"Sidebar: Still no valid icon for {widget_key} ({display_name}).")
