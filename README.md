<<<<<<< HEAD
# Cybersecurity Quiz Generator

This application generates interactive quizzes from PowerPoint (PPTX) and PDF files, specifically designed for cybersecurity students. It extracts content from the uploaded files and creates multiple-choice questions based on the material.

## Features

- Support for PPTX and PDF file uploads
- Generates 10-60 questions based on user preference
- Multiple-choice questions with immediate feedback
- Explanations for correct/incorrect answers
- Progress tracking and final score
- Interactive user interface

## Setup

1. Install Python 3.8 or higher
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Upload your PPTX or PDF file using the file uploader

4. Select the number of questions you want to generate (10-60)

5. Click "Generate Quiz" to start

6. Answer the questions and receive immediate feedback

7. View your final score at the end of the quiz

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt
- Internet connection (for the first run to download the question generation model)

## Note

The application uses a transformer model to generate questions, which may take a few moments to load on first run. The quality of generated questions depends on the clarity and structure of the input material. 
=======
# cyberQuiz
Quiz for Cyber Security Students
>>>>>>> 54b6ef8d1aa46d3564d41df356ff17d8c54b0368
