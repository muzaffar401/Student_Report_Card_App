import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import base64
import sqlite3
import os
from fpdf import FPDF
import tempfile
import uuid

# Constants
GRADE_SCALE = {
    "A": (90, 100, "Excellent Performance!", "#00FF41"),
    "B": (80, 89, "Very Good! Keep it up.", "#00E676"),
    "C": (70, 79, "Good, but there's room for improvement.", "#FFEA00"),
    "D": (60, 69, "Needs more effort.", "#FF9100"),
    "F": (0, 59, "Failed. Please work harder.", "#FF1744"),
}

# Database Setup
def init_db():
    conn = sqlite3.connect('report_cards.db')
    c = conn.cursor()
    
    # Create reports table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (id TEXT PRIMARY KEY,
                  student_name TEXT,
                  class_section TEXT,
                  date TEXT,
                  total_marks INTEGER,
                  average REAL,
                  grade TEXT,
                  remarks TEXT,
                  grade_color TEXT)''')
    
    # Create subjects table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS subjects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  report_id TEXT,
                  subject_name TEXT,
                  score INTEGER,
                  FOREIGN KEY(report_id) REFERENCES reports(id))''')
    
    conn.commit()
    conn.close()

def save_report(report_data):
    conn = sqlite3.connect('report_cards.db')
    c = conn.cursor()
    
    # Insert report data
    c.execute('''INSERT INTO reports 
                 (id, student_name, class_section, date, total_marks, average, grade, remarks, grade_color)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (report_data['id'],
               report_data['student_name'],
               report_data['class_section'],
               report_data['date'],
               report_data['total_marks'],
               report_data['average'],
               report_data['grade'],
               report_data['remarks'],
               report_data['grade_color']))
    
    # Insert subjects data
    for subject, score in report_data['subjects'].items():
        c.execute('''INSERT INTO subjects (report_id, subject_name, score)
                     VALUES (?, ?, ?)''',
                  (report_data['id'], subject, score))
    
    conn.commit()
    conn.close()

def load_previous_reports():
    conn = sqlite3.connect('report_cards.db')
    c = conn.cursor()
    
    # Get all reports
    c.execute('''SELECT * FROM reports ORDER BY date DESC''')
    reports_data = c.fetchall()
    
    reports = []
    for report in reports_data:
        # Get subjects for this report
        c.execute('''SELECT subject_name, score FROM subjects 
                     WHERE report_id = ?''', (report[0],))
        subjects_data = c.fetchall()
        
        # Convert to dictionary format
        subjects = {subject: score for subject, score in subjects_data}
        
        reports.append({
            'id': report[0],
            'student_name': report[1],
            'class_section': report[2],
            'date': report[3],
            'total_marks': report[4],
            'average': report[5],
            'grade': report[6],
            'remarks': report[7],
            'grade_color': report[8],
            'subjects': subjects
        })
    
    conn.close()
    return reports

def delete_report(report_id):
    conn = sqlite3.connect('report_cards.db')
    c = conn.cursor()
    
    try:
        # Delete subjects first (foreign key constraint)
        c.execute('''DELETE FROM subjects WHERE report_id = ?''', (report_id,))
        # Then delete the report
        c.execute('''DELETE FROM reports WHERE id = ?''', (report_id,))
        conn.commit()
        success = True
    except:
        success = False
    finally:
        conn.close()
    
    return success

def update_report(report_data):
    conn = sqlite3.connect('report_cards.db')
    c = conn.cursor()
    
    try:
        # Update report data
        c.execute('''UPDATE reports 
                     SET student_name = ?,
                         class_section = ?,
                         date = ?,
                         total_marks = ?,
                         average = ?,
                         grade = ?,
                         remarks = ?,
                         grade_color = ?
                     WHERE id = ?''',
                  (report_data['student_name'],
                   report_data['class_section'],
                   report_data['date'],
                   report_data['total_marks'],
                   report_data['average'],
                   report_data['grade'],
                   report_data['remarks'],
                   report_data['grade_color'],
                   report_data['id']))
        
        # Delete existing subjects
        c.execute('''DELETE FROM subjects WHERE report_id = ?''', (report_data['id'],))
        
        # Insert new subjects
        for subject, score in report_data['subjects'].items():
            c.execute('''INSERT INTO subjects (report_id, subject_name, score)
                         VALUES (?, ?, ?)''',
                      (report_data['id'], subject, score))
        
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error updating report: {e}")
        success = False
    finally:
        conn.close()
    
    return success

# Initialize database
init_db()

def calculate_average(scores):
    return sum(scores) / len(scores) if scores else 0

def assign_grade(average):
    for grade, (low, high, remark, color) in GRADE_SCALE.items():
        if low <= average <= high:
            return grade, remark, color
    return "F", "Invalid score", "#FF1744"

def generate_bar_chart(subject_scores):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    subjects = list(subject_scores.keys())
    scores = list(subject_scores.values())

    # Assign colors based on score ranges
    colors = []
    for score in scores:
        for grade, (low, high, _, color) in GRADE_SCALE.items():
            if low <= score <= high:
                colors.append(color)
                break

    bars = ax.bar(subjects, scores, color=colors, edgecolor='white', linewidth=1)
    ax.set_facecolor('#121212')
    fig.patch.set_facecolor('#121212')
    ax.set_ylabel("Scores (out of 100)", color='white')
    ax.set_title("Subject-wise Performance", color='white', pad=20)
    ax.set_ylim(0, 110)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
            color='white',
            fontweight='bold'
        )

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig

def generate_pie_chart(subject_scores):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 8))
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

    for score in subject_scores.values():
        for grade, (low, high, _, _) in GRADE_SCALE.items():
            if low <= score <= high:
                grade_counts[grade] += 1
                break

    labels = []
    sizes = []
    colors = []
    explode = []

    for grade, count in grade_counts.items():
        if count > 0:
            labels.append(f"{grade} ({count})")
            sizes.append(count)
            colors.append(GRADE_SCALE[grade][3])
            explode.append(0.1 if count == max(grade_counts.values()) else 0)

    if sizes:
        wedges, texts, autotexts = ax.pie(
            sizes,
            explode=explode,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            shadow=True,
            startangle=140,
            textprops={'color': 'white', 'fontweight': 'bold'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        ax.set_title("Grade Distribution", color='white', pad=20)
        ax.axis("equal")
    else:
        ax.text(0.5, 0.5, "No data to display", ha="center", va="center", color='white')

    fig.patch.set_facecolor('#121212')
    return fig

def get_table_download_link(df, filename="report_card.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'''
    <a href="data:file/csv;base64,{b64}" download="{filename}" 
       class="download-button">
        📥 Download CSV File
    </a>
    '''
    return href

def generate_pdf_report(report_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(
        200, 10, txt=f"Report Card for {report_data['student_name']}", ln=1, align="C"
    )
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {report_data['date']}", ln=1, align="C")
    pdf.cell(
        200,
        10,
        txt=f"Class: {report_data.get('class_section', 'N/A')}",
        ln=1,
        align="C",
    )

    # Summary
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="Summary", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Average Score: {report_data['average']:.2f}%", ln=1)
    pdf.cell(
        200,
        10,
        txt=f"Total Marks: {report_data.get('total_marks', sum(report_data['subjects'].values()))}/{len(report_data['subjects']) * 100}",
        ln=1,
    )
    pdf.cell(200, 10, txt=f"Overall Grade: {report_data['grade']}", ln=1)
    pdf.cell(200, 10, txt=f"Remarks: {report_data['remarks']}", ln=1)

    # Subjects
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="Subject-wise Scores", ln=1)
    pdf.set_font("Arial", size=12)

    for subject, score in report_data["subjects"].items():
        pdf.cell(200, 10, txt=f"{subject}: {score}/100", ln=1)

    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

def display_report_card(report, show_actions=True):
    """Helper function to display a report card"""
    # Safely get all values with defaults
    grade = report.get("grade", "N/A")
    student_name = report.get("student_name", "Unknown Student")
    date = report.get("date", "Unknown Date")
    class_section = report.get("class_section", "N/A")
    subjects = report.get("subjects", {})
    remarks = report.get("remarks", "No remarks available")
    report_id = report.get("id", str(uuid.uuid4()))

    # Calculate derived values safely
    total_marks = report.get("total_marks", sum(subjects.values()) if subjects else 0)
    num_subjects = len(subjects)
    average = report.get(
        "average", calculate_average(list(subjects.values())) if subjects else 0
    )

    # Create a container with grade-specific styling
    grade_class = f"grade-{grade}"
    st.markdown(f'<div class="report-card {grade_class}">', unsafe_allow_html=True)

    st.subheader(f"📖 Report Card for {student_name}")
    st.caption(f"Class: {class_section} | Date: {date} | ID: {report_id[:8]}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Marks",
            f"{total_marks}/{num_subjects * 100}" if num_subjects > 0 else "N/A",
        )
    with col2:
        st.metric("Percentage", f"{average:.2f}%" if average else "N/A")
    with col3:
        st.metric("Grade", grade)

    if average:
        st.progress(average / 100)

    # Subject-wise performance
    if subjects:
        st.write("### 📚 Subject-wise Performance")
        for subject, score in subjects.items():
            col1, col2 = st.columns([1, 4])
            col1.write(f"**{subject}**")
            col2.progress(score / 100, text=f"{score}/100")

        # Visualizations
        st.write("### 📊 Performance Analytics")
        tab1, tab2 = st.tabs(["Bar Chart", "Grade Distribution"])

        with tab1:
            st.pyplot(generate_bar_chart(subjects))

        with tab2:
            st.pyplot(generate_pie_chart(subjects))
    else:
        st.warning("No subject data available")

    # Remarks
    st.write(f"### 📌 Remarks")
    st.success(remarks)

    # Action buttons (only shown if show_actions is True)
    if show_actions:
        st.write("### ⚙️ Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Update This Report", key=f"update_{report_id}"):
                st.session_state.editing_report = report
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete This Report", key=f"delete_{report_id}"):
                if delete_report(report_id):
                    st.success("Report deleted successfully!")
                    # Remove from session state if it's the current report
                    if "current_report" in st.session_state and st.session_state.current_report.get("id") == report_id:
                        st.session_state.current_report = None
                    # Reload reports
                    st.session_state.reports = load_previous_reports()
                    st.rerun()
                else:
                    st.error("Failed to delete report")

    st.markdown("</div>", unsafe_allow_html=True)

    # Download options
    if subjects:
        st.write("### 💾 Download Options")
        df = pd.DataFrame(
            {
                "Subject": subjects.keys(),
                "Score": subjects.values(),
                "Grade": [assign_grade(score)[0] for score in subjects.values()],
            }
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                get_table_download_link(df, f"{student_name}_report.csv"),
                unsafe_allow_html=True,
            )
        with col2:
            pdf_path = generate_pdf_report(report)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download as PDF",
                    data=f,
                    file_name=f"{student_name}_report.pdf",
                    mime="application/pdf",
                )
            os.unlink(pdf_path)

def edit_report_form(report):
    """Form for editing an existing report"""
    st.subheader(f"✏️ Editing Report for {report.get('student_name', 'Unknown Student')}")
    
    with st.form(key="edit_report_form"):
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input(
                "Student Name",
                value=report.get("student_name", ""),
                key="edit_student_name"
            )
        with col2:
            class_section = st.text_input(
                "Class/Section",
                value=report.get("class_section", ""),
                key="edit_class_section"
            )
        
        # Display existing subjects and allow editing
        st.write("Edit Subject Scores:")
        edited_subjects = {}
        
        for subject, score in report.get("subjects", {}).items():
            col1, col2 = st.columns([3, 1])
            with col1:
                new_subject = st.text_input(
                    "Subject",
                    value=subject,
                    key=f"subject_{subject}_edit"
                )
            with col2:
                new_score = st.number_input(
                    "Score",
                    min_value=0,
                    max_value=100,
                    value=score,
                    key=f"score_{subject}_edit"
                )
            if new_subject:  # Only add if subject name is not empty
                edited_subjects[new_subject] = new_score
        
        # Add new subject fields
        st.write("Add New Subjects (optional):")
        for i in range(2):  # Add 2 empty fields for new subjects
            col1, col2 = st.columns([3, 1])
            with col1:
                new_subject = st.text_input(
                    f"New Subject {i+1}",
                    value="",
                    key=f"new_subject_{i}"
                )
            with col2:
                new_score = st.number_input(
                    f"Score {i+1}",
                    min_value=0,
                    max_value=100,
                    value=0,
                    key=f"new_score_{i}"
                )
            if new_subject:  # Only add if subject name is not empty
                edited_subjects[new_subject] = new_score
        
        # Form submission buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            submit_edit = st.form_submit_button("💾 Save Changes")
        with col2:
            cancel_edit = st.form_submit_button("❌ Cancel")
        
        if submit_edit:
            if not student_name:
                st.error("Please enter student name")
                return
            
            if not edited_subjects:
                st.error("Please enter at least one subject with score")
                return
            
            # Calculate new values
            total_marks = sum(edited_subjects.values())
            average = calculate_average(list(edited_subjects.values()))
            grade, remarks, grade_color = assign_grade(average)
            
            # Update the report
            updated_report = {
                **report,
                "student_name": student_name,
                "class_section": class_section,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "subjects": edited_subjects,
                "total_marks": total_marks,
                "average": average,
                "grade": grade,
                "remarks": remarks,
                "grade_color": grade_color,
            }
            
            # Save the updated report
            if update_report(updated_report):
                st.success("Report updated successfully!")
                
                # Update session state
                st.session_state.current_report = updated_report
                st.session_state.reports = load_previous_reports()
                if "editing_report" in st.session_state:
                    del st.session_state.editing_report
                st.rerun()
            else:
                st.error("Failed to update report in database")
        
        if cancel_edit:
            if "editing_report" in st.session_state:
                del st.session_state.editing_report
            st.rerun()

def main():
    st.set_page_config(
        page_title="Student Report Card Generator", 
        page_icon="📊", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for Neon Purple Theme
    st.markdown(
        """
        <style>
        /* Main background with dark purple gradient */
        .stApp {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2a 100%);
            color: #ffffff;
        }
        
        /* Sidebar with purple glow */
        .css-1d391kg, .css-1oe5cao {
            background-color: #1a0a2a !important;
            border-right: 1px solid #9c27b0;
            box-shadow: 0 0 20px rgba(156, 39, 176, 0.5);
        }
        
        /* Headers with neon purple text glow */
        h1, h2, h3, h4, h5, h6 {
            color: #e100ff !important;
            text-shadow: 0 0 10px rgba(225, 0, 255, 0.7);
        }
        
        /* Body text */
        body, .stMarkdown, .st-b7, .stText, .stMarkdown p, .stMarkdown li {
            color: #f0d0ff !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Input fields with purple glow */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #1e0a3a !important;
            color: #ffffff !important;
            border: 1px solid #9c27b0 !important;
            border-radius: 6px !important;
            box-shadow: 0 0 10px rgba(156, 39, 176, 0.3);
            transition: all 0.3s ease;
        }
        
        .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
            box-shadow: 0 0 15px rgba(156, 39, 176, 0.7);
            outline: none;
            border-color: #e100ff !important;
        }
        
        /* Neon purple buttons with glow effect */
        .stButton>button {
            background-color: #9c27b0 !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: bold;
            border-radius: 6px;
            transition: all 0.3s;
            box-shadow: 0 0 10px rgba(156, 39, 176, 0.5);
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
        }
        
        .stButton>button:hover {
            background-color: #e100ff !important;
            box-shadow: 0 0 20px rgba(225, 0, 255, 0.8);
            transform: translateY(-1px);
        }
        
        .stButton>button:active {
            transform: translateY(0);
            box-shadow: 0 0 15px rgba(225, 0, 255, 0.6);
        }
        
        /* Progress bars with neon purple gradient */
        .stProgress>div>div>div>div {
            background: linear-gradient(90deg, #9c27b0 0%, #e100ff 100%) !important;
            border-radius: 4px;
            box-shadow: 0 0 5px rgba(225, 0, 255, 0.5);
        }
        
        /* Tabs with neon purple underline */
        .stTabs>div>div>div>div {
            background-color: transparent !important;
            color: #d0a0ff !important;
            transition: all 0.3s;
            padding: 10px 20px;
        }
        
        .stTabs>div>div>div>div[aria-selected="true"] {
            color: #e100ff !important;
            background-color: rgba(156, 39, 176, 0.1) !important;
            position: relative;
            text-shadow: 0 0 5px rgba(225, 0, 255, 0.5);
        }
        
        .stTabs>div>div>div>div[aria-selected="true"]::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 50%;
            height: 3px;
            background: #e100ff;
            border-radius: 3px;
            box-shadow: 0 0 10px rgba(225, 0, 255, 0.7);
        }
        
        /* Report card styling with purple glass morphism */
        .report-card {
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            background: rgba(30, 10, 50, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(156, 39, 176, 0.6);
            box-shadow: 0 8px 32px rgba(156, 39, 176, 0.3);
            transition: all 0.3s ease;
        }
        
        .report-card:hover {
            box-shadow: 0 8px 32px rgba(225, 0, 255, 0.4);
            transform: translateY(-2px);
            border-color: #e100ff;
        }
        
        .grade-A { border-color: #e100ff; box-shadow: 0 8px 32px rgba(225, 0, 255, 0.3); }
        .grade-B { border-color: #c700ff; box-shadow: 0 8px 32px rgba(199, 0, 255, 0.3); }
        .grade-C { border-color: #a100ff; box-shadow: 0 8px 32px rgba(161, 0, 255, 0.3); }
        .grade-D { border-color: #7b00ff; box-shadow: 0 8px 32px rgba(123, 0, 255, 0.3); }
        .grade-F { border-color: #ff00e1; box-shadow: 0 8px 32px rgba(255, 0, 225, 0.3); }
        
        /* Metric cards with purple glow */
        .stMetric {
            background: rgba(30, 10, 50, 0.7);
            border: 1px solid rgba(156, 39, 176, 0.6);
            border-radius: 10px;
            padding: 15px;
            backdrop-filter: blur(5px);
            transition: all 0.3s;
            box-shadow: 0 0 15px rgba(156, 39, 176, 0.2);
        }
        
        .stMetric:hover {
            box-shadow: 0 0 25px rgba(225, 0, 255, 0.3);
            border-color: #e100ff;
        }
        
        /* Radio buttons with neon purple theme */
        .stRadio>div>div {
            background-color: rgba(30, 10, 50, 0.7) !important;
            border: 1px solid rgba(156, 39, 176, 0.6) !important;
            border-radius: 10px !important;
            padding: 10px;
            backdrop-filter: blur(5px);
            box-shadow: 0 0 10px rgba(156, 39, 176, 0.2);
        }
        
        .stRadio>div>label>div:first-child {
            background-color: #9c27b0 !important;
            box-shadow: 0 0 10px rgba(156, 39, 176, 0.8);
        }
        
        /* Expander with neon purple border */
        .stExpander {
            border: 1px solid rgba(156, 39, 176, 0.6) !important;
            border-radius: 10px !important;
            background: rgba(30, 10, 50, 0.7) !important;
            backdrop-filter: blur(5px);
            margin-bottom: 15px;
            box-shadow: 0 0 15px rgba(156, 39, 176, 0.2);
        }
        
        .stExpander>div>div>div {
            background-color: transparent !important;
        }
        
        /* Custom purple scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a0a2a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #9c27b0;
            border-radius: 4px;
            box-shadow: 0 0 5px rgba(225, 0, 255, 0.5);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #e100ff;
        }
        
        /* Tooltip styling */
        .stTooltip {
            background-color: #1e0a3a !important;
            border: 1px solid #e100ff !important;
            color: white !important;
            box-shadow: 0 0 15px rgba(225, 0, 255, 0.3);
        }
        
        /* Custom checkbox */
        .stCheckbox>div>label>div:first-child {
            background-color: #1e0a3a !important;
            border: 1px solid #9c27b0 !important;
            box-shadow: 0 0 5px rgba(156, 39, 176, 0.3);
        }
        
        .stCheckbox>div>label>div:first-child>div {
            background-color: #e100ff !important;
            box-shadow: 0 0 5px rgba(225, 0, 255, 0.5);
        }
        
        /* Additional neon purple accents */
        .stSelectbox>div>div>div>div {
            color: #e100ff !important;
            text-shadow: 0 0 5px rgba(225, 0, 255, 0.3);
        }
        
        .stNumberInput>div>div>input {
            background-color: #1e0a3a !important;
            color: #ffffff !important;
            border: 1px solid #9c27b0 !important;
            box-shadow: 0 0 10px rgba(156, 39, 176, 0.3);
        }
        
        /* Footer styling */
        .footer {
            color: #e100ff;
            text-align: center;
            padding: 10px;
            margin-top: 20px;
            border-top: 1px solid rgba(156, 39, 176, 0.3);
            text-shadow: 0 0 5px rgba(225, 0, 255, 0.3);
        }
        
        /* Success messages with purple accent */
        .stAlert .st-at {
            background-color: rgba(30, 10, 50, 0.7) !important;
            border: 1px solid #e100ff !important;
            color: #f0d0ff !important;
        }
        
        /* Error messages with purple accent */
        .stAlert .st-av {
            background-color: rgba(50, 10, 30, 0.7) !important;
            border: 1px solid #ff0066 !important;
            color: #ffd0e0 !important;
        }
        
        /* Info messages with purple accent */
        .stAlert .st-aw {
            background-color: rgba(20, 10, 50, 0.7) !important;
            border: 1px solid #9c27b0 !important;
            color: #f0d0ff !important;
        }

        .download-button {
            color: #ffffff !important;
            background-color: #9c27b0;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            border: none;
            box-shadow: 0 0 10px rgba(156, 39, 176, 0.5);
            transition: all 0.3s;
            display: inline-block;
            margin: 0.5rem 0;
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
            cursor: pointer;
        }
        
        .download-button:hover {
            background-color: #e100ff !important;
            box-shadow: 0 0 15px rgba(225, 0, 255, 0.8) !important;
            transform: translateY(-1px);
        }
        
        .download-button:active {
            transform: translateY(0);
        }

        /* Make the Streamlit download button match our custom style */
        .stDownloadButton>button {
            color: #ffffff !important;
            background-color: #9c27b0 !important;
            padding: 0.5rem 1rem !important;
            border-radius: 6px !important;
            font-weight: bold !important;
            border: none !important;
            box-shadow: 0 0 10px rgba(156, 39, 176, 0.5) !important;
            transition: all 0.3s !important;
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.3) !important;
            width: auto !important;
        }
        
        .stDownloadButton>button:hover {
            background-color: #e100ff !important;
            box-shadow: 0 0 15px rgba(225, 0, 255, 0.8) !important;
            transform: translateY(-1px) !important;
        }
        
        .stDownloadButton>button:active {
            transform: translateY(0) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
   
    st.title("📊 Report Card Generator")
    st.markdown(
        "<style>div[data-testid='stMarkdownContainer'] > p {color: #ffffff;}</style>", 
        unsafe_allow_html=True
    )
    st.write(
        "Generate comprehensive report cards with a modern neon interface."
    )

    # Initialize session state
    if "reports" not in st.session_state:
        st.session_state.reports = load_previous_reports()
    if "current_report" not in st.session_state:
        st.session_state.current_report = None

    # Check if we're editing a report
    if "editing_report" in st.session_state:
        edit_report_form(st.session_state.editing_report)
        return

    # Main form for new reports
    with st.expander("➕ Add New Report", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input(
                "Student Name",
                placeholder="Enter student's full name",
                key="student_name_input",
            )
        with col2:
            class_section = st.text_input(
                "Class/Section",
                placeholder="e.g., Grade 10 - A",
                value="",
                key="class_section_input",
            )

        input_method = st.radio(
            "Input Method", ("Manual Entry", "Bulk Upload"), key="input_method_radio"
        )

        if input_method == "Manual Entry":
            st.write("Enter subjects and marks (e.g., Math: 85, English: 90):")
            input_data = st.text_area(
                "Subject-Score Pairs", 
                height=100, 
                key="manual_input_area",
                placeholder="Math: 85\nScience: 92\nEnglish: 88"
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload CSV file", type=["csv"], key="csv_uploader"
            )
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    if "Subject" in df.columns and "Score" in df.columns:
                        input_data = "\n".join(
                            [
                                f"{row['Subject']}: {row['Score']}"
                                for _, row in df.iterrows()
                            ]
                        )
                        st.success("File uploaded successfully!")
                    else:
                        st.error("CSV must contain 'Subject' and 'Score' columns.")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

        if st.button(
            "📊 Generate Report Card",
            use_container_width=True,
            key="generate_report_button",
        ):
            if not student_name:
                st.error("Please enter student name")
                return

            subject_scores = {}
            try:
                for entry in input_data.split("\n"):
                    if ":" in entry:
                        subject, score = entry.split(":")
                        subject = subject.strip()
                        score = score.strip()
                        if score.isdigit():
                            score = int(score)
                            if 0 <= score <= 100:
                                subject_scores[subject] = score
                            else:
                                st.error(
                                    f"Marks for {subject} must be between 0 and 100."
                                )
                                return
                        else:
                            st.error(
                                f"Invalid score for {subject}. Please enter a number."
                            )
                            return
            except Exception as e:
                st.error(f"Error processing input: {str(e)}")
                return

            if subject_scores:
                total_marks = sum(subject_scores.values())
                average = calculate_average(list(subject_scores.values()))
                grade, remarks, grade_color = assign_grade(average)

                # Create new report with unique ID
                report = {
                    "id": str(uuid.uuid4()),
                    "student_name": student_name,
                    "class_section": class_section,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "subjects": subject_scores,
                    "total_marks": total_marks,
                    "average": average,
                    "grade": grade,
                    "remarks": remarks,
                    "grade_color": grade_color,
                }

                st.session_state.current_report = report
                st.session_state.reports.insert(0, report)
                save_report(report)
                st.rerun()
            else:
                st.error(
                    "No valid subject-score pairs found. Please enter data correctly."
                )

    # Display current report if exists
    if st.session_state.current_report:
        display_report_card(st.session_state.current_report)

    # Previous reports section
    if st.session_state.reports:
        st.sidebar.title("📂 Previous Reports")
        search_term = st.sidebar.text_input("🔍 Search Reports", "")
        
        filtered_reports = [
            report for report in st.session_state.reports 
            if search_term.lower() in report["student_name"].lower() or 
               search_term.lower() in report.get("class_section", "").lower()
        ]
        
        for i, report in enumerate(filtered_reports[:10]):
            with st.sidebar.expander(f"{report['student_name']} - {report['date']}"):
                st.write(f"**Class:** {report.get('class_section', 'N/A')}")
                st.write(f"**Average:** {report['average']:.2f}%")
                st.write(f"**Grade:** {report['grade']}")
                st.write(f"**Remarks:** {report['remarks']}")
                st.write(f"**ID:** {report['id'][:8]}")  # Show shortened ID

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"View #{i+1}", key=f"view_{report['id']}"):
                        st.session_state.current_report = report
                        st.rerun()
                with col2:
                    if st.button(f"Edit #{i+1}", key=f"edit_{report['id']}"):
                        st.session_state.editing_report = report
                        st.rerun()

        if len(filtered_reports) > 10:
            st.sidebar.info(f"Showing 10 of {len(filtered_reports)} reports. Use search to find specific reports.")

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<p style='color:#00FF41'>Developed with ❤️ using Streamlit</p>", 
        unsafe_allow_html=True
    )
    st.sidebar.markdown(
        "<p style='color:#00FF41'>v2.1 | Report Card Generator</p>", 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()