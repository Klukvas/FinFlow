export const MESSAGES = {
  // Success messages
  SUCCESS: {
    CATEGORY_CREATED: 'Категория успешно создана',
    CATEGORY_UPDATED: 'Категория успешно обновлена',
    CATEGORY_DELETED: 'Категория успешно удалена',
    GOAL_CREATED: 'Цель успешно создана',
    GOAL_UPDATED: 'Цель успешно обновлена',
    GOAL_DELETED: 'Цель успешно удалена',
    EXPENSE_CREATED: 'Расход успешно создан',
    EXPENSE_UPDATED: 'Расход успешно обновлен',
    EXPENSE_DELETED: 'Расход успешно удален',
    INCOME_CREATED: 'Доход успешно создан',
    INCOME_UPDATED: 'Доход успешно обновлен',
    INCOME_DELETED: 'Доход успешно удален',
    LOGIN_SUCCESS: 'Вход выполнен успешно',
    REGISTRATION_SUCCESS: 'Регистрация выполнена успешно',
    LOGOUT_SUCCESS: 'Выход выполнен успешно',
    PROFILE_UPDATED: 'Профиль успешно обновлен',
  },
  
  // Error messages
  ERROR: {
    CATEGORY_CREATE_FAILED: 'Ошибка при создании категории',
    CATEGORY_UPDATE_FAILED: 'Ошибка при обновлении категории',
    CATEGORY_DELETE_FAILED: 'Ошибка при удалении категории',
    CATEGORY_LOAD_FAILED: 'Ошибка при загрузке категорий',
    GOAL_CREATE_FAILED: 'Ошибка при создании цели',
    GOAL_UPDATE_FAILED: 'Ошибка при обновлении цели',
    GOAL_DELETE_FAILED: 'Ошибка при удалении цели',
    GOAL_LOAD_FAILED: 'Ошибка при загрузке целей',
    EXPENSE_CREATE_FAILED: 'Ошибка при создании расхода',
    EXPENSE_UPDATE_FAILED: 'Ошибка при обновлении расхода',
    EXPENSE_DELETE_FAILED: 'Ошибка при удалении расхода',
    EXPENSE_LOAD_FAILED: 'Ошибка при загрузке расходов',
    INCOME_CREATE_FAILED: 'Ошибка при создании дохода',
    INCOME_UPDATE_FAILED: 'Ошибка при обновлении дохода',
    INCOME_DELETE_FAILED: 'Ошибка при удалении дохода',
    INCOME_LOAD_FAILED: 'Ошибка при загрузке доходов',
    LOGIN_FAILED: 'Ошибка при входе в систему',
    REGISTRATION_FAILED: 'Ошибка при регистрации',
    LOGOUT_FAILED: 'Ошибка при выходе из системы',
    PROFILE_UPDATE_FAILED: 'Ошибка при обновлении профиля',
    NETWORK_ERROR: 'Ошибка сети. Проверьте подключение к интернету',
    UNAUTHORIZED: 'Недостаточно прав для выполнения операции',
    FORBIDDEN: 'Доступ запрещен',
    NOT_FOUND: 'Ресурс не найден',
    SERVER_ERROR: 'Внутренняя ошибка сервера',
    VALIDATION_ERROR: 'Ошибка валидации данных',
    UNKNOWN_ERROR: 'Произошла неизвестная ошибка',
  },
  
  // Loading messages
  LOADING: {
    CATEGORIES: 'Загрузка категорий...',
    GOALS: 'Загрузка целей...',
    EXPENSES: 'Загрузка расходов...',
    INCOME: 'Загрузка доходов...',
    PROFILE: 'Загрузка профиля...',
    GENERAL: 'Загрузка...',
  },
  
  // Empty state messages
  EMPTY: {
    NO_CATEGORIES: 'Нет категорий',
    NO_GOALS: 'Нет целей',
    NO_EXPENSES: 'Нет расходов',
    NO_INCOME: 'Нет доходов',
    NO_DATA: 'Нет данных',
  },
  
  // Placeholder messages
  PLACEHOLDER: {
    SEARCH: 'Поиск...',
    SELECT_OPTION: 'Выберите опцию',
    ENTER_VALUE: 'Введите значение',
  },
} as const;
