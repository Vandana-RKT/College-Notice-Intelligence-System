# College Notice Intelligence System (CNIS)

An AI-powered web application that simplifies college notice management by extracting important information from PDF circulars and presenting it in an organized, student-friendly format.

## Overview

College students often miss important announcements, deadlines, eligibility criteria, and registration details because college notices are shared as lengthy PDF documents.

The **College Notice Intelligence System (CNIS)** solves this problem by using Artificial Intelligence to analyze uploaded college notices, extract relevant information, and display it through an easy-to-use dashboard.

The system supports both administrators and students.

## Features

### Admin Module
- Secure administrator login
- Upload college notices in PDF format
- Automatically extract text from PDF documents
- Analyze notices using Google Gemini AI
- Extract important dates, deadlines, eligibility, fees, and required documents
- Review and publish notices
- Manage uploaded notices through an admin dashboard

### Student Module
- Student login
- View published college notices
- Read AI-generated notice summaries
- View important dates and deadlines
- Check eligibility criteria and registration fees
- Access original PDF notices
- View notice information in an organized format

## Technologies Used

| Category | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | SQLite |
| AI Integration | Google Gemini API |
| PDF Processing | PyMuPDF |
| Authentication | Flask Sessions, Werkzeug |
| Environment Management | Python dotenv |

## System Architecture

1. **PDF Upload:** Admin uploads a college notice in PDF format.
2. **Text Extraction:** PyMuPDF extracts the text from the uploaded PDF.
3. **AI Analysis:** Google Gemini analyzes the extracted content.
4. **Information Extraction:** Important details such as deadlines, eligibility, fees, and required documents are identified.
5. **Database Storage:** Notice information is stored in SQLite.
6. **Notice Publishing:** Admin reviews and publishes the notice.
7. **Student Access:** Students can view published notices and their important details.

## Project Structure

```text
College-Notice-Intelligence-System/
│
├── app.py
├── config.py
├── database.py
├── requirements.txt
├── .gitignore
│
├── services/
│   ├── llm_service.py
│   └── pdf_extractor.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── admin_dashboard.html
│   ├── admin_notices.html
│   ├── upload.html
│   ├── student_dashboard.html
│   └── notice_details.html
│
└── uploads/
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Vandana-RKT/College-Notice-Intelligence-System.git
```

### 2. Navigate to the Project Folder

```bash
cd College-Notice-Intelligence-System
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**
```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root directory:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Replace `your_gemini_api_key` with your own API key.

**Important:** Never upload your `.env` file or expose your API key publicly.

### 7. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## Future Enhancements

- Automated deadline reminders
- Email and notification integration
- Advanced notice search and filtering
- Calendar integration for important dates
- Improved AI-based categorization
- Mobile-friendly interface

## Project Objective

The main objective of CNIS is to reduce the time students spend reading lengthy college circulars and make important academic information easier to access through AI-powered automation.

## Author

**Vandana R**

Computer Science and Engineering

GitHub: [Vandana-RKT](https://github.com/Vandana-RKT)

---

*College Notice Intelligence System – Making college announcements smarter and simpler.*
