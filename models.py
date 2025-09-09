from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy extension.
# This object provides access to all SQLAlchemy functions and classes.
db = SQLAlchemy()

class Subject(db.Model):
    """
    Represents a top-level subject, typically corresponding to a single PDF document.
    """
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)

    # Subject-level overview and summary
    preface = db.Column(db.Text, nullable=True)
    overall_summary = db.Column(db.Text, nullable=True)

    # Establishes a one-to-many relationship with the Chapter model.
    # 'cascade' ensures that when a Subject is deleted, all its associated Chapters are also deleted.
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Subject {self.name}>'

class Chapter(db.Model):
    """
    Represents a single chapter within a Subject. Contains the AI-generated summary
    and links to related chart data.
    """
    __tablename__ = 'chapter'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

    # A short, introductory summary for the chapter.
    intro_summary = db.Column(db.Text, nullable=True)

    # A JSON list of content blocks (e.g., text, charts) that make up the chapter body.
    content_blocks = db.Column(db.Text, nullable=True)

    # Foreign key to link this chapter back to its parent Subject.
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    def __repr__(self):
        return f'<Chapter {self.title}>'