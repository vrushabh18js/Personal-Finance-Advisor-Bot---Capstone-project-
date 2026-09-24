import os
import json
from datetime import datetime, date
from collections import defaultdict
from models import db, User, Income, Expense, BudgetPlan, SavingGoal, SystemSetting, ChatMessage

# Try importing google.genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False


def get_api_key():
    """Retrieve Gemini API key from environment variable or DB settings."""
    env_key = os.environ.get('GEMINI_API_KEY')
    if env_key and env_key.strip():
        return env_key.strip()
    
    try:
        setting = SystemSetting.query.filter_by(key='gemini_api_key').first()
        if setting and setting.value and setting.value.strip():
            return setting.value.strip()
    except Exception:
        pass
    return None


def get_gemini_client():
    """Returns a configured Gemini Client if API key exists."""
    if not GENAI_AVAILABLE:
        return None
    api_key = get_api_key()
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return None


def get_user_financial_context(user_id, month=None, year=None):
    """Gathers all financial data for a user to provide context for AI and analytics."""
    user = db.session.get(User, user_id)
    if not user:
        return None

    today = date.today()
    target_month = month if month else today.month
    target_year = year if year else today.year

    # Incomes
    incomes = Income.query.filter_by(user_id=user_id).all()
    # Filter for target month or periodic
    month_incomes = [inc for inc in incomes if inc.date.month == target_month and inc.date.year == target_year]
    total_income = sum(inc.amount for inc in month_incomes) if month_incomes else sum(inc.amount for inc in incomes)

    # Expenses
    expenses = Expense.query.filter_by(user_id=user_id).all()
    month_expenses = [exp for exp in expenses if exp.date.month == target_month and exp.date.year == target_year]
    if not month_expenses and expenses:
        # Fallback to all expenses if target month empty
        month_expenses = expenses

    total_expense = sum(exp.amount for exp in month_expenses)
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

    # Categorized expenses
    category_expenses = defaultdict(float)
    essential_expenses = 0.0
    discretionary_expenses = 0.0

    for exp in month_expenses:
        category_expenses[exp.category] += exp.amount
        if exp.is_essential:
            essential_expenses += exp.amount
        else:
            discretionary_expenses += exp.amount

    # Budgets
    budgets = BudgetPlan.query.filter_by(user_id=user_id, month=target_month, year=target_year).all()
    if not budgets:
        # Check any budgets for user
        budgets = BudgetPlan.query.filter_by(user_id=user_id).all()

    budget_status = []
    total_budgeted = 0.0
    for b in budgets:
        spent = category_expenses.get(b.category, 0.0)
        rem = b.allocated_amount - spent
        pct = (spent / b.allocated_amount * 100) if b.allocated_amount > 0 else 0
        total_budgeted += b.allocated_amount
        budget_status.append({
            'id': b.id,
            'category': b.category,
            'allocated': b.allocated_amount,
            'spent': round(spent, 2),
            'remaining': round(rem, 2),
            'percentage_spent': round(pct, 1),
            'is_overbudget': spent > b.allocated_amount
        })

    # Goals
    goals = SavingGoal.query.filter_by(user_id=user_id).all()
    goals_data = [g.to_dict() for g in goals]
    total_goal_target = sum(g.target_amount for g in goals)
    total_goal_current = sum(g.current_amount for g in goals)

    # Emergency fund calculation
    emergency_goals = [g for g in goals if 'emergency' in g.name.lower() or g.category == 'Emergency']
    emergency_saved = sum(g.current_amount for g in emergency_goals)
    monthly_burn = total_expense if total_expense > 0 else 1.0
    emergency_runway_months = round(emergency_saved / monthly_burn, 1)

    return {
        'user': user.to_dict(),
        'target_month': target_month,
        'target_year': target_year,
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'net_savings': round(net_savings, 2),
        'savings_rate': round(savings_rate, 1),
        'essential_expenses': round(essential_expenses, 2),
        'discretionary_expenses': round(discretionary_expenses, 2),
        'needs_ratio': round((essential_expenses / total_income * 100) if total_income > 0 else 0, 1),
        'wants_ratio': round((discretionary_expenses / total_income * 100) if total_income > 0 else 0, 1),
        'category_expenses': {k: round(v, 2) for k, v in category_expenses.items()},
        'budget_status': budget_status,
        'total_budgeted': round(total_budgeted, 2),
        'goals': goals_data,
        'emergency_saved': round(emergency_saved, 2),
        'emergency_runway_months': emergency_runway_months
    }


