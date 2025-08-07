# Roadmap Master

A comprehensive application for creating, managing, and evolving project and life roadmaps with interactive visualizations and powerful planning features.

## Features

- **Dynamic Roadmap Creation**: Create milestones and tasks with intuitive timeline visualization
- **Task Dependency Management**: Track task dependencies with visual connectors
- **Critical Path Analysis**: Identify the critical path in your project workflows
- **Advanced Analytics & Reporting**: Visualize project progress and task distribution with interactive charts
- **Real-time Collaboration**: Work together with team members, leave comments, and share projects
- **Multiple Export Formats**: Export to PDF, Excel, CSV, HTML, iCalendar, and more
- **External Integrations**: Placeholder support for calendar and task management services
- **Multiple Visualization Types**: View your projects as timelines, Gantt charts, or mind maps
- **Customizable Interface**: Adjust timeline scales, color-code items, and organize by project
- **Progress Tracking**: Monitor completion progress and stay on top of deadlines
- **Dashboard Overview**: View summary statistics and performance metrics for your projects

## Installation

### Prerequisites

- Python 3.7 or higher
- PyQt5 and PyQtChart
- python-dateutil
- Optional: openpyxl (for Excel export), reportlab (for PDF export)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/roadmap-master.git
   cd roadmap-master
   ```

2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application:

```
python src/main.py
```

### Basic Workflow

1. **Create a Project**: Use the sidebar to add a new project
2. **Add Milestones and Tasks**: Right-click on a project to add milestones or tasks
3. **Set Dates and Properties**: Use the properties panel to set dates, descriptions, and colors
4. **Create Dependencies**: Use the dependency creation mode to link dependent tasks
5. **Visualize Critical Path**: Click the "Show Critical Path" button to highlight the critical path
6. **View Analytics**: Use the Analytics menu to access interactive reports and visualizations
7. **Collaborate**: Share projects, add comments, and track activity with the Collaboration menu
8. **Export Data**: Use the File menu to export your roadmap in various formats
9. **Track Progress**: Update task completion progress and view performance metrics

### Keyboard Shortcuts

- `Ctrl+N`: Create a new roadmap
- `Ctrl+S`: Save the current roadmap
- `Ctrl+O`: Open an existing roadmap
- `Ctrl++`: Zoom in on the timeline
- `Ctrl+-`: Zoom out on the timeline

## Development Roadmap

This project is under active development. Upcoming features include:

1. ✅ Core engine with basic roadmap visualization
2. ✅ Task management and dependency tracking
3. ✅ Advanced visualizations and analytics
4. ✅ Collaboration features
5. ✅ Integrations and exports
6. ⬜ Polish and performance optimization

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 