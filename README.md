# 📊 Student Report Card Generator

## Overview
The **Student Report Card Generator** is a user-friendly and interactive web application built using **Streamlit**. This app simplifies the process of generating student report cards by allowing users to input student scores, analyze performance, assign grades, and download comprehensive reports in **CSV** and **PDF** formats. It provides a structured approach to evaluating student performance with detailed **charts and insights**.

## Features

### 📝 **Student Report Generation**
- Enter student name, class, and section.
- Manually input subject names and corresponding scores.
- Bulk upload subject scores using a CSV file for quick data entry.

### 📊 **Performance Analytics & Visualization**
- **Bar Chart** visualization of subject-wise scores for easy comparison.
- **Pie Chart** displaying grade distribution to highlight overall performance.
- **Automated Grade Assignment** with remarks based on performance.
- **Average Score Calculation** for quick performance assessment.

### 🎯 **Grade Assessment & Feedback**
- The system uses a predefined grading scale:
  - **A (90-100%)**: Excellent Performance! ✅ Keep up the great work!
  - **B (80-89%)**: Very Good! Stay consistent. 👍
  - **C (70-79%)**: Good, but there's room for improvement. 😊
  - **D (60-69%)**: Needs more effort to improve. 🧐
  - **F (Below 60%)**: Failed. Extra practice required. ❌
- Personalized **feedback messages** based on student performance.

### 📂 **Downloadable & Printable Reports**
- Download report cards in **CSV** format for record-keeping.
- Generate and download **PDF** versions of report cards.
- Maintain previous reports stored in **JSON format** for easy retrieval.

### 🎨 **User-Friendly Interface**
- Clean and modern UI with an intuitive layout.
- Interactive widgets for quick data input and report generation.
- Color-coded performance indicators for better clarity.

## Installation Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/muzaffar401/Student_Report_Card_App.git
cd Student_Report_Card_App
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Application
```bash
streamlit run main.py
```

## How to Use

1. **Enter Student Details**
   - Provide the student name, class, and section.
   - Choose either **manual entry** or **bulk upload** for subject scores.
2. **Generate Report**
   - Click on "Generate Report Card" to analyze performance.
   - View subject-wise performance analytics and grading.
3. **Download & Save Report**
   - Save the report as a CSV or PDF file for future reference.
   - Access previously generated reports stored in JSON format.

## System Requirements
Ensure you have the following Python libraries installed:
```bash
pip install streamlit pandas matplotlib fpdf numpy
```

## Technologies Used
- **Streamlit** - UI Development
- **Pandas** - Data Processing
- **Matplotlib** - Data Visualization
- **FPDF** - PDF Report Generation

## Screenshots
![Screenshot 2025-03-27 014443](https://github.com/user-attachments/assets/27f460c4-2a00-42d9-8332-440f6eb8b7e7)

## Contributions
Contributions are welcome! Feel free to submit **issues**, **feature requests**, or **pull requests** to improve this project.

## License
📜 This project is open-source and available under the **MIT License**.