def calculate_financial_health_score(user_id):
    """
    Computes a comprehensive 0-100 Financial Health Score based on:
    1. Savings Rate (up to 30 pts)
    2. Budget Adherence (up to 30 pts)
    3. Emergency Cushion (up to 25 pts)
    4. Discretionary Spending Discipline (up to 15 pts)
    """
    ctx = get_user_financial_context(user_id)
    if not ctx:
        return {'score': 50, 'rating': 'Neutral', 'breakdown': {}, 'insights': []}

    savings_rate = ctx['savings_rate']
    budget_status = ctx['budget_status']
    emergency_runway = ctx['emergency_runway_months']
    wants_ratio = ctx['wants_ratio']

    # 1. Savings Rate Score (0 - 30)
    # 20%+ savings is optimal (30 pts), 0% is 5 pts, negative is 0 pts
    if savings_rate >= 20:
        savings_score = 30
    elif savings_rate > 0:
        savings_score = round(5 + (savings_rate / 20) * 25)
    else:
        savings_score = 0

    # 2. Budget Adherence Score (0 - 30)
    if budget_status:
        over_count = sum(1 for b in budget_status if b['is_overbudget'])
        budget_ratio = (len(budget_status) - over_count) / len(budget_status)
        budget_score = round(budget_ratio * 30)
    else:
        budget_score = 20  # Neutral if no budget set yet

    # 3. Emergency Cushion Score (0 - 25)
    # 3 to 6 months of expenses is benchmark
    if emergency_runway >= 6:
        emergency_score = 25
    elif emergency_runway >= 3:
        emergency_score = 20
    elif emergency_runway >= 1:
        emergency_score = 12
    elif emergency_runway > 0:
        emergency_score = 5
    else:
        emergency_score = 2

    # 4. Discretionary Discipline Score (0 - 15)
    # Wants ratio <= 30% gets full points (50/30/20 guideline)
    if wants_ratio <= 30:
        discipline_score = 15
    elif wants_ratio <= 45:
        discipline_score = 10
    elif wants_ratio <= 60:
        discipline_score = 5
    else:
        discipline_score = 0

    total_score = min(100, max(0, savings_score + budget_score + emergency_score + discipline_score))

    if total_score >= 85:
        rating = "Exceptional"
        badge_color = "emerald"
    elif total_score >= 70:
        rating = "Strong"
        badge_color = "teal"
    elif total_score >= 50:
        rating = "Moderate"
        badge_color = "amber"
    else:
        rating = "Needs Attention"
        badge_color = "rose"

    insights = []
    if savings_rate < 15:
        insights.append(f"Savings rate is {savings_rate}%. Target at least 20% to build wealth and stability.")
    else:
        insights.append(f"Great savings discipline! You are saving {savings_rate}% of your income.")

    overspent = [b['category'] for b in budget_status if b['is_overbudget']]
    if overspent:
        insights.append(f"Overbudget alert in: {', '.join(overspent)}. Consider reviewing non-essential spending here.")

    if emergency_runway < 3:
        insights.append(f"Emergency runway is currently {emergency_runway} months. Recommended safety cushion is 3-6 months.")
    else:
        insights.append(f"Solid emergency reserve! Your liquid cushion covers {emergency_runway} months of living expenses.")

    return {
        'score': total_score,
        'rating': rating,
        'badge_color': badge_color,
        'breakdown': {
            'savings_score': {'value': savings_score, 'max': 30, 'label': 'Savings Rate'},
            'budget_score': {'value': budget_score, 'max': 30, 'label': 'Budget Adherence'},
            'emergency_score': {'value': emergency_score, 'max': 25, 'label': 'Emergency Runway'},
            'discipline_score': {'value': discipline_score, 'max': 15, 'label': 'Spending Discipline'}
        },
        'insights': insights
    }


