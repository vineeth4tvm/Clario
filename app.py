import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from werkzeug.utils import secure_filename
from models import db, Subject, Chapter, ChartIdea
import ai_service
import r_service
from markdown_it import MarkdownIt

def create_app():
    """
    Factory function to create and configure the Flask application.
    This pattern is useful for testing and managing configurations.
    """
    app = Flask(__name__)

    # --- Configuration ---
    # Use a more secure, environment-based secret key in production
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-super-secret-key-that-should-be-changed')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'

    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # --- Database Initialization ---
    with app.app_context():
        # In a real-world application, use Flask-Migrate to handle schema changes.
        db.create_all()

    # =========================================================================
    # --- Main Routes ---
    # =========================================================================

    @app.route('/')
    def index():
        """Renders the home page, listing all subjects."""
        subjects = Subject.query.order_by(Subject.name).all()
        return render_template('index.html', subjects=subjects)

    @app.route('/subject/<int:subject_id>')
    def view_subject(subject_id):
        """Displays the chapters for a specific subject."""
        subject = db.get_or_404(Subject, subject_id)
        return render_template('subject.html', subject=subject)

    @app.route('/subject/<int:subject_id>/chapter/<int:chapter_id>')
    def view_chapter(subject_id, chapter_id):
        """Displays the main page for a chapter with all its features."""
        chapter = db.get_or_404(Chapter, chapter_id)

        # Verify chapter belongs to the subject
        if chapter.subject_id != subject_id:
            abort(404)

        # Clear Q&A when moving between chapters
        if session.get('qna_chapter_id') != chapter_id:
            session.pop('last_question', None)
            session.pop('last_answer', None)
        session['qna_chapter_id'] = chapter_id

        # Render Markdown for the 'facts' section
        md = MarkdownIt()
        # The AI is sometimes returning literal '\n' characters, so we replace them.
        facts_markdown = chapter.facts.replace('\\n', '\n') if chapter.facts else ""
        facts_html = md.render(facts_markdown) if facts_markdown else ""

        return render_template('chapter.html', subject_id=subject_id, chapter=chapter, facts_html=facts_html)

    # =========================================================================
    # --- Admin and Processing Routes ---
    # =========================================================================

    @app.route('/admin/upload', methods=['GET', 'POST'])
    def upload_pdf():
        """Handles the PDF upload form and processing workflow."""
        if request.method == 'POST':
            subject_name = request.form.get('subject_name')
            pdf_file = request.files.get('pdf_file')

            if not subject_name or not pdf_file or pdf_file.filename == '':
                flash('Missing subject name or file.', 'danger')
                return redirect(request.url)

            if pdf_file and pdf_file.filename.endswith('.pdf'):
                filename = secure_filename(pdf_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf_file.save(filepath)

                flash(f'File "{filename}" uploaded. Processing with Gemini... This may take a moment.', 'info')
                processed_data = ai_service.process_pdf_and_extract_chapters(filepath, subject_name)

                if 'error' in processed_data:
                    flash(f"AI processing failed: {processed_data['error']}", 'danger')
                    return redirect(request.url)

                try:
                    # Use a transaction to ensure all data is saved or none at all
                    with db.session.begin_nested():
                        new_subject = Subject(name=processed_data.get('subject_name', subject_name))
                        db.session.add(new_subject)

                        for ch_data in processed_data.get('chapters', []):
                            new_chapter = Chapter(
                                title=ch_data.get('title'),
                                summary=ch_data.get('preface'),  # 'summary' in db now stores the preface
                                facts=ch_data.get('facts'),      # New field for detailed facts
                                subject=new_subject
                            )
                            db.session.add(new_chapter)
                            # The new prompt doesn't generate chart ideas, so this loop is no longer needed.
                            # If chart ideas were to be re-introduced, the prompt and this section would need updating.
                    db.session.commit()
                    flash('Successfully processed PDF and created new subject!', 'success')
                    return redirect(url_for('view_subject', subject_id=new_subject.id))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Database error: Failed to save subject. Reason: {e}", 'danger')
        return render_template('admin_upload.html')

    @app.route('/generate-chart/<int:idea_id>', methods=['POST'])
    def generate_chart(idea_id):
        """Generates a chart from a ChartIdea via a POST request."""
        chart_idea = db.get_or_404(ChartIdea, idea_id)
        chapter = chart_idea.chapter

        r_script = ai_service.generate_r_script_for_chart(chart_idea.idea_text)
        if not r_script:
            flash("AI service failed to generate an R script.", 'danger')
            return redirect(url_for(
                'view_chapter',
                subject_id=chapter.subject_id,
                chapter_id=chapter.id
            ))

        chart_path = r_service.generate_chart_from_script(r_script)
        if not chart_path:
            flash("R service failed to execute the script and generate a chart.", 'danger')
        else:
            chapter.chart_path = chart_path
            chart_idea.is_generated = True
            db.session.commit()
            flash("Successfully generated and saved the chart!", 'success')

        return redirect(url_for(
            'view_chapter',
            subject_id=chapter.subject_id,
            chapter_id=chapter.id
        ))

    @app.route('/ask/<int:chapter_id>', methods=['POST'])
    def ask_question(chapter_id):
        """Handles the Q&A form submission."""
        chapter = db.get_or_404(Chapter, chapter_id)
        question = request.form.get('question')

        if not question:
            flash("Please enter a question.", 'warning')
        else:
            context = chapter.summary
            answer = ai_service.answer_question_from_context(question, context)
            session['last_question'] = question
            session['last_answer'] = answer
            session['qna_chapter_id'] = chapter_id

        return redirect(url_for(
            'view_chapter',
            subject_id=chapter.subject_id,
            chapter_id=chapter.id
        ))

    # =========================================================================
    # --- Quiz Routes ---
    # =========================================================================

    @app.route('/generate-quiz/<int:chapter_id>')
    def generate_quiz(chapter_id):
        """Generates a quiz from a chapter's summary and displays it."""
        chapter = db.get_or_404(Chapter, chapter_id)
        quiz_data = ai_service.generate_quiz_from_summary(chapter.summary)

        if not quiz_data or 'error' in quiz_data:
            flash(quiz_data.get('error', 'Could not generate quiz.'), 'danger')
            return redirect(url_for(
                'view_chapter',
                subject_id=chapter.subject_id,
                chapter_id=chapter.id
            ))

        return render_template('quiz.html', chapter=chapter, quiz_data=quiz_data)

    @app.route('/submit-quiz/<int:chapter_id>', methods=['POST'])
    def submit_quiz(chapter_id):
        """Grades the submitted quiz and shows the result."""
        chapter = db.get_or_404(Chapter, chapter_id)
        try:
            quiz_data_json = request.form.get('quiz_data')
            quiz_data = json.loads(quiz_data_json)
            questions = quiz_data.get('questions', [])

            score = 0
            total = len(questions)

            for i, question in enumerate(questions):
                user_answer = request.form.get(f'question_{i}')
                correct_answer = question.get('correct_answer_index')
                if user_answer is not None and int(user_answer) == correct_answer:
                    score += 1

            return render_template('result.html', chapter=chapter, score=score, total=total)
        except Exception as e:
            flash(f"An error occurred while grading the quiz: {e}", 'danger')
            return redirect(url_for(
                'view_chapter',
                subject_id=chapter.subject_id,
                chapter_id=chapter.id
            ))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
