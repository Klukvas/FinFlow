import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { SubscriptionService } from "@/services/subscriptionService";
import { Plan, PlanFeature } from "@/types";
import { FaCheck, FaBan } from "react-icons/fa";
import { EditFeaturesModal } from "@/components/EditFeaturesModal";

export const Subscription: React.FC = () => {
  const { token, logout, refreshToken } = useAuth();
  const queryClient = useQueryClient();

  const [editingFeatures, setEditingFeatures] = useState<Plan | null>(null);

  const subscriptionService = React.useMemo(
    () => new SubscriptionService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  // Fetch plans
  const { data: plansData, isLoading: plansLoading } = useQuery({
    queryKey: ["admin-plans"],
    queryFn: async () => {
      const result = await subscriptionService.listPlans();
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  // Fetch features
  const { data: featuresData } = useQuery({
    queryKey: ["admin-features"],
    queryFn: async () => {
      const result = await subscriptionService.listFeatures();
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  // Update features mutation
  const updateFeaturesMutation = useMutation({
    mutationFn: async ({
      planId,
      features,
    }: {
      planId: number;
      features: PlanFeature[];
    }) => {
      const result = await subscriptionService.updatePlanFeatures(
        planId,
        features,
      );
      if ("error" in result) throw new Error(result.error);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-plans"] });
      setEditingFeatures(null);
    },
  });

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">
          Subscription Plans
        </h1>
        <p className="text-slate-400">
          Manage plan features and limits. Plans and pricing are managed via
          Paddle.
        </p>
      </div>

      {/* Plans grid */}
      {plansLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plansData?.items.map((plan) => (
            <div
              key={plan.id}
              className={`bg-slate-800 rounded-xl border ${
                plan.is_active ? "border-slate-700" : "border-red-500/30"
              } overflow-hidden`}
            >
              {/* Plan header */}
              <div className="p-6 border-b border-slate-700">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      {plan.name}
                    </h3>
                    <p className="text-sm text-slate-400 font-mono">
                      {plan.code}
                    </p>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      plan.is_active
                        ? "bg-green-500/10 text-green-400 border border-green-500/20"
                        : "bg-red-500/10 text-red-400 border border-red-500/20"
                    }`}
                  >
                    {plan.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white">
                    {plan.period_days}
                  </span>
                  <span className="text-slate-400">days</span>
                </div>
              </div>

              {/* Features */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-slate-300">
                    Features
                  </h4>
                  <button
                    onClick={() => setEditingFeatures(plan)}
                    className="text-xs text-cyan-400 hover:text-cyan-300"
                  >
                    Edit
                  </button>
                </div>

                {plan.features.length > 0 ? (
                  <div className="space-y-2">
                    {plan.features.map((feature) => (
                      <div
                        key={feature.feature_code}
                        className="flex items-center justify-between py-2 px-3 bg-slate-900/50 rounded-lg"
                      >
                        <span className="text-sm text-slate-300">
                          {feature.feature_code}
                        </span>
                        <div className="flex items-center gap-2">
                          {feature.limit_value !== null && (
                            <span className="text-xs text-slate-400">
                              Limit: {feature.limit_value}
                            </span>
                          )}
                          {feature.enabled ? (
                            <FaCheck className="w-3 h-3 text-green-400" />
                          ) : (
                            <FaBan className="w-3 h-3 text-red-400" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 italic">
                    No features configured
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Features Modal */}
      {editingFeatures && featuresData && (
        <EditFeaturesModal
          plan={editingFeatures}
          allFeatures={featuresData.items}
          onClose={() => setEditingFeatures(null)}
          onSubmit={(features) =>
            updateFeaturesMutation.mutate({
              planId: editingFeatures.id,
              features,
            })
          }
          isLoading={updateFeaturesMutation.isPending}
          error={updateFeaturesMutation.error?.message}
        />
      )}
    </div>
  );
};
