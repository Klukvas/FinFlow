import React from "react";
import { IconType } from "react-icons";
import { SectionHeader } from "./SectionHeader";
import { FeatureItem } from "./FeatureItem";

interface FeatureGroupItem {
  icon: IconType;
  title: string;
  description: string;
}

interface FeatureGroupProps {
  label?: string;
  title: string;
  description?: string;
  items: FeatureGroupItem[];
  columns?: 2 | 3 | 4;
}

export const FeatureGroup: React.FC<FeatureGroupProps> = ({
  label,
  title,
  description,
  items,
  columns = 2,
}) => {
  const gridCols = {
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <section>
      <SectionHeader
        title={title}
        {...(label !== undefined ? { label } : {})}
        {...(description !== undefined ? { description } : {})}
      />
      <div className={`grid ${gridCols[columns]} gap-4`}>
        {items.map((item, index) => (
          <FeatureItem
            key={index}
            icon={item.icon}
            title={item.title}
            description={item.description}
          />
        ))}
      </div>
    </section>
  );
};
