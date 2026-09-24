/* ===================================================================
   BEACON - AI PERSONAL FINANCE ADVISOR
   Frontend Application Engine (ES6 / Chart.js)
   =================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Application State
    const state = {
        currentUser: null,
        users: [],
        activeTab: 'overview',
        dashboard: null,
        expenses: [],
        incomes: [],
        charts: {
            doughnut: null,
            bar: null
        }
    };

    // Category Palette
    const categoryColors = {
        'Housing & Rent': '#6366F1',
        'Food & Dining': '#F59E0B',
        'Groceries': '#10B981',
        'Transportation': '#06B6D4',
        'Utilities': '#8B5CF6',
        'Healthcare': '#EC4899',
        'Education': '#3B82F6',
        'Entertainment': '#F43F5E',
        'Shopping': '#D946EF',
        'Business & Subscriptions': '#14B8A6',
        'Tax & Emergency Buffer': '#EAB308',
        'Emergency / Savings': '#10B981',
        'Emergency / Savings Fund': '#10B981',
        'Miscellaneous': '#64748B'
    };

    // Format Currency Helper
    function formatMoney(amt, symbol = null) {
        const sym = symbol !== null ? symbol : (state.currentUser?.currency_symbol || '₹');
        const num = parseFloat(amt) || 0;
        return `${sym}${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    // Format Date Helper
    function formatDate(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    // Init App
    async function init() {
        setupEventListeners();
        await loadUsers();
        await loadSettingsStatus();
        await refreshAllData();
        // Set today's date in date pickers
        const todayStr = new Date().toISOString().split('T')[0];
        document.querySelectorAll('input[type="date"]').forEach(input => {
            if (!input.value) input.value = todayStr;
        });
    }

    // Event Listeners Registration
    function setupEventListeners() {
        // Navigation Tabs
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetTab = btn.getAttribute('data-tab');
                switchTab(targetTab);
            });
        });

        // Quick Action Buttons
        document.getElementById('btn-quick-income')?.addEventListener('click', () => openModal('modal-income'));
        document.getElementById('btn-quick-expense')?.addEventListener('click', () => openModal('modal-expense'));
        document.getElementById('btn-quick-ask-ai')?.addEventListener('click', () => switchTab('chat'));
        document.getElementById('btn-view-all-txns')?.addEventListener('click', () => switchTab('transactions'));

        // Modals Openers & Profile Handlers
        document.getElementById('btn-open-profile-modal')?.addEventListener('click', openProfileModal);
        document.getElementById('btn-quick-reset-data')?.addEventListener('click', handleResetData);
        document.getElementById('btn-settings-reset-data')?.addEventListener('click', handleResetData);
        document.getElementById('btn-load-mock-data')?.addEventListener('click', handleLoadMockData);
        document.getElementById('form-edit-profile')?.addEventListener('submit', handleSaveProfile);

        document.getElementById('btn-open-income-modal')?.addEventListener('click', () => openModal('modal-income'));
        document.getElementById('btn-open-expense-modal')?.addEventListener('click', () => openModal('modal-expense'));
        document.getElementById('btn-add-budget-category')?.addEventListener('click', () => openModal('modal-budget'));
        document.getElementById('btn-add-goal')?.addEventListener('click', () => openModal('modal-goal'));
        document.getElementById('btn-open-settings')?.addEventListener('click', () => openModal('modal-settings'));

        // Modal Closers
        document.querySelectorAll('[data-close]').forEach(el => {
            el.addEventListener('click', () => {
                const modalId = el.getAttribute('data-close');
                closeModal(modalId);
            });
        });

        // Close on backdrop click
        document.querySelectorAll('.modal-backdrop').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // Forms Submissions
        document.getElementById('form-add-expense')?.addEventListener('submit', handleAddExpense);
        document.getElementById('form-add-income')?.addEventListener('submit', handleAddIncome);
        document.getElementById('form-add-budget')?.addEventListener('submit', handleAddBudget);
        document.getElementById('form-add-goal')?.addEventListener('submit', handleAddGoal);
        document.getElementById('form-contribute-goal')?.addEventListener('submit', handleContributeGoal);
        document.getElementById('form-settings')?.addEventListener('submit', handleSaveSettings);

        // Budget Auto-Generate with AI
        document.getElementById('btn-auto-generate-budget')?.addEventListener('click', handleAutoGenerateBudget);

        // Transaction Search and Category Filter
        document.getElementById('txn-search-input')?.addEventListener('input', renderTransactionsTable);
        document.getElementById('txn-category-filter')?.addEventListener('change', renderTransactionsTable);

        // Chat Input & Send
        document.getElementById('btn-send-chat')?.addEventListener('click', handleSendMessage);
        document.getElementById('chat-user-input')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });
        document.getElementById('btn-clear-chat')?.addEventListener('click', handleClearChat);

        // Suggestion Chips
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const prompt = chip.getAttribute('data-prompt');
                const input = document.getElementById('chat-user-input');
                if (input) {
                    input.value = prompt;
                    handleSendMessage();
                }
            });
        });
    }

    // Tab Switching
    function switchTab(tabName) {
        state.activeTab = tabName;

        // Nav menu active class
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
        });

        // View panels active class
        document.querySelectorAll('.view-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `view-${tabName}`);
        });

        // Title and Subtitle update
        const titles = {
            'overview': ['Financial Dashboard', 'Real-time cashflow intelligence & automated budget tracking'],
            'transactions': ['Transaction Hub', 'Filter, audit, and log monthly incomes & categorized expenses'],
            'budgets': ['Smart Budget Planner', 'Automated 50/30/20 allocation & category spending limits'],
            'goals': ['Savings Goals & Runway', 'Milestone progress, emergency reserve & financial safety net'],
            'reports': ['Monthly Executive Report', 'Comprehensive financial statement, variance audit & AI action items'],
            'chat': ['Beacon AI Advisor', 'Conversational financial guidance tailored to your financial profile']
        };

        if (titles[tabName]) {
            document.getElementById('current-view-title').textContent = titles[tabName][0];
            document.getElementById('current-view-subtitle').textContent = titles[tabName][1];
        }

        // Lazy load tab data
        if (tabName === 'transactions') renderTransactionsTable();
        if (tabName === 'budgets') loadBudgets();
        if (tabName === 'goals') loadGoals();
        if (tabName === 'reports') loadMonthlyReport();
        if (tabName === 'chat') loadChatHistory();
        if (tabName === 'overview') updateCharts();
    }

    // Modal Helpers
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.add('active');
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove('active');
    }

    // Load Active User Profile
    async function loadUsers() {
        try {
            const currentRes = await fetch('/api/users/current');
            state.currentUser = await currentRes.json();
            updateProfileUI();
        } catch (err) {
            console.error('Failed to load user profile:', err);
        }
    }

    // Update Profile Information in Sidebar and Headers
    function updateProfileUI() {
        if (!state.currentUser) return;
        const u = state.currentUser;
        const sym = u.currency_symbol || '₹';

        const nameEl = document.getElementById('profile-user-name');
        if (nameEl) nameEl.textContent = u.name || u.username || 'Personal Finance';

        const badgeEl = document.getElementById('profile-type-badge');
        if (badgeEl) badgeEl.textContent = u.profile_type || 'Salaried';

        const targetEl = document.getElementById('profile-monthly-target');
        if (targetEl) targetEl.textContent = formatMoney(u.monthly_income_target || 0, sym);

        const avatarEl = document.getElementById('profile-avatar-circle');
        if (avatarEl) {
            const nameStr = (u.name || u.username || 'U').trim();
            avatarEl.textContent = nameStr.charAt(0).toUpperCase();
        }

        const reportNameEl = document.getElementById('report-client-name');
        if (reportNameEl) reportNameEl.textContent = u.name || 'User';

        // Update currency labels in forms
        document.querySelectorAll('.currency-prefix').forEach(el => {
            el.textContent = sym;
        });
    }

    // Open User Profile Modal
    function openProfileModal() {
        if (!state.currentUser) return;
        const u = state.currentUser;

        const nameInput = document.getElementById('profile-input-name');
        if (nameInput) nameInput.value = u.name || '';

        const typeInput = document.getElementById('profile-input-type');
        if (typeInput) typeInput.value = u.profile_type || 'Salaried';

        const currInput = document.getElementById('profile-input-currency');
        if (currInput) currInput.value = u.currency_symbol || '₹';

        const incInput = document.getElementById('profile-input-income');
        if (incInput) incInput.value = u.monthly_income_target || '';

        const bioInput = document.getElementById('profile-input-bio');
        if (bioInput) bioInput.value = u.scenario_description || '';

        const clearCheck = document.getElementById('profile-checkbox-clear');
        if (clearCheck) clearCheck.checked = false;

        openModal('modal-profile');
    }

    // Save User Profile
    async function handleSaveProfile(e) {
        e.preventDefault();
        const name = document.getElementById('profile-input-name').value.trim();
        const profile_type = document.getElementById('profile-input-type').value;
        const currency_symbol = document.getElementById('profile-input-currency').value;
        const monthly_income_target = parseFloat(document.getElementById('profile-input-income').value) || 0;
        const scenario_description = document.getElementById('profile-input-bio').value.trim();
        const clear_data = document.getElementById('profile-checkbox-clear')?.checked || false;

        if (!name) {
            showToast('Please enter your full name', 'error');
            return;
        }

        try {
            const res = await fetch('/api/users/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    profile_type,
                    currency_symbol,
                    monthly_income_target,
                    scenario_description,
                    clear_data
                })
            });
            const data = await res.json();
            if (data.success) {
                state.currentUser = data.user;
                closeModal('modal-profile');
                updateProfileUI();
                await refreshAllData();
                showToast(`Welcome, ${data.user.name}! Your profile is ready.`, 'success');
            } else {
                showToast(data.error || 'Failed to update profile', 'error');
            }
        } catch (err) {
            console.error('Error saving profile:', err);
            showToast('Network error while saving profile', 'error');
        }
    }

    // Reset All Transactions to Clean Slate
    async function handleResetData() {
        const confirmed = confirm("Are you sure you want to clear all expenses and incomes? You will have a completely clean ledger to add your own real transactions.");
        if (!confirmed) return;

        try {
            const res = await fetch('/api/data/reset', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-settings');
                await refreshAllData();
                showToast('All transaction records cleared. Your ledger is now fresh!', 'success');
            } else {
                showToast('Failed to reset records', 'error');
            }
        } catch (err) {
            console.error('Error resetting data:', err);
            showToast('Network error while resetting data', 'error');
        }
    }

    // Load Sample Mock Data
    async function handleLoadMockData() {
        try {
            const res = await fetch('/api/data/seed-mock', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-settings');
                await refreshAllData();
                showToast('Sample demonstration data loaded successfully!', 'success');
            } else {
                showToast('Failed to load demo data', 'error');
            }
        } catch (err) {
            console.error('Error loading mock data:', err);
            showToast('Network error loading demo data', 'error');
        }
    }

    // Load Settings / Gemini API Key Status
    async function loadSettingsStatus() {
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();
            const label = document.getElementById('engine-label');
            const banner = document.getElementById('settings-status-text');

            if (data.has_gemini_key) {
                label.textContent = 'Gemini 3.6 Flash';
                banner.innerHTML = `<span class="text-emerald">✓ Active: Gemini 3.6 Flash (${data.masked_key})</span>`;
            } else {
                label.textContent = 'Autonomous AI';
                banner.innerHTML = `<span>Operating on Built-in Deterministic AI Engine</span>`;
            }
        } catch (err) {
            console.error('Failed to load settings:', err);
        }
    }

    // Refresh All Data Across Dashboard
    async function refreshAllData() {
        await Promise.all([
            loadDashboardAnalytics(),
            loadTransactionsData(),
            loadBudgets(),
            loadGoals(),
            loadMonthlyReport(),
            loadChatHistory()
        ]);
    }

    // Load Dashboard Analytics & Health Score
    async function loadDashboardAnalytics() {
        try {
            const res = await fetch('/api/analytics/dashboard');
            const data = await res.json();
            state.dashboard = data;
            const ctx = data.context || {};
            const health = data.health || {};
            const sym = state.currentUser?.currency_symbol || '₹';

            // Top Metrics
            document.getElementById('stat-total-income').textContent = formatMoney(ctx.total_income, sym);
            document.getElementById('stat-total-expense').textContent = formatMoney(ctx.total_expense, sym);
            document.getElementById('stat-net-savings').textContent = formatMoney(ctx.net_savings, sym);
            document.getElementById('stat-savings-rate').textContent = `${ctx.savings_rate || 0}% Savings Rate`;
            document.getElementById('stat-runway-months').textContent = `${ctx.emergency_runway_months || 0} mo`;

            // Dynamic Metric Hints
            document.getElementById('stat-expense-count').textContent = `${formatMoney(ctx.essential_expenses || 0, sym)} Essential`;
            document.getElementById('stat-runway-status').textContent = `${formatMoney(ctx.emergency_saved || 0, sym)} Saved`;

            // Alerts
            renderAlerts(data.alerts || []);

            // Health Score Radial
            const scoreNum = health.score || 0;
            document.getElementById('health-score-num').textContent = scoreNum;
            const ratingBadge = document.getElementById('health-rating-badge');
            ratingBadge.textContent = health.rating || 'Moderate';
            ratingBadge.className = `badge-pill text-${health.badge_color || 'indigo'}`;

            // Circle SVG Dasharray (circumference ~ 264)
            const circleBar = document.getElementById('health-circle-bar');
            if (circleBar) {
                const strokeVal = `${scoreNum}, 100`;
                circleBar.setAttribute('stroke-dasharray', strokeVal);
                circleBar.style.stroke = scoreNum >= 75 ? 'var(--emerald)' : (scoreNum >= 50 ? 'var(--amber)' : 'var(--rose)');
            }

            // Subscores Breakdown
            const subContainer = document.getElementById('health-subscores-container');
            if (subContainer && health.breakdown) {
                subContainer.innerHTML = Object.values(health.breakdown).map(b => {
                    const pct = Math.round((b.value / b.max) * 100);
                    const color = pct >= 70 ? 'var(--emerald)' : (pct >= 40 ? 'var(--amber)' : 'var(--rose)');
                    return `
                        <div class="health-subscore-item">
                            <div class="subscore-header">
                                <span>${b.label}</span>
                                <span>${b.value}/${b.max}</span>
                            </div>
                            <div class="subscore-track">
                                <div class="subscore-fill" style="width: ${pct}%; background: ${color};"></div>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            // Health Insights
            const insightsContainer = document.getElementById('health-insights-list');
            if (insightsContainer && health.insights) {
                insightsContainer.innerHTML = health.insights.map(i => `
                    <div class="insight-point">
                        <i class="fa-solid fa-angle-right text-indigo"></i>
                        <span>${i}</span>
                    </div>
                `).join('');
            }

            // 50/30/20 Rule Breakdown
            const needsPct = ctx.needs_ratio || 0;
            const wantsPct = ctx.wants_ratio || 0;
            const savingsPct = ctx.savings_rate || 0;

            document.getElementById('bar-fill-needs').style.width = `${Math.min(100, needsPct)}%`;
            document.getElementById('bar-fill-wants').style.width = `${Math.min(100, wantsPct)}%`;
            document.getElementById('bar-fill-savings').style.width = `${Math.max(0, Math.min(100, savingsPct))}%`;

            document.getElementById('val-needs').textContent = `${formatMoney(ctx.essential_expenses, sym)} (${needsPct}%)`;
            document.getElementById('val-wants').textContent = `${formatMoney(ctx.discretionary_expenses, sym)} (${wantsPct}%)`;
            document.getElementById('val-savings').textContent = `${formatMoney(ctx.net_savings, sym)} (${savingsPct}%)`;

            // Smart Rule Recommendation
            const recBox = document.getElementById('rule-recommendation-text');
            if (recBox) {
                if (needsPct > 55) {
                    recBox.textContent = `Needs consume ${needsPct}% of income (ideal <= 50%). Look for opportunities to lower fixed housing or utility costs.`;
                } else if (wantsPct > 35) {
                    recBox.textContent = `Discretionary wants are running at ${wantsPct}% (ideal <= 30%). Trimming restaurant dining could save an extra $150+/mo.`;
                } else if (savingsPct >= 20) {
                    recBox.textContent = `Optimal 50/30/20 compliance! You are saving ${savingsPct}% of earnings, exceeding the 20% wealth-building threshold.`;
                } else {
                    recBox.textContent = `Aim to increase your savings rate from ${savingsPct}% towards 20% to build an airtight emergency cushion.`;
                }
            }

            // Update Charts
            updateCharts();

        } catch (err) {
            console.error('Failed to load dashboard analytics:', err);
        }
    }

    // Render Alert Banners
    function renderAlerts(alerts) {
        const wrapper = document.getElementById('alerts-wrapper');
        if (!wrapper) return;
        if (!alerts || alerts.length === 0) {
            wrapper.innerHTML = '';
            return;
        }

        wrapper.innerHTML = alerts.map(a => `
            <div class="alert-banner alert-${a.type || 'warning'}">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <div>
                    <strong>${a.title}:</strong> ${a.message}
                </div>
            </div>
        `).join('');
    }

    // Update Chart.js Visualizations
    function updateCharts() {
        if (!state.dashboard || !state.dashboard.context) return;
        const ctx = state.dashboard.context;

        // 1. Doughnut Chart: Category Expenses
        const doughnutCanvas = document.getElementById('categoryDoughnutChart');
        if (doughnutCanvas) {
            const catExpenses = ctx.category_expenses || {};
            const labels = Object.keys(catExpenses);
            const dataVals = Object.values(catExpenses);

            const colors = labels.map(cat => categoryColors[cat] || '#818CF8');

            if (state.charts.doughnut) {
                state.charts.doughnut.destroy();
            }

            if (labels.length > 0) {
                state.charts.doughnut = new Chart(doughnutCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: dataVals,
                            backgroundColor: colors,
                            borderWidth: 2,
                            borderColor: '#111827'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    color: '#9CA3AF',
                                    font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
                                    boxWidth: 12
                                }
                            }
                        }
                    }
                });
            } else {
                state.charts.doughnut = new Chart(doughnutCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: ['No expenses logged yet - Click + Add Expense'],
                        datasets: [{
                            data: [1],
                            backgroundColor: ['rgba(255, 255, 255, 0.07)'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            tooltip: { enabled: false },
                            legend: {
                                position: 'bottom',
                                labels: { color: '#9CA3AF', font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 }, boxWidth: 10 }
                            }
                        }
                    }
                });
            }
        }

        // 2. Bar Chart: Income vs Expense Breakdown
        const barCanvas = document.getElementById('cashflowBarChart');
        if (barCanvas) {
            if (state.charts.bar) {
                state.charts.bar.destroy();
            }

            state.charts.bar = new Chart(barCanvas, {
                type: 'bar',
                data: {
                    labels: ['Monthly Flow'],
                    datasets: [
                        {
                            label: 'Total Income',
                            data: [ctx.total_income || 0],
                            backgroundColor: '#10B981',
                            borderRadius: 8
                        },
                        {
                            label: 'Essential Needs',
                            data: [ctx.essential_expenses || 0],
                            backgroundColor: '#6366F1',
                            borderRadius: 8
                        },
                        {
                            label: 'Discretionary Wants',
                            data: [ctx.discretionary_expenses || 0],
                            backgroundColor: '#F59E0B',
                            borderRadius: 8
                        },
                        {
                            label: 'Net Savings',
                            data: [Math.max(0, ctx.net_savings || 0)],
                            backgroundColor: '#06B6D4',
                            borderRadius: 8
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9CA3AF' }
                        },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: {
                                color: '#9CA3AF',
                                callback: (v) => `₹${v}`
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#9CA3AF',
                                font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
                                boxWidth: 12
                            }
                        }
                    }
                }
            });
        }
    }

    // Load Transactions (Expenses + Incomes)
    async function loadTransactionsData() {
        try {
            const [expRes, incRes] = await Promise.all([
                fetch('/api/expenses'),
                fetch('/api/incomes')
            ]);
            state.expenses = await expRes.json();
            state.incomes = await incRes.json();

            renderRecentTransactionsTable();
            renderTransactionsTable();
        } catch (err) {
            console.error('Failed to load transactions:', err);
        }
    }

    // Render Recent Transactions on Dashboard Overview
    function renderRecentTransactionsTable() {
        const tbody = document.getElementById('recent-txns-tbody');
        if (!tbody) return;

        // Combine and sort by date descending
        const combined = [
            ...state.incomes.map(i => ({ ...i, type: 'Income', category: 'Income' })),
            ...state.expenses.map(e => ({ ...e, type: 'Expense' }))
        ].sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 6);

        if (combined.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No transactions logged yet.</td></tr>`;
            return;
        }

        const sym = state.currentUser?.currency_symbol || '₹';

        tbody.innerHTML = combined.map(item => `
            <tr>
                <td>${formatDate(item.date)}</td>
                <td>
                    <strong>${item.type === 'Income' ? item.source : item.description}</strong>
                    ${item.notes ? `<small class="text-muted d-block">${item.notes}</small>` : ''}
                </td>
                <td>
                    <span class="badge-tag" style="background: rgba(255,255,255,0.05); color: #fff;">
                        ${item.category}
                    </span>
                </td>
                <td>
                    ${item.type === 'Income'
                        ? `<span class="badge-tag badge-income">Income Stream</span>`
                        : (item.is_essential ? `<span class="badge-tag badge-essential">Essential Need</span>` : `<span class="badge-tag badge-discretionary">Discretionary Want</span>`)
                    }
                </td>
                <td class="text-muted">${item.payment_method || item.frequency || 'Direct'}</td>
                <td class="text-right font-weight-bold ${item.type === 'Income' ? 'text-emerald' : 'text-rose'}">
                    ${item.type === 'Income' ? '+' : '-'}${formatMoney(item.amount, sym)}
                </td>
            </tr>
        `).join('');
    }

    // Render Full Filterable Ledger
    function renderTransactionsTable() {
        const tbody = document.getElementById('transactions-table-body');
        if (!tbody) return;

        const searchQuery = (document.getElementById('txn-search-input')?.value || '').toLowerCase();
        const categoryFilter = document.getElementById('txn-category-filter')?.value || 'All';

        let combined = [
            ...state.incomes.map(i => ({ ...i, type: 'Income', category: 'Income', description: i.source })),
            ...state.expenses.map(e => ({ ...e, type: 'Expense' }))
        ];

        // Apply filters
        if (searchQuery) {
            combined = combined.filter(t => (t.description || '').toLowerCase().includes(searchQuery));
        }
        if (categoryFilter !== 'All') {
            combined = combined.filter(t => t.category === categoryFilter);
        }

        combined.sort((a, b) => new Date(b.date) - new Date(a.date));

        if (combined.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No transactions matched your filters.</td></tr>`;
            return;
        }

        const sym = state.currentUser?.currency_symbol || '₹';

        tbody.innerHTML = combined.map(item => `
            <tr>
                <td>
                    ${item.type === 'Income'
                        ? `<span class="badge-tag badge-income"><i class="fa-solid fa-arrow-down"></i> Income</span>`
                        : `<span class="badge-tag badge-expense"><i class="fa-solid fa-arrow-up"></i> Expense</span>`
                    }
                </td>
                <td>${formatDate(item.date)}</td>
                <td>
                    <strong>${item.description}</strong>
                    ${item.notes ? `<small class="text-muted d-block">${item.notes}</small>` : ''}
                </td>
                <td>
                    <span class="badge-tag" style="background: rgba(255,255,255,0.05); color: #fff;">
                        ${item.category}
                    </span>
                </td>
                <td>
                    ${item.type === 'Income'
                        ? `<span class="text-muted">-</span>`
                        : (item.is_essential ? `<span class="badge-tag badge-essential">Essential</span>` : `<span class="badge-tag badge-discretionary">Discretionary</span>`)
                    }
                </td>
                <td class="text-muted">${item.payment_method || item.frequency || 'Direct'}</td>
                <td class="text-right font-weight-bold ${item.type === 'Income' ? 'text-emerald' : 'text-rose'}">
                    ${item.type === 'Income' ? '+' : '-'}${formatMoney(item.amount, sym)}
                </td>
                <td class="text-center">
                    <button class="btn-icon btn-delete-txn" data-type="${item.type}" data-id="${item.id}" title="Delete Record">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        tbody.querySelectorAll('.btn-delete-txn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const type = btn.getAttribute('data-type');
                const id = btn.getAttribute('data-id');
                if (confirm(`Delete this ${type.toLowerCase()} record?`)) {
                    await deleteTransaction(type, id);
                }
            });
        });
    }

    // Delete Transaction Helper
    async function deleteTransaction(type, id) {
        try {
            const endpoint = type === 'Income' ? `/api/incomes/${id}` : `/api/expenses/${id}`;
            const res = await fetch(endpoint, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                await refreshAllData();
            }
        } catch (err) {
            console.error('Failed to delete transaction:', err);
        }
    }

    // Add Expense Handler
    async function handleAddExpense(e) {
        e.preventDefault();
        const desc = document.getElementById('expense-desc').value;
        const amt = document.getElementById('expense-amount').value;
        const date = document.getElementById('expense-date').value;
        const category = document.getElementById('expense-category').value;
        const payment = document.getElementById('expense-payment').value;
        const isEssential = document.getElementById('expense-essential').checked;

        try {
            const res = await fetch('/api/expenses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description: desc,
                    amount: amt,
                    date: date,
                    category: category,
                    payment_method: payment,
                    is_essential: isEssential
                })
            });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-expense');
                document.getElementById('form-add-expense').reset();
                await refreshAllData();
            } else {
                alert(data.error || 'Failed to save expense');
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Add Income Handler
    async function handleAddIncome(e) {
        e.preventDefault();
        const source = document.getElementById('income-source').value;
        const amt = document.getElementById('income-amount').value;
        const date = document.getElementById('income-date').value;
        const frequency = document.getElementById('income-frequency').value;
        const notes = document.getElementById('income-notes').value;

        try {
            const res = await fetch('/api/incomes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source: source,
                    amount: amt,
                    date: date,
                    frequency: frequency,
                    notes: notes
                })
            });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-income');
                document.getElementById('form-add-income').reset();
                await refreshAllData();
            } else {
                alert(data.error || 'Failed to record income');
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Load Smart Budgets
    async function loadBudgets() {
        try {
            const res = await fetch('/api/budgets');
            const data = await res.json();
            const budgets = data.budgets || [];
            const container = document.getElementById('budget-cards-container');
            const sym = state.currentUser?.currency_symbol || '₹';

            // Top budget summary
            document.getElementById('budget-sum-allocated').textContent = formatMoney(data.total_budgeted, sym);
            document.getElementById('budget-sum-spent').textContent = formatMoney(data.total_expense, sym);
            const cushion = data.total_budgeted - data.total_expense;
            document.getElementById('budget-sum-remaining').textContent = formatMoney(cushion, sym);
            document.getElementById('budget-sum-remaining').className = `val ${cushion >= 0 ? 'text-emerald' : 'text-rose'}`;

            if (!container) return;

            if (budgets.length === 0) {
                container.innerHTML = `
                    <div class="card glass-card text-center py-5" style="grid-column: 1/-1;">
                        <i class="fa-solid fa-sliders text-muted mb-3" style="font-size: 2rem;"></i>
                        <h4>No budget targets set for this month</h4>
                        <p class="text-muted mb-3">Click "Auto-Generate with AI" to compute custom limits based on your profile.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = budgets.map(b => {
                const pct = Math.min(100, Math.round(b.percentage_spent));
                const isOver = b.is_overbudget;
                const statusClass = isOver ? 'pct-danger' : (b.percentage_spent >= 80 ? 'pct-warning' : 'pct-safe');
                const barColor = isOver ? 'var(--rose)' : (b.percentage_spent >= 80 ? 'var(--amber)' : 'var(--emerald)');

                return `
                    <div class="budget-card ${isOver ? 'overbudget' : ''}">
                        <div class="budget-card-header">
                            <span class="budget-cat-name">${b.category}</span>
                            <span class="budget-pct-badge ${statusClass}">
                                ${isOver ? '⚠️ Over Budget' : `${b.percentage_spent}%`}
                            </span>
                        </div>
                        <div class="budget-meter-track">
                            <div class="budget-meter-fill" style="width: ${pct}%; background: ${barColor};"></div>
                        </div>
                        <div class="budget-stats-row">
                            <span>Spent: <strong>${formatMoney(b.spent, sym)}</strong></span>
                            <span>Limit: <strong>${formatMoney(b.allocated, sym)}</strong></span>
                        </div>
                        <div class="budget-card-footer">
                            <span class="text-muted" style="font-size: 0.75rem;">
                                ${isOver ? `<span class="text-rose font-weight-bold">+${formatMoney(b.spent - b.allocated, sym)} overrun</span>` : `${formatMoney(b.remaining, sym)} left`}
                            </span>
                            <button class="btn-icon btn-delete-budget" data-id="${b.id}" title="Remove Category Limit">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            container.querySelectorAll('.btn-delete-budget').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.getAttribute('data-id');
                    if (confirm('Remove this category budget allocation?')) {
                        await fetch(`/api/budgets/${id}`, { method: 'DELETE' });
                        await refreshAllData();
                    }
                });
            });

        } catch (err) {
            console.error('Failed to load budgets:', err);
        }
    }

    // Add Budget Form Handler
    async function handleAddBudget(e) {
        e.preventDefault();
        const cat = document.getElementById('budget-category').value;
        const amt = document.getElementById('budget-amount').value;

        try {
            const res = await fetch('/api/budgets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category: cat, allocated_amount: amt, rule_type: 'Custom' })
            });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-budget');
                document.getElementById('form-add-budget').reset();
                await refreshAllData();
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Auto-Generate AI Budget
    async function handleAutoGenerateBudget() {
        const profile = state.currentUser?.profile_type || 'Salaried';
        let ruleType = '50/30/20';
        if (profile === 'Student') ruleType = 'Lean Student';
        else if (profile === 'Freelancer') ruleType = 'Irregular Income Buffer';
        else if (profile === 'Household') ruleType = 'Household Plan';

        if (confirm(`Auto-generate AI budget allocations tailored for ${state.currentUser?.name} (${ruleType})?`)) {
            try {
                const res = await fetch('/api/budgets/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rule_type: ruleType })
                });
                const data = await res.json();
                if (data.success) {
                    await refreshAllData();
                }
            } catch (err) {
                console.error(err);
            }
        }
    }

    // Load Savings Goals & Runway
    async function loadGoals() {
        try {
            const res = await fetch('/api/goals');
            const goals = await res.json();
            const container = document.getElementById('goals-cards-container');
            const sym = state.currentUser?.currency_symbol || '₹';

            // Emergency Runway Banner
            const ctx = state.dashboard?.context || {};
            document.getElementById('runway-total-saved').textContent = formatMoney(ctx.emergency_saved || 0, sym);
            const months = ctx.emergency_runway_months || 0;
            document.getElementById('runway-months-display').textContent = `${months} Months`;

            const evalNote = document.getElementById('runway-eval-note');
            if (months < 1) {
                evalNote.textContent = '⚠️ Critical: Less than 1 month of safety reserves.';
                evalNote.className = 'runway-eval-note text-rose';
            } else if (months < 3) {
                evalNote.textContent = '⚠️ Vulnerable: Below 3 months of baseline living costs.';
                evalNote.className = 'runway-eval-note text-amber';
            } else if (months <= 6) {
                evalNote.textContent = '🛡️ Resilient: Healthy emergency cushion (3-6 months).';
                evalNote.className = 'runway-eval-note text-emerald';
            } else {
                evalNote.textContent = '💎 Anti-fragile: Extraordinary emergency runway (> 6 months).';
                evalNote.className = 'runway-eval-note text-cyan';
            }

            if (!container) return;

            if (goals.length === 0) {
                container.innerHTML = `
                    <div class="card glass-card text-center py-5" style="grid-column: 1/-1;">
                        <i class="fa-solid fa-bullseye text-muted mb-3" style="font-size: 2rem;"></i>
                        <h4>No financial goals created yet</h4>
                        <p class="text-muted mb-3">Create an emergency fund or milestone target to track your progress.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = goals.map(g => {
                const pct = Math.min(100, g.progress_percentage || 0);
                const isCompleted = g.status === 'Completed' || pct >= 100;

                return `
                    <div class="goal-card">
                        <div class="goal-card-header">
                            <span class="goal-title">${g.name}</span>
                            <span class="badge-pill ${isCompleted ? 'text-emerald' : 'text-indigo'}">
                                ${isCompleted ? '✓ Completed' : `${pct}%`}
                            </span>
                        </div>
                        <div class="goal-progress-wrap">
                            <div class="goal-progress-track">
                                <div class="goal-progress-fill" style="width: ${pct}%;"></div>
                            </div>
                            <div class="goal-meta-row">
                                <span>Saved: <strong>${formatMoney(g.current_amount, sym)}</strong></span>
                                <span>Goal: <strong>${formatMoney(g.target_amount, sym)}</strong></span>
                            </div>
                        </div>
                        <div class="goal-meta-row text-muted">
                            <span><i class="fa-solid fa-tag"></i> ${g.category}</span>
                            ${g.target_date ? `<span><i class="fa-regular fa-calendar"></i> ${formatDate(g.target_date)}</span>` : ''}
                        </div>
                        <div class="budget-card-footer">
                            <button class="btn btn-secondary btn-sm btn-open-contribute" data-id="${g.id}" data-name="${g.name}">
                                <i class="fa-solid fa-plus text-emerald"></i> Contribute
                            </button>
                            <button class="btn-icon btn-delete-goal" data-id="${g.id}" title="Delete Goal">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            container.querySelectorAll('.btn-open-contribute').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.getAttribute('data-id');
                    const name = btn.getAttribute('data-name');
                    document.getElementById('contribute-goal-id').value = id;
                    document.getElementById('contribute-goal-title').textContent = `Target Goal: ${name}`;
                    openModal('modal-contribute');
                });
            });

            container.querySelectorAll('.btn-delete-goal').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.getAttribute('data-id');
                    if (confirm('Delete this savings goal?')) {
                        await fetch(`/api/goals/${id}`, { method: 'DELETE' });
                        await refreshAllData();
                    }
                });
            });

        } catch (err) {
            console.error('Failed to load goals:', err);
        }
    }

    // Add Goal Form Handler
    async function handleAddGoal(e) {
        e.preventDefault();
        const name = document.getElementById('goal-name').value;
        const target = document.getElementById('goal-target').value;
        const current = document.getElementById('goal-current').value || 0;
        const category = document.getElementById('goal-category').value;
        const targetDate = document.getElementById('goal-target-date').value;

        try {
            const res = await fetch('/api/goals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    target_amount: target,
                    current_amount: current,
                    category: category,
                    target_date: targetDate || null
                })
            });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-goal');
                document.getElementById('form-add-goal').reset();
                await refreshAllData();
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Contribute to Goal Handler
    async function handleContributeGoal(e) {
        e.preventDefault();
        const id = document.getElementById('contribute-goal-id').value;
        const amt = document.getElementById('contribute-amount').value;

        try {
            const res = await fetch(`/api/goals/${id}/contribute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amt })
            });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-contribute');
                document.getElementById('form-contribute-goal').reset();
                await refreshAllData();
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Load Monthly Executive Report
    async function loadMonthlyReport() {
        try {
            const res = await fetch('/api/analytics/monthly-report');
            const data = await res.json();
            if (!data || data.error) return;

            const sym = state.currentUser?.currency_symbol || '₹';
            document.getElementById('report-title-display').textContent = data.report_title;
            document.getElementById('report-date-string').textContent = data.generated_at;

            // Report Metrics Boxes
            const boxes = document.getElementById('report-metrics-boxes');
            if (boxes) {
                boxes.innerHTML = `
                    <div class="report-box">
                        <span class="label">Monthly Inflow</span>
                        <span class="value text-emerald">${formatMoney(data.metrics.total_income, sym)}</span>
                    </div>
                    <div class="report-box">
                        <span class="label">Total Outflow</span>
                        <span class="value text-rose">${formatMoney(data.metrics.total_expense, sym)}</span>
                    </div>
                    <div class="report-box">
                        <span class="label">Net Savings</span>
                        <span class="value text-indigo">${formatMoney(data.metrics.net_savings, sym)} (${data.metrics.savings_rate}%)</span>
                    </div>
                    <div class="report-box">
                        <span class="label">Health Score</span>
                        <span class="value text-amber">${data.metrics.health_score}/100</span>
                    </div>
                `;
            }

            // AI Verdict
            document.getElementById('report-ai-verdict-text').textContent = data.ai_verdict;

            // Action Items
            const actionsList = document.getElementById('report-action-items-list');
            if (actionsList && data.action_items) {
                actionsList.innerHTML = data.action_items.map(item => `
                    <li class="action-item"><i class="fa-solid fa-circle-check text-emerald mr-2"></i> ${item}</li>
                `).join('');
            }

            // Variance Audit Table
            const varianceTbody = document.getElementById('report-variance-table-body');
            if (varianceTbody && data.budget_variance) {
                varianceTbody.innerHTML = data.budget_variance.map(v => {
                    const variance = v.allocated - v.spent;
                    const isFavorable = variance >= 0;
                    return `
                        <tr>
                            <td><strong>${v.category}</strong></td>
                            <td>${formatMoney(v.allocated, sym)}</td>
                            <td>${formatMoney(v.spent, sym)}</td>
                            <td class="${isFavorable ? 'text-emerald' : 'text-rose'}">
                                ${isFavorable ? '+' : ''}${formatMoney(variance, sym)}
                            </td>
                            <td>
                                <span class="badge-tag ${isFavorable ? 'badge-income' : 'badge-expense'}">
                                    ${isFavorable ? 'Under Limit' : 'Over Limit'}
                                </span>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

        } catch (err) {
            console.error('Failed to load monthly report:', err);
        }
    }

    // Load AI Chat History
    async function loadChatHistory() {
        try {
            const res = await fetch('/api/advisor/history');
            const messages = await res.json();
            const container = document.getElementById('chat-messages-container');
            if (!container) return;

            container.innerHTML = messages.map(m => renderChatMessageBubble(m)).join('');
            scrollChatToBottom();
        } catch (err) {
            console.error('Failed to load chat history:', err);
        }
    }

    // Render Chat Message Bubble with Markdown Parsing
    function renderChatMessageBubble(msg) {
        const isBot = msg.role === 'assistant';
        let formattedContent = msg.content
            .replace(/### (.*?)\n/g, '<h4>$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/- (.*?)\n/g, '<li>$1</li>');

        // Wrap list items
        if (formattedContent.includes('<li>')) {
            formattedContent = formattedContent.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        }

        return `
            <div class="chat-bubble-wrap ${isBot ? 'bot' : 'user'}">
                <div class="chat-bubble ${isBot ? 'bot' : 'user'}">
                    ${formattedContent}
                </div>
            </div>
        `;
    }

    function scrollChatToBottom() {
        const container = document.getElementById('chat-messages-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    // Send AI Chat Message
    async function handleSendMessage() {
        const input = document.getElementById('chat-user-input');
        const text = (input.value || '').trim();
        if (!text) return;

        input.value = '';
        const container = document.getElementById('chat-messages-container');
        const typing = document.getElementById('chat-typing-indicator');

        // Append user bubble immediately
        container.insertAdjacentHTML('beforeend', renderChatMessageBubble({ role: 'user', content: text }));
        scrollChatToBottom();

        // Show typing indicator
        if (typing) typing.style.display = 'flex';

        try {
            const res = await fetch('/api/advisor/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();

            if (typing) typing.style.display = 'none';

            if (data.bot_message) {
                container.insertAdjacentHTML('beforeend', renderChatMessageBubble(data.bot_message));
                scrollChatToBottom();
            }
        } catch (err) {
            if (typing) typing.style.display = 'none';
            console.error('Chat error:', err);
        }
    }

    // Clear Chat History
    async function handleClearChat() {
        if (confirm('Clear conversational history with Beacon?')) {
            try {
                await fetch('/api/advisor/clear', { method: 'POST' });
                document.getElementById('chat-messages-container').innerHTML = '';
            } catch (err) {
                console.error(err);
            }
        }
    }

    // Save Gemini Settings
    async function handleSaveSettings(e) {
        e.preventDefault();
        const key = document.getElementById('settings-gemini-key').value;
        try {
            const res = await fetch('/api/settings/api-key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key })
            });
            const data = await res.json();
            if (data.success) {
                closeModal('modal-settings');
                await loadSettingsStatus();
                alert('Gemini settings saved successfully!');
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Start App
    init();
});
