import unittest
import json
from app import app, db
from models import User, Income, Expense, BudgetPlan, SavingGoal, ChatMessage

class PersonalFinanceAdvisorTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            # Seed test user
            user = User(
                username='test_user',
                name='Test User',
                email='test@example.com',
                profile_type='Salaried',
                scenario_description='Test salaried professional profile',
                monthly_income_target=5000.0,
                currency_symbol='$'
            )
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_users(self):
        res = self.client.get('/api/users')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue('users' in data)
        self.assertGreaterEqual(len(data['users']), 1)

    def test_add_and_delete_income(self):
        # Add income
        payload = {
            'source': 'Consulting Gig',
            'amount': 1200.0,
            'frequency': 'One-time',
            'notes': 'Website design fee',
            'date': '2026-09-01'
        }
        res = self.client.post(f'/api/incomes?user_id={self.user_id}', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        income_id = data['income']['id']

        # Verify listed
        res_list = self.client.get(f'/api/incomes?user_id={self.user_id}')
        incomes = res_list.get_json()
        self.assertEqual(len(incomes), 1)
        self.assertEqual(incomes[0]['source'], 'Consulting Gig')

        # Delete income
        res_del = self.client.delete(f'/api/incomes/{income_id}?user_id={self.user_id}')
        self.assertEqual(res_del.status_code, 200)

    def test_add_and_delete_expense(self):
        # Add expense
        payload = {
            'description': 'Supermarket Groceries',
            'amount': 150.0,
            'category': 'Groceries',
            'is_essential': True,
            'payment_method': 'Credit Card',
            'date': '2026-09-05'
        }
        res = self.client.post(f'/api/expenses?user_id={self.user_id}', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        expense_id = data['expense']['id']

        # Delete expense
        res_del = self.client.delete(f'/api/expenses/{expense_id}?user_id={self.user_id}')
        self.assertEqual(res_del.status_code, 200)

    def test_auto_generate_budget(self):
        # Seed an income first
        self.client.post(f'/api/incomes?user_id={self.user_id}', json={
            'source': 'Salary', 'amount': 4000.0, 'date': '2026-09-01'
        })

        # Generate 50/30/20 budget
        res = self.client.post(f'/api/budgets/generate?user_id={self.user_id}', json={'rule_type': '50/30/20'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['budgets']), 0)

    def test_goals_and_contribute(self):
        # Create goal
        payload = {
            'name': 'Emergency Buffer',
            'target_amount': 5000.0,
            'current_amount': 1000.0,
            'category': 'Emergency'
        }
        res = self.client.post(f'/api/goals?user_id={self.user_id}', json=payload)
        self.assertEqual(res.status_code, 201)
        goal_id = res.get_json()['goal']['id']

        # Contribute to goal
        res_contrib = self.client.post(f'/api/goals/{goal_id}/contribute?user_id={self.user_id}', json={'amount': 500.0})
        self.assertEqual(res_contrib.status_code, 200)
        updated_goal = res_contrib.get_json()['goal']
        self.assertEqual(updated_goal['current_amount'], 1500.0)
        self.assertEqual(updated_goal['progress_percentage'], 30.0)

    def test_dashboard_analytics_and_health_score(self):
        # Add income and expenses
        self.client.post(f'/api/incomes?user_id={self.user_id}', json={
            'source': 'Salary', 'amount': 4000.0, 'date': '2026-09-01'
        })
        self.client.post(f'/api/expenses?user_id={self.user_id}', json={
            'description': 'Rent', 'amount': 1200.0, 'category': 'Housing & Rent', 'is_essential': True, 'date': '2026-09-02'
        })
        self.client.post(f'/api/expenses?user_id={self.user_id}', json={
            'description': 'Dinner', 'amount': 200.0, 'category': 'Food & Dining', 'is_essential': False, 'date': '2026-09-03'
        })

        res = self.client.get(f'/api/analytics/dashboard?user_id={self.user_id}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue('context' in data)
        self.assertTrue('health' in data)
        self.assertEqual(data['context']['total_income'], 4000.0)
        self.assertEqual(data['context']['total_expense'], 1400.0)
        self.assertEqual(data['context']['net_savings'], 2600.0)
        self.assertGreater(data['health']['score'], 0)

    def test_monthly_report_generation(self):
        self.client.post(f'/api/incomes?user_id={self.user_id}', json={
            'source': 'Salary', 'amount': 5000.0, 'date': '2026-09-01'
        })
        res = self.client.get(f'/api/analytics/monthly-report?user_id={self.user_id}')
        self.assertEqual(res.status_code, 200)
        report = res.get_json()
        self.assertTrue('report_title' in report)
        self.assertTrue('ai_verdict' in report)
        self.assertTrue('action_items' in report)

    def test_ai_advisor_chat(self):
        res = self.client.post(f'/api/advisor/chat?user_id={self.user_id}', json={
            'message': 'How can I optimize my spending according to 50/30/20?'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue('bot_message' in data)
        self.assertIn('50/30/20', data['bot_message']['content'])

if __name__ == '__main__':
    unittest.main()
