# Video Downloader

A Python application that allows you to download videos from URLs. Features include:

- Download videos from direct URLs
- Support for playlists - select which videos to download
- Progress bar to track download status
- Modern user interface
- Document manager for notes and transcripts
- Checklist manager for tasks
- PDF viewer with bookmarks

## Requirements

- Python 3.7+
- PyQt5
- PyQtWebEngine (for PDF viewing)
- pytube
- python-docx (for document export)

## Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python main.py
```

2. Enter a video URL or playlist URL in the input field and click "Load"
3. For playlists, select the videos you want to download using the checkboxes
4. Choose a save directory by clicking "Browse"
5. Click "Download Selected" to begin downloading

### PDF Viewer

The application includes a PDF viewer with bookmarking capabilities:

1. Go to the "PDFs" tab
2. Click "Open PDF" to select a PDF file
3. Use the navigation controls to browse through the document
4. Add bookmarks to remember important pages
5. Edit or remove bookmarks as needed

Bookmarks include:
- Title
- Page number
- Optional notes
- Quick navigation by double-clicking

## Features

- Checkbox selection for playlist videos
- Progress tracking for each download
- Select/deselect all buttons for convenience
- Error handling with detailed messages
- Modern UI with clear status indicators
- Document management for text notes and extracted video transcripts
- Checklist system for task management
- PDF viewer with bookmark functionality
- Dark/light theme support

## Troubleshooting

If you encounter issues:

- Make sure you have a stable internet connection
- Verify that the URL is valid and accessible
- Check that you have write permissions for the save directory
- Some videos may be restricted and cannot be downloaded
- For PDF viewing issues, ensure PyQtWebEngine is properly installed 