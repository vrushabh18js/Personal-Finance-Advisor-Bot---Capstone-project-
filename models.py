from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=True)
    profile_type = db.Column(db.String(64), nullable=False, default='Salaried')  # 'Salaried', 'Student', 'Freelancer', 'Household'
    scenario_description = db.Column(db.Text, nullable=True)
    monthly_income_target = db.Column(db.Float, default=0.0)
    currency_symbol = db.Column(db.String(8), default='₹')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    incomes = db.relationship('Income', backref='user', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('BudgetPlan', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('SavingGoal', backref='user', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('ChatMessage', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'profile_type': self.profile_type,
            'scenario_description': self.scenario_description,
            'monthly_income_target': self.monthly_income_target,
            'currency_symbol': self.currency_symbol,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Income(db.Model):
    __tablename__ = 'incomes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    frequency = db.Column(db.String(32), default='Monthly')  # 'Monthly', 'Bi-weekly', 'Weekly', 'One-time', 'Client Project'
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source': self.source,
            'amount': self.amount,
            'date': self.date.isoformat() if self.date else None,
            'frequency': self.frequency,
            'notes': self.notes
        }


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(64), nullable=False)  # 'Housing & Rent', 'Food & Dining', 'Groceries', etc.
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(256), nullable=False)
    is_essential = db.Column(db.Boolean, default=True)  # True = Need, False = Want
    payment_method = db.Column(db.String(32), default='Debit Card')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'amount': self.amount,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'is_essential': self.is_essential,
            'payment_method': self.payment_method
        }


class BudgetPlan(db.Model):
    __tablename__ = 'budget_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    allocated_amount = db.Column(db.Float, nullable=False)
    rule_type = db.Column(db.String(32), default='50/30/20')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'month': self.month,
            'year': self.year,
            'category': self.category,
            'allocated_amount': self.allocated_amount,
            'rule_type': self.rule_type
        }


class SavingGoal(db.Model):
    __tablename__ = 'saving_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(64), default='Emergency')  # 'Emergency', 'Education', 'Technology', 'Family', 'Travel'
    status = db.Column(db.String(32), default='In Progress')

    def to_dict(self):
        pct = (self.current_amount / self.target_amount * 100) if self.target_amount > 0 else 0
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'category': self.category,
            'status': self.status,
            'progress_percentage': round(pct, 1),
            'remaining_amount': max(0.0, self.target_amount - self.current_amount)
        }


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(16), nullable=False)  # 'user', 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {'key': self.key, 'value': self.value}
