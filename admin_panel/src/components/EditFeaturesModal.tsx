import React, { useState } from "react";
import { Plan, Feature, PlanFeature } from "@/types";
import { FaTimes, FaToggleOn, FaToggleOff } from "react-icons/fa";

interface EditFeaturesModalProps {
  plan: Plan;
  allFeatures: Feature[];
  onClose: () => void;
  onSubmit: (features: PlanFeature[]) => void;
  isLoading: boolean;
  error?: string;
}

export const EditFeaturesModal: React.FC<EditFeaturesModalProps> = ({
  plan,
  allFeatures,
  onClose,
  onSubmit,
  isLoading,
  error,
}) => {
  const [features, setFeatures] = useState<
    Map<string, { enabled: boolean; limit_value: number | null }>
  >(() => {
    const map = new Map();
    plan.features.forEach((f) => {
      map.set(f.feature_code, {
        enabled: f.enabled,
        limit_value: f.limit_value,
      });
    });
    return map;
  });

  const toggleFeature = (code: string) => {
    const next = new Map(features);
    const current = next.get(code);
    if (current) {
      next.set(code, { ...current, enabled: !current.enabled });
    } else {
      next.set(code, { enabled: true, limit_value: null });
    }
    setFeatures(next);
  };

  const updateLimit = (code: string, value: string) => {
    const next = new Map(features);
    const current = next.get(code) || { enabled: true, limit_value: null };
    const limitValue = value === "" ? null : parseInt(value);
    next.set(code, { ...current, limit_value: limitValue });
    setFeatures(next);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const featuresList: PlanFeature[] = [];
    features.forEach((value, key) => {
      featuresList.push({
        feature_code: key,
        enabled: value.enabled,
        limit_value: value.limit_value,
      });
    });
    onSubmit(featuresList);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl border border-slate-700 w-full max-w-lg max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div>
            <h2 className="text-lg font-semibold text-white">Edit Features</h2>
            <p className="text-sm text-slate-400">{plan.name}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-auto p-6">
          <div className="space-y-3">
            {allFeatures.map((feature) => {
              const current = features.get(feature.code);
              const isEnabled = current?.enabled ?? false;

              return (
                <div
                  key={feature.code}
                  className={`p-4 rounded-xl border transition-all ${
                    isEnabled
                      ? "bg-cyan-500/5 border-cyan-500/20"
                      : "bg-slate-900/30 border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-white">{feature.name}</p>
                      <p className="text-xs text-slate-400 font-mono">
                        {feature.code}
                      </p>
                      {feature.description && (
                        <p className="text-sm text-slate-400 mt-1">
                          {feature.description}
                        </p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleFeature(feature.code)}
                      className={`p-1 transition-colors ${
                        isEnabled ? "text-cyan-400" : "text-slate-500"
                      }`}
                    >
                      {isEnabled ? (
                        <FaToggleOn className="w-8 h-8" />
                      ) : (
                        <FaToggleOff className="w-8 h-8" />
                      )}
                    </button>
                  </div>

                  {isEnabled && (
                    <div className="mt-3">
                      <label className="block text-xs text-slate-400 mb-1">
                        Limit (optional)
                      </label>
                      <input
                        type="number"
                        value={current?.limit_value ?? ""}
                        onChange={(e) =>
                          updateLimit(feature.code, e.target.value)
                        }
                        placeholder="No limit"
                        className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {allFeatures.length === 0 && (
            <p className="text-center text-slate-500 py-8">
              No features available
            </p>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
              {error}
            </div>
          )}
        </form>

        <div className="p-6 border-t border-slate-700">
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={isLoading}
            className="w-full py-3 bg-cyan-500 hover:bg-cyan-400 text-white font-medium rounded-xl disabled:opacity-50 transition-colors"
          >
            {isLoading ? "Saving..." : "Save Features"}
          </button>
        </div>
      </div>
    </div>
  );
};