def generate_automated_budget(user_id, rule_type="50/30/20"):
    """
    Intelligently generates category budgets based on user profile and selected financial methodology:
    - 50/30/20: 50% Needs, 30% Wants, 20% Savings
    - Student Lean: 65% Essentials, 15% Wants, 20% Future Fund
    - Freelancer Buffer: 45% Essentials, 20% Lifestyle, 20% Tax/Runway, 15% Savings
    - Household Plan: 55% Household Needs, 25% Wants, 20% Long-term family goals
    """
    user = db.session.get(User, user_id)
    if not user:
        return []

    ctx = get_user_financial_context(user_id)
    income = ctx['total_income'] if ctx and ctx['total_income'] > 0 else (user.monthly_income_target or 3000.0)
    profile = user.profile_type or 'Salaried'

    allocations = {}
    today = date.today()

    if profile == 'Student' or rule_type == 'Lean Student':
        rule_name = 'Lean Student'
        # Total: Needs 65%, Wants 15%, Savings 20%
        allocations = {
            'Housing & Rent': income * 0.35,
            'Groceries': income * 0.18,
            'Transportation': income * 0.08,
            'Utilities': income * 0.04,
            'Education': income * 0.10,
            'Food & Dining': income * 0.10,
            'Entertainment': income * 0.05,
            'Miscellaneous': income * 0.05,
            'Emergency / Savings': income * 0.05
        }
    elif profile == 'Freelancer' or rule_type == 'Irregular Income Buffer':
        rule_name = 'Irregular Income Buffer'
        # 45% Needs, 20% Lifestyle, 20% Tax Reserve, 15% Savings
        allocations = {
            'Housing & Rent': income * 0.28,
            'Groceries': income * 0.12,
            'Utilities': income * 0.05,
            'Healthcare': income * 0.08,
            'Business & Subscriptions': income * 0.10,
            'Food & Dining': income * 0.10,
            'Entertainment': income * 0.07,
            'Tax & Emergency Buffer': income * 0.15,
            'Miscellaneous': income * 0.05
        }
    elif profile == 'Household' or rule_type == 'Household Plan':
        rule_name = 'Household Family Plan'
        # 55% Family Needs, 25% Lifestyle, 20% Goals
        allocations = {
            'Housing & Rent': income * 0.30,
            'Groceries': income * 0.16,
            'Utilities': income * 0.07,
            'Healthcare': income * 0.07,
            'Education': income * 0.10,
            'Transportation': income * 0.08,
            'Food & Dining': income * 0.08,
            'Entertainment': income * 0.06,
            'Miscellaneous': income * 0.08
        }
    else:
        # Standard 50/30/20 for Salaried Professional
        rule_name = '50/30/20 Standard'
        allocations = {
            'Housing & Rent': income * 0.28,
            'Groceries': income * 0.12,
            'Transportation': income * 0.06,
            'Utilities': income * 0.04,
            'Food & Dining': income * 0.12,
            'Entertainment': income * 0.08,
            'Shopping': income * 0.06,
            'Healthcare': income * 0.04,
            'Emergency / Savings Fund': income * 0.15,
            'Miscellaneous': income * 0.05
        }

    # Remove existing budget plans for this month and save new ones
    BudgetPlan.query.filter_by(user_id=user_id, month=today.month, year=today.year).delete()

    created_budgets = []
    for cat, amt in allocations.items():
        bp = BudgetPlan(
            user_id=user_id,
            month=today.month,
            year=today.year,
            category=cat,
            allocated_amount=round(amt, 2),
            rule_type=rule_name
        )
        db.session.add(bp)
        created_budgets.append(bp)

    db.session.commit()
    return [b.to_dict() for b in created_budgets]


