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
    summary = db.Column(db.Text, nullable=False, comment="Stores the 'preface' or high-level summary of the chapter.")
    facts = db.Column(db.Text, nullable=True, comment="Stores the detailed, bullet-pointed facts from the chapter, likely in Markdown format.")

    # Stores the relative path to a generated chart image (e.g., 'charts/some-uuid.png').
    chart_path = db.Column(db.String(200), nullable=True)

    # Foreign key to link this chapter back to its parent Subject.
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    # Establishes a one-to-many relationship with the ChartIdea model.
    chart_ideas = db.relationship('ChartIdea', backref='chapter', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Chapter {self.title}>'

class ChartIdea(db.Model):
    """
    Represents a single chart idea suggested by the AI for a specific chapter.
    This allows for on-demand chart generation.
    """
    __tablename__ = 'chart_idea'
    id = db.Column(db.Integer, primary_key=True)
    idea_text = db.Column(db.String(300), nullable=False, comment="The textual description of the chart idea.")

    # Foreign key to link this idea back to its parent Chapter.
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)

    # A flag to track whether a chart has been generated from this idea, to avoid re-generation.
    is_generated = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<ChartIdea {self.idea_text}>'
