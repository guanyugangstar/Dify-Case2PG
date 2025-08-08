# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an administrative case database entry system (v3.0) built with Flask. The system supports batch uploading of multiple file formats (images, PDF, Word, TXT, etc.) and PC camera photo uploads. It automatically calls a local Dify workflow for image recognition, OCR, and intelligent parsing to extract structured information, which is then stored in a PostgreSQL database and displayed through a web interface.

Key features:
- Multi-format file upload (PDF, Word, TXT, images, etc.)
- PC camera photo capture and upload
- Integration with local Dify workflows for intelligent document parsing
- PostgreSQL database storage and retrieval
- Streamed SSE (Server-Sent Events) experience for real-time processing feedback
- Modern Apple-style UI with responsive design
- Database table visualization in modal popups
- Excel export functionality

## Development Commands

### Installation and Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
2. Start the Flask server:
   ```bash
   python app.py
   ```

3. Access the application at http://localhost:8888

### Alternative Setup (Windows)
Double-click the `start.bat` script which will:
- Create a virtual environment
- Install all dependencies
- Start the Flask service

## Code Architecture

### Backend (app.py)
- Flask application with three main routes:
  1. `/` - Serves the main HTML page
  2. `/upload` - Handles file uploads, Dify workflow integration, and SSE streaming
  3. `/get_table_data` - Queries PostgreSQL database and returns structured data
- Key components:
  - Dify API integration (file upload and workflow execution)
  - PostgreSQL database connectivity
  - SSE streaming implementation for real-time feedback
  - File type mapping and handling
  - Dynamic table selection based on Dify workflow output

### Frontend (templates/index.html)
- Modern Apple-style UI with responsive design
- Key functionality:
  - Multi-file selection and upload
  - Camera photo capture interface
  - SSE stream processing and display
  - Modal popup for database table visualization
  - Excel export functionality
  - Responsive table display with horizontal scrolling
  - Cell content preview and copy functionality

### Static Assets (static/)
- CSS styling (style.css)
- SheetJS library for Excel export (xlsx.full.min.js)
- UI images and icons

## Key Implementation Details

### Dify Workflow Integration
1. Files are first uploaded to Dify via `/v1/files/upload`
2. Uploaded file IDs are then used to trigger a workflow via `/v1/workflows/run`
3. Results are streamed back using Server-Sent Events (SSE)
4. Only the final `workflow_finished` event is displayed to the user

### Database Interaction
- PostgreSQL connection configured in `DB_CONFIG`
- Dynamic table selection based on Dify workflow classification output
- Table mapping: Contract→contract_summary, Review→reconsideration_summary, Litigation→case_summary

### Camera Upload Feature
- Uses MediaDevices API for camera access
- Captures photos and converts them to File objects
- Photos can be deleted before confirmation
- Confirmed photos are added to the main upload queue

### UI/UX Features
- Streamed processing results with real-time display
- Modal popup for database table visualization
- Responsive table design with horizontal scrolling
- Cell content truncation with modal preview for long content
- Excel export with custom styling and column widths