def chat_with_advisor(user_id, message_text):
    """
    AI Conversational Financial Advisor:
    - Uses Gemini 2.5 Flash if API key is provided
    - Otherwise uses smart deterministic financial consultant logic tailored to the user's scenario
    """
    user = db.session.get(User, user_id)
    if not user:
        return "User not found."

    ctx = get_user_financial_context(user_id)
    health = calculate_financial_health_score(user_id)
    client = get_gemini_client()

    overbudget_items = [b for b in ctx.get('budget_status', []) if b.get('is_overbudget')]
    sym = user.currency_symbol or '₹'
    overbudget_str = ", ".join([f"{b['category']} (spent {sym}{b['spent']} of {sym}{b['allocated']})" for b in overbudget_items]) or "None"

    goals_str = ", ".join([f"{g['name']} ({sym}{g['current_amount']}/{sym}{g['target_amount']} - {g['progress_percentage']}%)" for g in ctx.get('goals', [])]) or "None defined yet"


    system_prompt = f"""You are 'Beacon', an elite Certified Financial Planner (CFP) and empathetic AI Personal Finance Advisor specialized in Indian and personal finance management.
You are counseling {user.name}, who is categorized under the '{user.profile_type}' profile.
User Context: {user.scenario_description}

Current Live Financial Snapshot:
- Monthly Income: {sym}{ctx['total_income']:,.2f}
- Monthly Expenses: {sym}{ctx['total_expense']:,.2f} (Essential: {sym}{ctx['essential_expenses']:,.2f}, Discretionary: {sym}{ctx['discretionary_expenses']:,.2f})
- Net Monthly Savings: {sym}{ctx['net_savings']:,.2f} (Savings Rate: {ctx['savings_rate']}%)
- Needs Ratio: {ctx['needs_ratio']}%, Wants Ratio: {ctx['wants_ratio']}%
- Financial Health Score: {health['score']}/100 ({health['rating']})
- Overbudget Categories: {overbudget_str}
- Active Goals: {goals_str}
- Emergency Fund Runway: {ctx['emergency_runway_months']} months of living expenses

Guidelines for responses:
1. Provide actionable, realistic, mathematically sound financial guidance using {sym} currency.
2. Tone: Professional, empowering, encouraging, and direct.
3. Reference their exact numbers and categories to show true personalization.
4. If advising on investments or savings, reference Indian options like Liquid Funds, High-Yield FDs, Nifty Index SIPs, RD, or Sukanya Samriddhi where relevant.
5. If the user is a college student managing pocket money ({sym}6,000), provide realistic college-level cost-cutting (canteen, notes, sharing).
"""

    # If Gemini client is active, call API
    if client:
        try:
            # Build conversation history
            past_messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp.desc()).limit(6).all()
            past_messages.reverse()

            chat_contents = [system_prompt]
            for m in past_messages:
                chat_contents.append(f"{'User' if m.role == 'user' else 'Beacon Advisor'}: {m.content}")
            chat_contents.append(f"User: {message_text}\nBeacon Advisor:")

            prompt_content = "\n\n".join(chat_contents)
            models_to_try = ['gemini-3.5-flash-lite', 'gemini-3.6-flash', 'gemini-3.7-flash']
            for mod in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=mod,
                        contents=prompt_content
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as mod_err:
                    print(f"Model {mod} error: {mod_err}")
                    continue
        except Exception as e:
            print(f"Gemini API error, falling back to heuristic engine: {e}")

    # Fallback Smart Deterministic Advisor Engine
    lower_msg = message_text.lower()
    resp_lines = []

    if any(k in lower_msg for k in ['overspend', 'budget', 'exceed', 'burn', 'limit']):
        if overbudget_items:
            resp_lines.append(f"### ⚠️ Budget Overrun Analysis for {user.name}")
            resp_lines.append(f"You have currently exceeded your budget limits in **{len(overbudget_items)} categories**:")
            for b in overbudget_items:
                diff = round(b['spent'] - b['allocated'], 2)
                resp_lines.append(f"- **{b['category']}**: Allocated {sym}{b['allocated']:,.2f}, but spent **{sym}{b['spent']:,.2f}** (+{sym}{diff:,.2f} overrun).")
            resp_lines.append("\n**Immediate Action Plan:**")
            resp_lines.append("1. **Pause non-essential spending** in high-burn areas via UPI or cards for the remainder of this month.")
            resp_lines.append(f"2. Rebalance {sym}{sum(b['spent'] - b['allocated'] for b in overbudget_items):,.2f} from surplus categories or discretionary buffer.")
            resp_lines.append("3. Click **'Auto-Generate with AI'** in your Budget tab to re-calibrate allocations.")
        else:
            resp_lines.append("### ✅ Excellent Budget Discipline!")
            resp_lines.append(f"All your tracked spending is currently within allocated limits! Your overall savings rate is **{ctx['savings_rate']}%**.")
            resp_lines.append("To optimize further, consider funneling any month-end surplus into an Emergency Liquid Fund or SIP.")

    elif any(k in lower_msg for k in ['save', 'saving', 'goal', 'emergency', 'invest', 'future', 'sip', 'fd']):
        resp_lines.append(f"### 📈 Savings & Wealth Building Strategy")
        resp_lines.append(f"Your current monthly savings capacity is **{sym}{ctx['net_savings']:,.2f}** ({ctx['savings_rate']}% savings rate).")
        resp_lines.append(f"- **Emergency Fund Runway**: You have **{ctx['emergency_runway_months']} months** of liquid expenses covered ({sym}{ctx['emergency_saved']:,.2f}).")
        
        if ctx['emergency_runway_months'] < 3:
            resp_lines.append(f"- ⚠️ **Top Priority**: Build this reserve to at least 3 full months ({sym}{ctx['total_expense'] * 3:,.2f}) in a high-yield savings account or auto-sweep FD before aggressive equity investing.")
        else:
            resp_lines.append(f"- 🛡️ **Milestone Met**: Your emergency cushion is solid. You can now allocate excess monthly cashflow toward Nifty 50 Index SIPs or target goals.")

        if ctx['goals']:
            resp_lines.append("\n**Goal Progress Summary:**")
            for g in ctx['goals']:
                resp_lines.append(f"- **{g['name']}**: {sym}{g['current_amount']:,.2f} / {sym}{g['target_amount']:,.2f} ({g['progress_percentage']}%)")

    elif any(k in lower_msg for k in ['freelance', 'client', 'variable', 'irregular', 'tax', 'advance tax']):
        resp_lines.append("### 💼 Freelancer Cashflow & Tax Management")
        resp_lines.append(f"With variable income (currently **{sym}{ctx['total_income']:,.2f}**), financial stability relies on the **Buffer System**:")
        resp_lines.append("1. **Advance Tax Reserve**: Transfer 20-25% of every incoming client invoice immediately into a dedicated separate tax account.")
        resp_lines.append(f"2. Maintain a **6-month emergency runway** (target: {sym}{ctx['total_expense'] * 6:,.2f}) to smooth out lean client billing cycles.")
        resp_lines.append("3. Pay yourself a **consistent baseline salary** from your business account rather than spending windfall project checks all at once.")

    elif any(k in lower_msg for k in ['student', 'allowance', 'pocket money', 'college', 'pocket', 'canteen']):
        resp_lines.append("### 🎓 Student Lean Budget Playbook")
        resp_lines.append(f"Managing your **{sym}{ctx['total_income']:,.2f} monthly pocket money** requires disciplined allocation:")
        resp_lines.append("1. **Hostel & Mess First**: Ensure room rent/mess charges (₹2,400) and study materials are locked in at the beginning of the month.")
        resp_lines.append("2. **Canteen & Tea Breaks**: Daily Chai, Maggi, and snack breaks add up quickly. Cap daily discretionary spends to ₹20-25.")
        resp_lines.append(f"3. **Micro-Savings**: Consistently saving ₹600-₹900/month from your ₹6,000 pocket money builds a ₹10,000+ safety cushion by academic year-end.")

    elif any(k in lower_msg for k in ['household', 'family', 'grocery', 'child', 'emi', 'home loan', 'school']):
        resp_lines.append("### 🏡 Household & Family Financial Coordination")
        resp_lines.append(f"Managing combined household cashflow of **{sym}{ctx['total_income']:,.2f}/mo** with **{sym}{ctx['total_expense']:,.2f}** in commitments:")
        resp_lines.append(f"- **Essential Needs & EMI Ratio**: {ctx['needs_ratio']}% of total income (keep total EMIs <= 40%).")
        resp_lines.append("- **Bulk Grocery Savings**: Monthly D-Mart or wholesale mandi shopping reduces FMCG costs by 12-18%.")
        resp_lines.append("- **Family Goals**: Automate monthly transfers to children's education funds and annual vacation sinking funds right after salary credit.")

    else:
        resp_lines.append(f"### 💡 Comprehensive Financial Health Review for {user.name}")
        resp_lines.append(f"Here is your real-time financial assessment as a **{user.profile_type}**:")
        resp_lines.append(f"- **Financial Health Score**: **{health['score']}/100** ({health['rating']})")
        resp_lines.append(f"- **Monthly Net Flow**: +{sym}{ctx['net_savings']:,.2f} (Income: {sym}{ctx['total_income']:,.2f} | Outflow: {sym}{ctx['total_expense']:,.2f})")
        resp_lines.append(f"- **50/30/20 Distribution**: Needs: **{ctx['needs_ratio']}%** | Wants: **{ctx['wants_ratio']}%** | Savings: **{ctx['savings_rate']}%**")
        
        if overbudget_items:
            resp_lines.append(f"- ⚠️ **Watch Out**: Overspending detected in {overbudget_str}.")
        else:
            resp_lines.append("- ✨ **Status**: All expense categories are currently within healthy limits.")
            
        resp_lines.append("\n**How can I assist you further today?** You can ask me:")
        resp_lines.append("- *'How do I cut down my food & dining expenses?'*")
        resp_lines.append("- *'Generate a personalized budget plan for my income'*")
        resp_lines.append("- *'How much should I keep in my emergency fund?'*")

    return "\n".join(resp_lines)


