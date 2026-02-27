from app.schemas.prompts import PromptId


SYSTEM_PROMPT = """You are a professional financial advisor AI assistant for FinFlow personal finance application.
You analyze user's financial data and provide actionable, specific advice.

Rules:
1. Base ALL advice on the actual financial data provided — never invent numbers.
2. Be specific: reference actual categories, amounts, and dates from the data.
3. Be concise and practical. Provide 2-4 sections in your response.
4. Respond in {language}.
5. Format your response as a JSON array of sections:
[
  {{"title": "Section title", "content": "Markdown content with **bold**, lists, etc.", "priority": "high|medium|low"}}
]
6. Use markdown formatting in content: **bold** for key numbers, bullet lists for recommendations.
7. Do NOT include any text outside the JSON array. Return ONLY valid JSON."""


PROMPT_TEMPLATES: dict[PromptId, dict[str, str]] = {
    PromptId.EXPENSES_REDUCE_SPENDING: {
        "ru": """Проанализируй расходы пользователя и определи, где можно тратить меньше.

Финансовые данные:
{data}

Дай конкретные рекомендации по снижению расходов с указанием категорий и сумм.""",
        "en": """Analyze user expenses and identify where they can spend less.

Financial data:
{data}

Provide specific recommendations for reducing spending with categories and amounts.""",
        "uk": """Проаналізуй витрати користувача та визнач, де можна витрачати менше.

Фінансові дані:
{data}

Дай конкретні рекомендації щодо зниження витрат із зазначенням категорій та сум.""",
    },
    PromptId.EXPENSES_SAVE_MORE: {
        "ru": """Проанализируй доходы и расходы пользователя. Найди возможности для экономии.

Финансовые данные:
{data}

Предложи конкретные способы сэкономить, основываясь на реальных данных.""",
        "en": """Analyze user income and expenses. Find savings opportunities.

Financial data:
{data}

Suggest specific ways to save based on actual data.""",
        "uk": """Проаналізуй доходи та витрати користувача. Знайди можливості для економії.

Фінансові дані:
{data}

Запропонуй конкретні способи зекономити, спираючись на реальні дані.""",
    },
    PromptId.EXPENSES_ANOMALIES: {
        "ru": """Проанализируй расходы пользователя и найди аномалии: необычные траты, резкие скачки, подозрительные паттерны.

Финансовые данные:
{data}

Укажи конкретные аномалии с датами, суммами и категориями.""",
        "en": """Analyze user expenses and find anomalies: unusual spending, sharp spikes, suspicious patterns.

Financial data:
{data}

Point out specific anomalies with dates, amounts, and categories.""",
        "uk": """Проаналізуй витрати користувача та знайди аномалії: незвичайні витрати, різкі стрибки, підозрілі патерни.

Фінансові дані:
{data}

Вкажи конкретні аномалії з датами, сумами та категоріями.""",
    },
    PromptId.GOALS_REALISTIC: {
        "ru": """Оцени реалистичность финансовых целей пользователя на основе его доходов и расходов.

Финансовые данные:
{data}

Для каждой цели определи, реалистична ли она, и если нет — что нужно изменить.""",
        "en": """Evaluate whether user's financial goals are realistic based on their income and expenses.

Financial data:
{data}

For each goal, determine if it's realistic, and if not — what needs to change.""",
        "uk": """Оціни реалістичність фінансових цілей користувача на основі його доходів та витрат.

Фінансові дані:
{data}

Для кожної цілі визнач, чи реалістична вона, і якщо ні — що потрібно змінити.""",
    },
    PromptId.GOALS_FASTER: {
        "ru": """Предложи способы быстрее достичь финансовых целей пользователя.

Финансовые данные:
{data}

Дай конкретные рекомендации для ускорения достижения каждой цели.""",
        "en": """Suggest ways to reach financial goals faster.

Financial data:
{data}

Provide specific recommendations to accelerate achieving each goal.""",
        "uk": """Запропонуй способи швидше досягти фінансових цілей користувача.

Фінансові дані:
{data}

Дай конкретні рекомендації для прискорення досягнення кожної цілі.""",
    },
    PromptId.GOALS_PRIORITIZE: {
        "ru": """Помоги расставить приоритеты среди финансовых целей пользователя, учитывая долги.

Финансовые данные:
{data}

Предложи оптимальный порядок приоритетов с обоснованием.""",
        "en": """Help prioritize user's financial goals considering debts.

Financial data:
{data}

Suggest optimal priority order with reasoning.""",
        "uk": """Допоможи розставити пріоритети серед фінансових цілей користувача, враховуючи борги.

Фінансові дані:
{data}

Запропонуй оптимальний порядок пріоритетів з обґрунтуванням.""",
    },
    PromptId.DEBTS_PAY_FIRST: {
        "ru": """Проанализируй долги пользователя и определи, какие нужно гасить в первую очередь.

Финансовые данные:
{data}

Используй методы snowball/avalanche и укажи оптимальный порядок погашения.""",
        "en": """Analyze user debts and determine which should be paid off first.

Financial data:
{data}

Use snowball/avalanche methods and indicate optimal repayment order.""",
        "uk": """Проаналізуй борги користувача та визнач, які потрібно гасити в першу чергу.

Фінансові дані:
{data}

Використай методи snowball/avalanche та вкажи оптимальний порядок погашення.""",
    },
    PromptId.DEBTS_RISK_ASSESSMENT: {
        "ru": """Оцени риски долговой нагрузки пользователя.

Финансовые данные:
{data}

Рассчитай debt-to-income ratio, оцени общий уровень риска и дай рекомендации.""",
        "en": """Assess the risk of user's debt burden.

Financial data:
{data}

Calculate debt-to-income ratio, assess overall risk level, and provide recommendations.""",
        "uk": """Оціни ризики боргового навантаження користувача.

Фінансові дані:
{data}

Розрахуй debt-to-income ratio, оціни загальний рівень ризику та дай рекомендації.""",
    },
    PromptId.DEBTS_REPAYMENT_STRATEGY: {
        "ru": """Разработай стратегию погашения долгов с учётом целей пользователя.

Финансовые данные:
{data}

Предложи пошаговый план погашения с конкретными суммами и сроками.""",
        "en": """Develop a debt repayment strategy considering user's goals.

Financial data:
{data}

Propose a step-by-step repayment plan with specific amounts and timelines.""",
        "uk": """Розроби стратегію погашення боргів з урахуванням цілей користувача.

Фінансові дані:
{data}

Запропонуй покроковий план погашення з конкретними сумами та термінами.""",
    },
}
