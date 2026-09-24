import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import db, User, Income, Expense, BudgetPlan, SavingGoal, ChatMessage, SystemSetting
import ai_engine
import seed_data

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'finance-bot-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///personal_finance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Helper to get current active user ID from session or query param
def get_current_user_id():
    uid = request.args.get('user_id', type=int)
    if uid:
        session['user_id'] = uid
        return uid
    if 'user_id' in session:
        return session['user_id']
    # Default to first user
    first_user = User.query.first()
    if first_user:
        session['user_id'] = first_user.id
        return first_user.id
    return 1


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


# ----------------------------------------------------
# USER & PROFILE API
# ----------------------------------------------------
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    current_id = get_current_user_id()
    return jsonify({
        'users': [u.to_dict() for u in users],
        'current_user_id': current_id
    })


@app.route('/api/users/current', methods=['GET'])
def get_current_user():
    uid = get_current_user_id()
    user = db.session.get(User, uid)
    if not user:
        user = User.query.first()
    return jsonify(user.to_dict() if user else {})


@app.route('/api/users/profile', methods=['POST', 'PUT'])
def update_profile():
    uid = get_current_user_id()
    user = db.session.get(User, uid)
    if not user:
        user = User.query.first()
    if not user:
        user = User(username='user', name='My Profile')
        db.session.add(user)
        db.session.flush()
        session['user_id'] = user.id

    data = request.get_json() or {}
    name = str(data.get('name', '')).strip()
    if name:
        user.name = name
    if 'profile_type' in data and data['profile_type']:
        user.profile_type = data['profile_type']
    if 'monthly_income_target' in data:
        try:
            user.monthly_income_target = float(data['monthly_income_target'])
        except (ValueError, TypeError):
            pass
    if 'currency_symbol' in data and data['currency_symbol']:
        user.currency_symbol = data['currency_symbol']
    if 'scenario_description' in data:
        user.scenario_description = data['scenario_description']

    if data.get('clear_data'):
        seed_data.clear_user_data(user.id)

    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})


@app.route('/api/data/reset', methods=['POST'])
def reset_data():
    uid = get_current_user_id()
    seed_data.clear_user_data(uid)
    return jsonify({'success': True, 'message': 'All financial records cleared successfully.'})


@app.route('/api/data/seed-mock', methods=['POST'])
def seed_mock():
    uid = get_current_user_id()
    seed_data.populate_user_mock_data(uid)
    return jsonify({'success': True, 'message': 'Mock sample data generated successfully.'})


@app.route('/api/users/switch', methods=['POST'])
def switch_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User profile not found'}), 404
    session['user_id'] = user.id
    return jsonify({'success': True, 'user': user.to_dict()})


# ----------------------------------------------------
# INCOMES API
# ----------------------------------------------------
@app.route('/api/incomes', methods=['GET'])
def get_incomes():
    uid = get_current_user_id()
    incomes = Income.query.filter_by(user_id=uid).order_by(Income.date.desc()).all()
    return jsonify([inc.to_dict() for inc in incomes])