def generate_monthly_report_data(user_id, month=None, year=None):
    """Generates an executive monthly financial report with AI summary and breakdown."""
    user = db.session.get(User, user_id)
    if not user:
        return None

    ctx = get_user_financial_context(user_id, month=month, year=year)
    health = calculate_financial_health_score(user_id)

    # Top spending categories
    sorted_cats = sorted(ctx['category_expenses'].items(), key=lambda x: x[1], reverse=True)
    top_3_categories = sorted_cats[:3]

    sym = user.currency_symbol or '₹'
    verdict_summary = f"{user.name} achieved a {ctx['savings_rate']}% savings rate this month, saving {sym}{ctx['net_savings']:,.2f} on a total income of {sym}{ctx['total_income']:,.2f}."
    
    action_items = []
    if ctx['savings_rate'] < 20:
        action_items.append("Trim discretionary expenses (dining out, entertainment) by 10% to push your savings rate towards 20%.")
    else:
        action_items.append("Maintain your strong savings momentum by routing half of this month's surplus directly to your emergency fund.")

    overspent = [b for b in ctx['budget_status'] if b['is_overbudget']]
    if overspent:
        action_items.append(f"Audit your spend in {', '.join([b['category'] for b in overspent])} to bring it back under your monthly allocation.")
    else:
        action_items.append("All category budgets remained within bounds. Great discipline across all spending categories.")

    if ctx['emergency_runway_months'] < 3:
        action_items.append(f"Your current safety cushion covers {ctx['emergency_runway_months']} months. Prioritize reaching the 3-month mark ({sym}{ctx['total_expense'] * 3:,.2f}).")
    else:
        action_items.append(f"Emergency runway is well-padded at {ctx['emergency_runway_months']} months. Consider exploring low-cost diversified index funds or liquid funds.")

    return {
        'report_title': f"Monthly Financial Review - {date(ctx['target_year'], ctx['target_month'], 1).strftime('%B %Y')}",
        'user': user.to_dict(),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'metrics': {
            'total_income': ctx['total_income'],
            'total_expense': ctx['total_expense'],
            'net_savings': ctx['net_savings'],
            'savings_rate': ctx['savings_rate'],
            'needs_ratio': ctx['needs_ratio'],
            'wants_ratio': ctx['wants_ratio'],
            'health_score': health['score'],
            'health_rating': health['rating'],
            'emergency_runway_months': ctx['emergency_runway_months']
        },
        'top_spending_categories': [{'category': cat, 'amount': amt} for cat, amt in top_3_categories],
        'budget_variance': ctx['budget_status'],
        'goals_status': ctx['goals'],
        'ai_verdict': verdict_summary,
        'action_items': action_items
    }
