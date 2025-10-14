import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { CategoryList, CreateCategory, EditCategory, CategoryStatistics } from '../components';
import { Modal } from '../components/ui/shared/Modal';
import { Button } from '../components/ui/shared/Button';
import { FaPlus } from 'react-icons/fa';
import type { Category as CategoryType } from '@/types';

export const Category = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [refreshKey, setRefreshKey] = useState(0);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<CategoryType | null>(null);

  const handleCategoryCreated = () => {
    setRefreshKey(prev => prev + 1);
    setIsCreateModalOpen(false);
  };

  const handleCategoryUpdated = () => {
    setRefreshKey(prev => prev + 1);
    setIsEditModalOpen(false);
    setEditingCategory(null);
  };

  const handleEditCategory = (category: CategoryType) => {
    setEditingCategory(category);
    setIsEditModalOpen(true);
  };

  const handleCancelEdit = () => {
    setIsEditModalOpen(false);
    setEditingCategory(null);
  };

  const handleCategoryClick = (category: CategoryType) => {
    // Переходим на страницу деталей категории
    navigate(`/category/${category.id}`);
  };

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6 lg:space-y-8">
        {/* Page Header */}
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 rounded-xl sm:rounded-2xl blur-3xl"></div>
          <div className="relative theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border p-4 sm:p-6 lg:p-8 theme-shadow">
            <div className="flex flex-col gap-4 sm:gap-6">
              <div className="space-y-2 sm:space-y-3">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg sm:rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-4 h-4 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <h1 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold theme-text-primary leading-tight">
                    {t('categoryPage.title')}
                  </h1>
                </div>
                <p className="theme-text-secondary text-xs sm:text-sm md:text-base max-w-2xl leading-relaxed">
                  {t('categoryPage.subtitle')}
                </p>
              </div>
              
              <div className="flex-shrink-0">
                <Button
                  data-testid='create-category-button'
                  onClick={() => setIsCreateModalOpen(true)}
                  className="group relative bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold px-4 sm:px-6 py-3 sm:py-3 rounded-lg sm:rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 flex items-center gap-2 sm:gap-3 w-full sm:w-auto justify-center min-h-[44px] sm:min-h-[48px] text-sm sm:text-base"
                >
                  <div className="w-4 h-4 sm:w-5 sm:h-5 group-hover:rotate-90 transition-transform duration-200">
                    <FaPlus className="w-full h-full" />
                  </div>
                  <span>{t('categoryPage.createButton')}</span>
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <CategoryStatistics refreshTrigger={refreshKey} />

        {/* Categories List */}
        <div className="theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border theme-shadow overflow-hidden">
          <CategoryList key={refreshKey} onEditCategory={handleEditCategory} onCategoryClick={handleCategoryClick} />
        </div>

        {/* Create Category Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={t('categoryPage.createModalTitle')}
          size="md"
          data-testid='category-modal'
        >
          <CreateCategory onCategoryCreated={handleCategoryCreated} />
        </Modal>

        {/* Edit Category Modal */}
        {editingCategory && (
          <Modal
            isOpen={isEditModalOpen}
            onClose={handleCancelEdit}
            title={t('categoryPage.editModalTitle')}
            size="md"
            data-testid='category-modal'
          >
            <EditCategory
              category={editingCategory}
              onCategoryUpdated={handleCategoryUpdated}
              onCancel={handleCancelEdit}
            />
          </Modal>
        )}
      </div>
    </div>
  );
};

