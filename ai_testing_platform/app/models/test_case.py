from .. import db  # Assuming db will be initialized in app/__init__.py

class TestCase(db.Model):
    __tablename__ = 'test_cases'

    id = db.Column(db.String, primary_key=True, unique=True, nullable=False) # Test Case ID from Excel
    description = db.Column(db.String, nullable=False)
    expected_outcome = db.Column(db.String, nullable=False)

    # Optional fields, to be populated later
    category = db.Column(db.String, nullable=True)
    priority = db.Column(db.String, nullable=True) # Could be db.Enum later
    tags = db.Column(db.JSON, nullable=True) # Stores a list of strings or key-value pairs

    def __repr__(self):
        return f"<TestCase {self.id}>"

    def to_dict(self):
        """Converts the TestCase object to a dictionary."""
        return {
            'Test Case ID': self.id, # Match Excel header for consistency in display
            'Description': self.description,
            'Expected Outcome': self.expected_outcome,
            'Category': self.category if self.category is not None else '', # Default to empty string if None
            'Priority': self.priority if self.priority is not None else '', # Default to empty string if None
            'Tags': self.tags if self.tags else [] # Ensure tags is a list, default to empty list
        }
