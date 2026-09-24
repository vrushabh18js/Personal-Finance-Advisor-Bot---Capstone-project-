from datetime import date, timedelta
from models import db, User, Income, Expense, BudgetPlan, SavingGoal, ChatMessage

def clear_user_data(user_id):
    """Clears all financial records and messages for a specific user."""
    ChatMessage.query.filter_by(user_id=user_id).delete()
    SavingGoal.query.filter_by(user_id=user_id).delete()
    BudgetPlan.query.filter_by(user_id=user_id).delete()
    Expense.query.filter_by(user_id=user_id).delete()
    Income.query.filter_by(user_id=user_id).delete()
    db.session.commit()


def populate_user_mock_data(user_id):
    """Seeds realistic sample financial records tailored to the user profile."""
    user = db.session.get(User, user_id)
    if not user:
        return
    clear_user_data(user_id)
    today = date.today()
    sym = user.currency_symbol or '₹'

    # Tailored mock data based on profile type
    if user.profile_type == 'Student':
        income_amt = user.monthly_income_target if user.monthly_income_target > 0 else 6000.0
        db.session.add_all([
            Income(user_id=user.id, source="Monthly Allowance / Pocket Money", amount=income_amt * 0.75, date=today.replace(day=1), frequency="Monthly", notes="Family allowance for mess & study"),
            Income(user_id=user.id, source="Tutoring / Campus Project", amount=income_amt * 0.25, date=today.replace(day=15), frequency="Monthly", notes="Part-time gig")
        ])
        db.session.add_all([
            Expense(user_id=user.id, category="Housing & Rent", amount=income_amt * 0.40, date=today.replace(day=1), description="Hostel & Mess Charges", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Groceries", amount=income_amt * 0.14, date=today.replace(day=4), description="Hostel snacks, fruits & milk", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Education", amount=income_amt * 0.08, date=today.replace(day=6), description="College notes, photocopies & stationery", is_essential=True, payment_method="Cash"),
            Expense(user_id=user.id, category="Food & Dining", amount=income_amt * 0.10, date=today.replace(day=9), description="Canteen Chai, Maggi & snacks", is_essential=False, payment_method="UPI"),
            Expense(user_id=user.id, category="Transportation", amount=income_amt * 0.06, date=today.replace(day=11), description="Student bus pass & metro", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Entertainment", amount=income_amt * 0.07, date=today.replace(day=16), description="Mobile recharge & movie outing", is_essential=False, payment_method="UPI")
        ])
        db.session.add_all([
            SavingGoal(user_id=user.id, name="Laptop / Study Tech Upgrade", target_amount=income_amt * 8, current_amount=income_amt * 2, target_date=today + timedelta(days=180), category="Technology"),
            SavingGoal(user_id=user.id, name="Student Emergency Reserve", target_amount=income_amt * 1.5, current_amount=income_amt * 0.5, target_date=today + timedelta(days=60), category="Emergency")
        ])
    elif user.profile_type == 'Freelancer':
        income_amt = user.monthly_income_target if user.monthly_income_target > 0 else 110000.0
        db.session.add_all([
            Income(user_id=user.id, source="Primary Client Retainer", amount=income_amt * 0.65, date=today.replace(day=2), frequency="Client Project", notes="Monthly design retainer"),
            Income(user_id=user.id, source="Secondary Project Milestone", amount=income_amt * 0.35, date=today.replace(day=18), frequency="Client Project", notes="Completed deliverables")
        ])
        db.session.add_all([
            Expense(user_id=user.id, category="Housing & Rent", amount=income_amt * 0.28, date=today.replace(day=2), description="Studio Apartment & Co-working desk", is_essential=True, payment_method="Bank Transfer"),
            Expense(user_id=user.id, category="Business & Subscriptions", amount=income_amt * 0.08, date=today.replace(day=5), description="Figma, Adobe CC & Cloud Hosting", is_essential=True, payment_method="Credit Card"),
            Expense(user_id=user.id, category="Groceries", amount=income_amt * 0.10, date=today.replace(day=7), description="Fresh groceries & supermarket supplies", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Food & Dining", amount=income_amt * 0.08, date=today.replace(day=12), description="Cafes & client lunch meetings", is_essential=False, payment_method="Credit Card"),
            Expense(user_id=user.id, category="Transportation", amount=income_amt * 0.05, date=today.replace(day=15), description="Cabs & local travel", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Entertainment", amount=income_amt * 0.04, date=today.replace(day=20), description="Streaming services & weekend leisure", is_essential=False, payment_method="Credit Card")
        ])
        db.session.add_all([
            SavingGoal(user_id=user.id, name="6-Month Lean Runway Fund", target_amount=income_amt * 3, current_amount=income_amt * 1.5, target_date=today + timedelta(days=180), category="Emergency"),
            SavingGoal(user_id=user.id, name="Advance Tax Reserve", target_amount=income_amt * 1.2, current_amount=income_amt * 0.8, target_date=today + timedelta(days=90), category="Tax")
        ])
    else:  # Default / Salaried
        income_amt = user.monthly_income_target if user.monthly_income_target > 0 else 75000.0
        db.session.add_all([
            Income(user_id=user.id, source="Primary Take-Home Salary", amount=income_amt * 0.94, date=today.replace(day=1), frequency="Monthly", notes="Net monthly credit after deductions"),
            Income(user_id=user.id, source="Dividends & Interest", amount=income_amt * 0.06, date=today.replace(day=15), frequency="Quarterly", notes="Investments return")
        ])
        db.session.add_all([
            Expense(user_id=user.id, category="Housing & Rent", amount=income_amt * 0.32, date=today.replace(day=2), description="Apartment Rent & Maintenance", is_essential=True, payment_method="Bank Transfer"),
            Expense(user_id=user.id, category="Groceries", amount=income_amt * 0.12, date=today.replace(day=5), description="Supermarket & daily provisions", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Utilities", amount=income_amt * 0.05, date=today.replace(day=8), description="Electricity, Water & High-speed Wifi", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Transportation", amount=income_amt * 0.06, date=today.replace(day=10), description="Metro & Fuel expenses", is_essential=True, payment_method="UPI"),
            Expense(user_id=user.id, category="Food & Dining", amount=income_amt * 0.09, date=today.replace(day=14), description="Weekend dining & delivery orders", is_essential=False, payment_method="Credit Card"),
            Expense(user_id=user.id, category="Entertainment", amount=income_amt * 0.04, date=today.replace(day=18), description="Movies & fitness subscriptions", is_essential=False, payment_method="Credit Card"),
            Expense(user_id=user.id, category="Shopping", amount=income_amt * 0.05, date=today.replace(day=22), description="Personal shopping & apparel", is_essential=False, payment_method="Debit Card")
        ])
        db.session.add_all([
            SavingGoal(user_id=user.id, name="Emergency Liquid Fund", target_amount=income_amt * 3, current_amount=income_amt * 1.8, target_date=today + timedelta(days=120), category="Emergency"),
            SavingGoal(user_id=user.id, name="Index Fund SIP Portfolio", target_amount=income_amt * 6, current_amount=income_amt * 2.2, target_date=today + timedelta(days=365), category="Investment")
        ])

    db.session.add(ChatMessage(
        user_id=user.id,
        role="assistant",
        content=f"Welcome {user.name}! I've loaded sample starter data for your {user.profile_type} profile. You can log real expenses and incomes anytime using the '+ Add Expense' or '+ Add Income' buttons."
    ))
    db.session.commit()


def seed_database(force_reseed=False):
    """Initializes the database with an active user profile if empty."""
    if not force_reseed and User.query.first():
        print("Database already seeded. Skipping initial seeding.")
        return

    if force_reseed:
        print("Re-seeding database...")
        ChatMessage.query.delete()
        SavingGoal.query.delete()
        BudgetPlan.query.delete()
        Expense.query.delete()
        Income.query.delete()
        User.query.delete()
        db.session.commit()

    print("Creating primary user profile...")
    today = date.today()

    # ----------------------------------------------------
    # SCENARIO 1: Salaried Professional (Rohan Sharma)
    # ----------------------------------------------------
    user1 = User(
        username="rohan_sharma",
        name="Rohan Sharma",
        email="rohan.sharma@techcorp.in",
        profile_type="Salaried",
        scenario_description="IT software engineer in Bengaluru managing monthly salary, flat rent, Blinkit groceries, transport, and 50/30/20 budget allocations.",
        monthly_income_target=85000.0,
        currency_symbol="₹"
    )
    db.session.add(user1)
    db.session.flush()

    # Incomes for Rohan
    db.session.add_all([
        Income(user_id=user1.id, source="TechCorp India Net Salary", amount=80000.0, date=today.replace(day=1), frequency="Monthly", notes="Net take-home salary after PF & TDS"),
        Income(user_id=user1.id, source="Mutual Fund & Stock Dividends", amount=5000.0, date=today.replace(day=15), frequency="Quarterly", notes="Quarterly dividend payout")
    ])

    # Expenses for Rohan (Total = ₹51,700, Net Savings = ₹33,300)
    db.session.add_all([
        Expense(user_id=user1.id, category="Housing & Rent", amount=24000.0, date=today.replace(day=2), description="2BHK Flat Rent in Indiranagar", is_essential=True, payment_method="Bank Transfer"),
        Expense(user_id=user1.id, category="Groceries", amount=8200.0, date=today.replace(day=5), description="Blinkit, Swiggy Instamart & BigBasket", is_essential=True, payment_method="Credit Card"),
        Expense(user_id=user1.id, category="Transportation", amount=4200.0, date=today.replace(day=7), description="Namma Metro Smart Card & Petrol", is_essential=True, payment_method="UPI"),
        Expense(user_id=user1.id, category="Utilities", amount=2800.0, date=today.replace(day=10), description="BESCOM Electricity & ACT Fibernet", is_essential=True, payment_method="UPI"),
        Expense(user_id=user1.id, category="Food & Dining", amount=6800.0, date=today.replace(day=12), description="Weekend dinners & Zomato orders", is_essential=False, payment_method="Credit Card"),
        Expense(user_id=user1.id, category="Entertainment", amount=3200.0, date=today.replace(day=14), description="Cult.fit membership & PVR movie tickets", is_essential=False, payment_method="UPI"),
        Expense(user_id=user1.id, category="Healthcare", amount=1500.0, date=today.replace(day=18), description="Apollo Pharmacy & routine vitamins", is_essential=True, payment_method="Debit Card"),
        Expense(user_id=user1.id, category="Shopping", amount=3500.0, date=today.replace(day=20), description="Myntra sale clothing & accessories", is_essential=False, payment_method="Credit Card")
    ])

    # Budgets for Rohan (50/30/20 Standard in ₹)
    db.session.add_all([
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Housing & Rent", allocated_amount=24500.0, rule_type="50/30/20"),
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Groceries", allocated_amount=9000.0, rule_type="50/30/20"),
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Transportation", allocated_amount=5000.0, rule_type="50/30/20"),
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Utilities", allocated_amount=3500.0, rule_type="50/30/20"),
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Food & Dining", allocated_amount=6000.0, rule_type="50/30/20"),
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Entertainment", allocated_amount=4000.0, rule_type="50/30/20"),
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Shopping", allocated_amount=4000.0, rule_type="50/30/20"),
        BudgetPlan(user_id=user1.id, month=today.month, year=today.year, category="Emergency / Savings Fund", allocated_amount=17000.0, rule_type="50/30/20")
    ])

    # Goals for Rohan
    db.session.add_all([
        SavingGoal(user_id=user1.id, name="6-Month Emergency Fund in High-Yield FD", target_amount=250000.0, current_amount=160000.0, target_date=today + timedelta(days=120), category="Emergency"),
        SavingGoal(user_id=user1.id, name="Nifty 50 Index Mutual Fund SIP Portfolio", target_amount=500000.0, current_amount=185000.0, target_date=today + timedelta(days=365), category="Investment")
    ])

    db.session.add(ChatMessage(
        user_id=user1.id,
        role="assistant",
        content="Namaste Rohan! I have analyzed your salaried finances. Your net take-home income is ₹85,000, and your savings rate is a healthy 39.2% (₹33,300 saved this month). Food & Dining was slightly above target at ₹6,800 (vs ₹6,000 allocated); redirecting ₹800 towards your Nifty 50 SIP will compound significantly."
    ))

    # ----------------------------------------------------
    # SCENARIO 2: College Student (Aarav Patel) - POCKET MONEY TOTAL: ₹6,000
    # ----------------------------------------------------
    user2 = User(
        username="aarav_patel",
        name="Aarav Patel",
        email="aarav.patel@enggcollege.edu.in",
        profile_type="Student",
        scenario_description="Undergraduate college student managing on ₹6,000 monthly pocket money, tracking hostel mess, Xerox study notes, canteen chai, and saving for a laptop.",
        monthly_income_target=6000.0,
        currency_symbol="₹"
    )
    db.session.add(user2)
    db.session.flush()

    # Incomes for Aarav (Total Pocket Money = ₹6,000)
    db.session.add_all([
        Income(user_id=user2.id, source="Monthly Pocket Money from Parents", amount=4500.0, date=today.replace(day=1), frequency="Monthly", notes="Family allowance for food, travel & stationery"),
        Income(user_id=user2.id, source="High School Science Tutoring Gig", amount=1500.0, date=today.replace(day=15), frequency="Monthly", notes="Weekend coaching classes (Pocket Money supplement)")
    ])

    # Expenses for Aarav (Total = ₹5,100, Net Savings = ₹900)
    db.session.add_all([
        Expense(user_id=user2.id, category="Housing & Rent", amount=2400.0, date=today.replace(day=1), description="Shared Student PG Hostel & Mess Charges", is_essential=True, payment_method="UPI"),
        Expense(user_id=user2.id, category="Groceries", amount=850.0, date=today.replace(day=4), description="Fruit stall, milk & hostel snacks", is_essential=True, payment_method="UPI"),
        Expense(user_id=user2.id, category="Education", amount=450.0, date=today.replace(day=6), description="Engineering notes, Xerox & assignment files", is_essential=True, payment_method="Cash"),
        Expense(user_id=user2.id, category="Food & Dining", amount=650.0, date=today.replace(day=9), description="College canteen Chai, Samosa & Maggi breaks", is_essential=False, payment_method="UPI"),
        Expense(user_id=user2.id, category="Transportation", amount=350.0, date=today.replace(day=11), description="Student City Bus Pass", is_essential=True, payment_method="UPI"),
        Expense(user_id=user2.id, category="Entertainment", amount=400.0, date=today.replace(day=16), description="Monthly 5G Jio mobile recharge & chai with friends", is_essential=False, payment_method="UPI")
    ])

    # Budgets for Aarav (Lean Student Plan for ₹6,000 budget)
    db.session.add_all([
        BudgetPlan(user_id=user2.id, month=today.month, year=today.year, category="Housing & Rent", allocated_amount=2400.0, rule_type="Lean Student"),
        BudgetPlan(user_id=user2.id, month=today.month, year=today.year, category="Groceries", allocated_amount=900.0, rule_type="Lean Student"),
        BudgetPlan(user_id=user2.id, month=today.month, year=today.year, category="Education", allocated_amount=500.0, rule_type="Lean Student"),
        BudgetPlan(user_id=user2.id, month=today.month, year=today.year, category="Food & Dining", allocated_amount=550.0, rule_type="Lean Student"),
        BudgetPlan(user_id=user2.id, month=today.month, year=today.year, category="Transportation", allocated_amount=400.0, rule_type="Lean Student"),
        BudgetPlan(user_id=user2.id, month=today.month, year=today.year, category="Entertainment", allocated_amount=350.0, rule_type="Lean Student"),
        BudgetPlan(user_id=user2.id, month=today.month, year=today.year, category="Emergency / Savings", allocated_amount=900.0, rule_type="Lean Student")
    ])

    # Goals for Aarav
    db.session.add_all([
        SavingGoal(user_id=user2.id, name="Coding Laptop Upgrade Fund", target_amount=45000.0, current_amount=12500.0, target_date=today + timedelta(days=180), category="Technology"),
        SavingGoal(user_id=user2.id, name="Student Emergency Reserve", target_amount=5000.0, current_amount=2200.0, target_date=today + timedelta(days=60), category="Emergency")
    ])

    db.session.add(ChatMessage(
        user_id=user2.id,
        role="assistant",
        content="Namaste Aarav! You are managing a ₹6,000 monthly pocket money budget admirably. Your total outflow is ₹5,100, leaving you with ₹900 in monthly savings (15% savings rate). Note that Food & Dining (₹650) was slightly above your ₹550 limit due to canteen outings; sticking strictly to ₹550 will keep you on track for your ₹45,000 Laptop Fund!"
    ))

    # ----------------------------------------------------
    # SCENARIO 3: Freelancer (Priya Verma)
    # ----------------------------------------------------
    user3 = User(
        username="priya_verma",
        name="Priya Verma",
        email="priya@vermastudios.in",
        profile_type="Freelancer",
        scenario_description="Freelance UI/UX designer with variable multi-client income in Mumbai, managing advance tax reserves, client subscriptions, and runway.",
        monthly_income_target=125000.0,
        currency_symbol="₹"
    )
    db.session.add(user3)
    db.session.flush()

    # Incomes for Priya (Total = ₹1,25,000)
    db.session.add_all([
        Income(user_id=user3.id, source="Fintech Client App UI Redesign", amount=75000.0, date=today.replace(day=3), frequency="Client Project", notes="Milestone 2 payment via NEFT"),
        Income(user_id=user3.id, source="Monthly Brand Consulting Retainer", amount=35000.0, date=today.replace(day=10), frequency="Monthly", notes="Ongoing retainer contract"),
        Income(user_id=user3.id, source="Figma Community UI Kit Sales", amount=15000.0, date=today.replace(day=18), frequency="One-time", notes="Digital design template royalties")
    ])

    # Expenses for Priya (Total = ₹74,500, Net Savings = ₹50,500)
    db.session.add_all([
        Expense(user_id=user3.id, category="Housing & Rent", amount=32000.0, date=today.replace(day=1), description="Studio Apartment Rent in Bandra", is_essential=True, payment_method="Bank Transfer"),
        Expense(user_id=user3.id, category="Business & Subscriptions", amount=4500.0, date=today.replace(day=4), description="Figma Organization, Adobe CC & Cloud Hosting", is_essential=True, payment_method="Credit Card"),
        Expense(user_id=user3.id, category="Healthcare", amount=5500.0, date=today.replace(day=5), description="HDFC ERGO Comprehensive Health Insurance", is_essential=True, payment_method="UPI"),
        Expense(user_id=user3.id, category="Tax & Emergency Buffer", amount=25000.0, date=today.replace(day=8), description="Quarterly Advance Tax Reserve Transfer", is_essential=True, payment_method="Bank Transfer"),
        Expense(user_id=user3.id, category="Groceries", amount=9500.0, date=today.replace(day=12), description="Nature's Basket & Local Organic Mandi", is_essential=True, payment_method="UPI"),
        Expense(user_id=user3.id, category="Food & Dining", amount=4200.0, date=today.replace(day=15), description="Client coffee meetings & co-working lunch", is_essential=False, payment_method="Credit Card"),
        Expense(user_id=user3.id, category="Utilities", amount=3800.0, date=today.replace(day=21), description="Airtel Xstream Gigabit Fiber & Electricity", is_essential=True, payment_method="UPI")
    ])

    # Budgets for Priya (Irregular Income Buffer in ₹)
    db.session.add_all([
        BudgetPlan(user_id=user3.id, month=today.month, year=today.year, category="Housing & Rent", allocated_amount=33000.0, rule_type="Irregular Income Buffer"),
        BudgetPlan(user_id=user3.id, month=today.month, year=today.year, category="Business & Subscriptions", allocated_amount=5000.0, rule_type="Irregular Income Buffer"),
        BudgetPlan(user_id=user3.id, month=today.month, year=today.year, category="Healthcare", allocated_amount=6000.0, rule_type="Irregular Income Buffer"),
        BudgetPlan(user_id=user3.id, month=today.month, year=today.year, category="Tax & Emergency Buffer", allocated_amount=26000.0, rule_type="Irregular Income Buffer"),
        BudgetPlan(user_id=user3.id, month=today.month, year=today.year, category="Groceries", allocated_amount=10000.0, rule_type="Irregular Income Buffer"),
        BudgetPlan(user_id=user3.id, month=today.month, year=today.year, category="Food & Dining", allocated_amount=5000.0, rule_type="Irregular Income Buffer"),
        BudgetPlan(user_id=user3.id, month=today.month, year=today.year, category="Utilities", allocated_amount=4000.0, rule_type="Irregular Income Buffer")
    ])

    # Goals for Priya
    db.session.add_all([
        SavingGoal(user_id=user3.id, name="6-Month Freelance Runway Buffer", target_amount=450000.0, current_amount=285000.0, target_date=today + timedelta(days=180), category="Emergency"),
        SavingGoal(user_id=user3.id, name="Apple MacBook Pro M3 Max Workstation", target_amount=195000.0, current_amount=98000.0, target_date=today + timedelta(days=90), category="Technology")
    ])

    db.session.add(ChatMessage(
        user_id=user3.id,
        role="assistant",
        content="Namaste Priya! Your freelance billing this month reached ₹1,25,000. Moving ₹25,000 into your Advance Tax Reserve is textbook financial discipline. Your emergency cushion covers 3.8 months of living costs; ramping this to 6 months (₹4,50,000) will keep your freelance business resilient across seasonal cycles."
    ))

    # ----------------------------------------------------
    # SCENARIO 4: Household Manager (The Mehta Family)
    # ----------------------------------------------------
    user4 = User(
        username="the_mehtas",
        name="The Mehta Household",
        email="family@mehtahome.in",
        profile_type="Household",
        scenario_description="Multi-earner Indian family in Delhi-NCR managing home loan EMI, kids CBSE schooling, D-Mart groceries, and higher education funds.",
        monthly_income_target=165000.0,
        currency_symbol="₹"
    )
    db.session.add(user4)
    db.session.flush()

    # Incomes for Mehtas (Total = ₹1,65,000)
    db.session.add_all([
        Income(user_id=user4.id, source="Rajesh - VP Operations Net Salary", amount=95000.0, date=today.replace(day=1), frequency="Monthly", notes="Direct corporate salary deposit via HDFC"),
        Income(user_id=user4.id, source="Kavita - Healthcare Consulting", amount=70000.0, date=today.replace(day=15), frequency="Bi-weekly", notes="Monthly professional consulting retainer")
    ])

    # Expenses for Mehtas (Total = ₹1,13,500, Net Savings = ₹51,500)
    db.session.add_all([
        Expense(user_id=user4.id, category="Housing & Rent", amount=46000.0, date=today.replace(day=1), description="SBI Home Loan EMI & Maintenance", is_essential=True, payment_method="Bank Transfer"),
        Expense(user_id=user4.id, category="Groceries", amount=18500.0, date=today.replace(day=4), description="D-Mart Bulk Monthly Stock & Vegetable Mandi", is_essential=True, payment_method="Credit Card"),
        Expense(user_id=user4.id, category="Education", amount=14000.0, date=today.replace(day=7), description="Two Kids CBSE School Fees & Tuition", is_essential=True, payment_method="UPI"),
        Expense(user_id=user4.id, category="Transportation", amount=11200.0, date=today.replace(day=10), description="Maruti Grand Vitara EMI & Fuel/Fastag", is_essential=True, payment_method="Bank Transfer"),
        Expense(user_id=user4.id, category="Utilities", amount=6200.0, date=today.replace(day=12), description="BSES Electricity, IGL Piped Gas & Broadband", is_essential=True, payment_method="UPI"),
        Expense(user_id=user4.id, category="Healthcare", amount=5800.0, date=today.replace(day=14), description="Parents Chronic Diabetes Meds & Doctor Consult", is_essential=True, payment_method="Credit Card"),
        Expense(user_id=user4.id, category="Food & Dining", amount=7600.0, date=today.replace(day=17), description="Family Weekend Dinner & Haldiram's", is_essential=False, payment_method="Credit Card"),
        Expense(user_id=user4.id, category="Entertainment", amount=4200.0, date=today.replace(day=22), description="Family Movie outing & Kids amusement park", is_essential=False, payment_method="UPI")
    ])

    # Budgets for Mehtas (Household Family Plan in ₹)
    db.session.add_all([
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Housing & Rent", allocated_amount=47000.0, rule_type="Household Family Plan"),
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Groceries", allocated_amount=19000.0, rule_type="Household Family Plan"),
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Education", allocated_amount=15000.0, rule_type="Household Family Plan"),
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Transportation", allocated_amount=12000.0, rule_type="Household Family Plan"),
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Utilities", allocated_amount=7000.0, rule_type="Household Family Plan"),
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Healthcare", allocated_amount=7000.0, rule_type="Household Family Plan"),
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Food & Dining", allocated_amount=7000.0, rule_type="Household Family Plan"),
        BudgetPlan(user_id=user4.id, month=today.month, year=today.year, category="Entertainment", allocated_amount=5000.0, rule_type="Household Family Plan")
    ])

    # Goals for Mehtas
    db.session.add_all([
        SavingGoal(user_id=user4.id, name="Kids Higher Education & Sukanya Samriddhi Fund", target_amount=1500000.0, current_amount=620000.0, target_date=today + timedelta(days=730), category="Education"),
        SavingGoal(user_id=user4.id, name="Family Diwali Vacation to Kashmir", target_amount=120000.0, current_amount=72000.0, target_date=today + timedelta(days=120), category="Family"),
        SavingGoal(user_id=user4.id, name="Home Festive Renovation Sinking Fund", target_amount=200000.0, current_amount=115000.0, target_date=today + timedelta(days=240), category="Emergency")
    ])

    db.session.add(ChatMessage(
        user_id=user4.id,
        role="assistant",
        content="Namaste Mehta Family! Your combined household cashflow is ₹1,65,000/month with ₹1,13,500 allocated to family obligations. You are saving ₹51,500 (31.2% savings rate), keeping your essential needs ratio at a safe 61.6%. Your Kashmir vacation fund is already 60% funded (₹72,000/1,20,000)."
    ))

    db.session.commit()
    print("Database successfully re-seeded with realistic Indian rupee (INR) scenarios!")
