import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/shared/Button";
import { Plus } from "lucide-react";

interface GoalsHeaderProps {
  onShowCreateModal: () => void;
}

export const GoalsHeader = React.memo<GoalsHeaderProps>(
  ({ onShowCreateModal }) => {
    const { t } = useTranslation();
    return (
      <div className="flex justify-end mb-4 sm:mb-6">
        <Button
          onClick={onShowCreateModal}
          className="flex items-center justify-center gap-2 py-3 sm:py-2 min-h-[44px] touch-manipulation"
          data-testid="goals-create-button"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden xs:inline">
            {t("goalsPage.createButton")}
          </span>
          <span className="xs:hidden">{t("goalsPage.createButtonShort")}</span>
        </Button>
      </div>
    );
  },
);

GoalsHeader.displayName = "GoalsHeader";
