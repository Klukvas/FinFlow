import React from 'react';
import { useTranslation } from 'react-i18next';
import { PromptCard } from './PromptCard';
import { PromptBlockConfig } from './promptConfig';

interface PromptBlockProps {
  block: PromptBlockConfig;
  activePromptId: string | null;
  loadingPromptId: string | null;
  onPromptClick: (promptId: string) => void;
}

export const PromptBlock: React.FC<PromptBlockProps> = ({
  block,
  activePromptId,
  loadingPromptId,
  onPromptClick,
}) => {
  const { t } = useTranslation();

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold theme-text-primary mb-4">
        {t(block.titleKey)}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {block.prompts.map((prompt) => (
          <PromptCard
            key={prompt.id}
            titleKey={prompt.titleKey}
            descriptionKey={prompt.descriptionKey}
            icon={prompt.icon}
            isLoading={loadingPromptId === prompt.id}
            isActive={activePromptId === prompt.id}
            onClick={() => onPromptClick(prompt.id)}
          />
        ))}
      </div>
    </div>
  );
};