@app.route('/api/incomes', methods=['POST'])
def add_income():
    uid = get_current_user_id()
    data = request.get_json() or {}
    try:
        amount = float(data.get('amount', 0))
        source = str(data.get('source', '')).strip()
        frequency = data.get('frequency', 'Monthly')
        notes = data.get('notes', '')
        date_str = data.get('date')
        income_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()

        if not source or amount <= 0:
            return jsonify({'error': 'Please provide a valid source name and positive amount.'}), 400

        inc = Income(
            user_id=uid,
            source=source,
            amount=amount,
            date=income_date,
            frequency=frequency,
            notes=notes
        )
        db.session.add(inc)
        db.session.commit()
        return jsonify({'success': True, 'income': inc.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/incomes/<int:income_id>', methods=['DELETE'])
def delete_income(income_id):
    uid = get_current_user_id()
    inc = Income.query.filter_by(id=income_id, user_id=uid).first()
    if not inc:
        return jsonify({'error': 'Income record not found'}), 404
    db.session.delete(inc)
    db.session.commit()
    return jsonify({'success': True})


# ----------------------------------------------------
# EXPENSES API
# ----------------------------------------------------
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    uid = get_current_user_id()
    category = request.args.get('category')
    query = Expense.query.filter_by(user_id=uid)
    if category and category.strip() and category != 'All':
        query = query.filter_by(category=category.strip())
    expenses = query.order_by(Expense.date.desc()).all()
    return jsonify([exp.to_dict() for exp in expenses])


@app.route('/api/expenses', methods=['POST'])
def add_expense():
    uid = get_current_user_id()
    data = request.get_json() or {}
    try:
        amount = float(data.get('amount', 0))
        category = str(data.get('category', 'Miscellaneous')).strip()
        description = str(data.get('description', '')).strip()
        is_essential = bool(data.get('is_essential', True))
        payment_method = data.get('payment_method', 'Debit Card')
        date_str = data.get('date')
        expense_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()

        if not description or amount <= 0:
            return jsonify({'error': 'Please provide a valid description and positive amount.'}), 400

        exp = Expense(
            user_id=uid,
            category=category,
            amount=amount,
            date=expense_date,
            description=description,
            is_essential=is_essential,
            payment_method=payment_method
        )
        db.session.add(exp)
        db.session.commit()
        return jsonify({'success': True, 'expense': exp.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    uid = get_current_user_id()
    exp = Expense.query.filter_by(id=expense_id, user_id=uid).first()
    if not exp:
        return jsonify({'error': 'Expense record not found'}), 404
    db.session.delete(exp)
    db.session.commit()
    return jsonify({'success': True})


# ----------------------------------------------------
# BUDGETS API
# ----------------------------------------------------
@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    uid = get_current_user_id()
    ctx = ai_engine.get_user_financial_context(uid)
    return jsonify({
        'budgets': ctx['budget_status'] if ctx else [],
        'total_budgeted': ctx['total_budgeted'] if ctx else 0,
        'total_expense': ctx['total_expense'] if ctx else 0
    })


@app.route('/api/budgets', methods=['POST'])
def add_or_update_budget():
    uid = get_current_user_id()
    data = request.get_json() or {}
    category = data.get('category')
    allocated = float(data.get('allocated_amount', 0))
    rule_type = data.get('rule_type', 'Custom')
    today = date.today()

    if not category or allocated < 0:
        return jsonify({'error': 'Invalid category or allocation amount.'}), 400

    bp = BudgetPlan.query.filter_by(user_id=uid, month=today.month, year=today.year, category=category).first()
    if bp:
        bp.allocated_amount = allocated
        bp.rule_type = rule_type
    else:
        bp = BudgetPlan(
            user_id=uid,
            month=today.month,
            year=today.year,
            category=category,
            allocated_amount=allocated,
            rule_type=rule_type
        )
        db.session.add(bp)

    db.session.commit()
    return jsonify({'success': True, 'budget': bp.to_dict()})


@app.route('/api/budgets/generate', methods=['POST'])
def generate_ai_budget():
    uid = get_current_user_id()
    data = request.get_json() or {}
    rule_type = data.get('rule_type', '50/30/20')
    new_budgets = ai_engine.generate_automated_budget(uid, rule_type=rule_type)
    return jsonify({'success': True, 'budgets': new_budgets})


@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    uid = get_current_user_id()
    bp = BudgetPlan.query.filter_by(id=budget_id, user_id=uid).first()
    if not bp:
        return jsonify({'error': 'Budget plan item not found'}), 404
    db.session.delete(bp)
    db.session.commit()
    return jsonify({'success': True})


# ----------------------------------------------------
# SAVING GOALS API
# ----------------------------------------------------
@app.route('/api/goals', methods=['GET'])
def get_goals():
    uid = get_current_user_id()
    goals = SavingGoal.query.filter_by(user_id=uid).all()
    return jsonify([g.to_dict() for g in goals])


@app.route('/api/goals', methods=['POST'])
def add_goal():
    uid = get_current_user_id()
    data = request.get_json() or {}
    try:
        name = str(data.get('name', '')).strip()
        target_amount = float(data.get('target_amount', 0))
        current_amount = float(data.get('current_amount', 0))
        category = data.get('category', 'Emergency')
        date_str = data.get('target_date')
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

        if not name or target_amount <= 0:
            return jsonify({'error': 'Please provide a valid goal name and target amount.'}), 400

        goal = SavingGoal(
            user_id=uid,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date,
            category=category,
            status='Completed' if current_amount >= target_amount else 'In Progress'
        )
        db.session.add(goal)
        db.session.commit()
        return jsonify({'success': True, 'goal': goal.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/goals/<int:goal_id>/contribute', methods=['POST'])
def contribute_goal(goal_id):
    uid = get_current_user_id()
    data = request.get_json() or {}
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'Contribution amount must be positive'}), 400

    goal = SavingGoal.query.filter_by(id=goal_id, user_id=uid).first()
    if not goal:
        return jsonify({'error': 'Saving goal not found'}), 404

    goal.current_amount += amount
    if goal.current_amount >= goal.target_amount:
        goal.status = 'Completed'

    db.session.commit()
    return jsonify({'success': True, 'goal': goal.to_dict()})


@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    uid = get_current_user_id()
    goal = SavingGoal.query.filter_by(id=goal_id, user_id=uid).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'success': True})


# ----------------------------------------------------
# ANALYTICS & REPORTS API
# ----------------------------------------------------
@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    uid = get_current_user_id()
    ctx = ai_engine.get_user_financial_context(uid)
    health = ai_engine.calculate_financial_health_score(uid)

    # Anomaly alerts
    alerts = []
    if ctx:
        if ctx['net_savings'] < 0:
            alerts.append({
                'type': 'danger',
                'title': 'Deficit Alert',
                'message': f"Monthly outflow (${ctx['total_expense']}) exceeds income (${ctx['total_income']}) by ${abs(ctx['net_savings'])}."
            })
        overspent = [b for b in ctx['budget_status'] if b['is_overbudget']]
        for o in overspent:
            alerts.append({
                'type': 'warning',
                'title': f"Budget Exceeded: {o['category']}",
                'message': f"Spent ${o['spent']} out of allocated ${o['allocated']} ({o['percentage_spent']}%)."
            })
        if ctx['emergency_runway_months'] < 1.0:
            alerts.append({
                'type': 'info',
                'title': 'Emergency Runway Low',
                'message': f"Liquid emergency reserve covers less than 1 month ({ctx['emergency_runway_months']} mo)."
            })

    return jsonify({
        'context': ctx,
        'health': health,
        'alerts': alerts
    })


@app.route('/api/analytics/monthly-report', methods=['GET'])
def get_monthly_report():
    uid = get_current_user_id()
    report = ai_engine.generate_monthly_report_data(uid)
    if not report:
        return jsonify({'error': 'Unable to generate monthly report'}), 400
    return jsonify(report)


# ----------------------------------------------------
# AI ADVISOR CHAT API
# ----------------------------------------------------
@app.route('/api/advisor/history', methods=['GET'])
def get_chat_history():
    uid = get_current_user_id()
    msgs = ChatMessage.query.filter_by(user_id=uid).order_by(ChatMessage.timestamp.asc()).all()
    return jsonify([m.to_dict() for m in msgs])


@app.route('/api/advisor/chat', methods=['POST'])
def send_chat_message():
    uid = get_current_user_id()
    data = request.get_json() or {}
    message_text = str(data.get('message', '')).strip()
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400

    # Save user message
    user_msg = ChatMessage(user_id=uid, role='user', content=message_text)
    db.session.add(user_msg)
    db.session.commit()

    # Generate response
    ai_response = ai_engine.chat_with_advisor(uid, message_text)

    # Save assistant response
    bot_msg = ChatMessage(user_id=uid, role='assistant', content=ai_response)
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({
        'user_message': user_msg.to_dict(),
        'bot_message': bot_msg.to_dict()
    })


@app.route('/api/advisor/clear', methods=['POST'])
def clear_chat():
    uid = get_current_user_id()
    ChatMessage.query.filter_by(user_id=uid).delete()
    db.session.commit()
    return jsonify({'success': True})


# ----------------------------------------------------
# SETTINGS & API KEY
# ----------------------------------------------------
@app.route('/api/settings', methods=['GET'])
def get_settings():
    api_key = ai_engine.get_api_key()
    has_key = bool(api_key and len(api_key) > 5)
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if has_key else ""
    return jsonify({
        'has_gemini_key': has_key,
        'masked_key': masked_key,
        'ai_mode': 'Google Gemini 3.6 Flash' if has_key else 'Autonomous Deterministic Financial Engine'
    })


@app.route('/api/settings/api-key', methods=['POST'])
def update_api_key():
    data = request.get_json() or {}
    key_val = str(data.get('api_key', '')).strip()
    
    setting = SystemSetting.query.filter_by(key='gemini_api_key').first()
    if not setting:
        setting = SystemSetting(key='gemini_api_key', value=key_val)
        db.session.add(setting)
    else:
        setting.value = key_val
    
    db.session.commit()
    return jsonify({'success': True, 'has_key': bool(key_val)})


# ----------------------------------------------------
# APP INITIALIZATION
# ----------------------------------------------------
with app.app_context():
    db.create_all()
    seed_data.seed_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
