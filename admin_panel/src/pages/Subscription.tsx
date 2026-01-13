import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { SubscriptionService } from '@/services/subscriptionService';
import { Plan, Feature, PlanFeature } from '@/types';
import { 
  FaPlus, 
  FaEdit, 
  FaTimes,
  FaCheck,
  FaBan,
  FaToggleOn,
  FaToggleOff
} from 'react-icons/fa';

export const Subscription: React.FC = () => {
  const { token, logout } = useAuth();
  const queryClient = useQueryClient();
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [editingFeatures, setEditingFeatures] = useState<Plan | null>(null);

  const subscriptionService = React.useMemo(
    () => new SubscriptionService(() => token, logout),
    [token, logout]
  );

  // Fetch plans
  const { data: plansData, isLoading: plansLoading } = useQuery({
    queryKey: ['admin-plans'],
    queryFn: async () => {
      const result = await subscriptionService.listPlans();
      if ('error' in result) throw new Error(result.error);
      return result;
    },
  });

  // Fetch features
  const { data: featuresData } = useQuery({
    queryKey: ['admin-features'],
    queryFn: async () => {
      const result = await subscriptionService.listFeatures();
      if ('error' in result) throw new Error(result.error);
      return result;
    },
  });

  // Create plan mutation
  const createPlanMutation = useMutation({
    mutationFn: async (data: { code: string; name: string; period_days: number }) => {
      const result = await subscriptionService.createPlan(data);
      if ('error' in result) throw new Error(result.error);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-plans'] });
      setShowCreateModal(false);
    },
  });

  // Update plan mutation
  const updatePlanMutation = useMutation({
    mutationFn: async ({ planId, data }: { planId: number; data: { name?: string; period_days?: number; is_active?: boolean } }) => {
      const result = await subscriptionService.updatePlan(planId, data);
      if ('error' in result) throw new Error(result.error);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-plans'] });
      setEditingPlan(null);
    },
  });

  // Update features mutation
  const updateFeaturesMutation = useMutation({
    mutationFn: async ({ planId, features }: { planId: number; features: PlanFeature[] }) => {
      const result = await subscriptionService.updatePlanFeatures(planId, features);
      if ('error' in result) throw new Error(result.error);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-plans'] });
      setEditingFeatures(null);
    },
  });

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Subscription Plans</h1>
          <p className="text-slate-400">Manage subscription plans and features</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-white font-medium rounded-xl transition-colors"
        >
          <FaPlus className="w-4 h-4" />
          Create Plan
        </button>
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
                plan.is_active ? 'border-slate-700' : 'border-red-500/30'
              } overflow-hidden`}
            >
              {/* Plan header */}
              <div className="p-6 border-b border-slate-700">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                    <p className="text-sm text-slate-400 font-mono">{plan.code}</p>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    plan.is_active
                      ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                      : 'bg-red-500/10 text-red-400 border border-red-500/20'
                  }`}>
                    {plan.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white">{plan.period_days}</span>
                  <span className="text-slate-400">days</span>
                </div>
              </div>

              {/* Features */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-slate-300">Features</h4>
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
                        <span className="text-sm text-slate-300">{feature.feature_code}</span>
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
                  <p className="text-sm text-slate-500 italic">No features configured</p>
                )}
              </div>

              {/* Actions */}
              <div className="px-6 pb-6">
                <button
                  onClick={() => setEditingPlan(plan)}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-colors"
                >
                  <FaEdit className="w-4 h-4" />
                  Edit Plan
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Plan Modal */}
      {showCreateModal && (
        <CreatePlanModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={(data) => createPlanMutation.mutate(data)}
          isLoading={createPlanMutation.isPending}
          error={createPlanMutation.error?.message}
        />
      )}

      {/* Edit Plan Modal */}
      {editingPlan && (
        <EditPlanModal
          plan={editingPlan}
          onClose={() => setEditingPlan(null)}
          onSubmit={(data) => updatePlanMutation.mutate({ planId: editingPlan.id, data })}
          isLoading={updatePlanMutation.isPending}
          error={updatePlanMutation.error?.message}
        />
      )}

      {/* Edit Features Modal */}
      {editingFeatures && featuresData && (
        <EditFeaturesModal
          plan={editingFeatures}
          allFeatures={featuresData.items}
          onClose={() => setEditingFeatures(null)}
          onSubmit={(features) => updateFeaturesMutation.mutate({ planId: editingFeatures.id, features })}
          isLoading={updateFeaturesMutation.isPending}
          error={updateFeaturesMutation.error?.message}
        />
      )}
    </div>
  );
};

// Create Plan Modal Component
interface CreatePlanModalProps {
  onClose: () => void;
  onSubmit: (data: { code: string; name: string; period_days: number }) => void;
  isLoading: boolean;
  error?: string;
}

const CreatePlanModal: React.FC<CreatePlanModalProps> = ({ onClose, onSubmit, isLoading, error }) => {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [periodDays, setPeriodDays] = useState(30);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ code, name, period_days: periodDays });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl border border-slate-700 w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">Create Plan</h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg">
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Code</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
              placeholder="e.g. premium"
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Premium Plan"
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Period (days)</label>
            <input
              type="number"
              value={periodDays}
              onChange={(e) => setPeriodDays(parseInt(e.target.value) || 30)}
              min={1}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-cyan-500 hover:bg-cyan-400 text-white font-medium rounded-xl disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Creating...' : 'Create Plan'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Edit Plan Modal Component
interface EditPlanModalProps {
  plan: Plan;
  onClose: () => void;
  onSubmit: (data: { name?: string; period_days?: number; is_active?: boolean }) => void;
  isLoading: boolean;
  error?: string;
}

const EditPlanModal: React.FC<EditPlanModalProps> = ({ plan, onClose, onSubmit, isLoading, error }) => {
  const [name, setName] = useState(plan.name);
  const [periodDays, setPeriodDays] = useState(plan.period_days);
  const [isActive, setIsActive] = useState(plan.is_active);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, period_days: periodDays, is_active: isActive });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl border border-slate-700 w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">Edit Plan</h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg">
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Code</label>
            <input
              type="text"
              value={plan.code}
              disabled
              className="w-full px-4 py-3 bg-slate-900/30 border border-slate-700 rounded-xl text-slate-500 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Period (days)</label>
            <input
              type="number"
              value={periodDays}
              onChange={(e) => setPeriodDays(parseInt(e.target.value) || 30)}
              min={1}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Status</label>
            <button
              type="button"
              onClick={() => setIsActive(!isActive)}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border transition-all ${
                isActive
                  ? 'bg-green-500/10 border-green-500/30 text-green-400'
                  : 'bg-red-500/10 border-red-500/30 text-red-400'
              }`}
            >
              <span>{isActive ? 'Active' : 'Inactive'}</span>
              {isActive ? <FaToggleOn className="w-6 h-6" /> : <FaToggleOff className="w-6 h-6" />}
            </button>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-cyan-500 hover:bg-cyan-400 text-white font-medium rounded-xl disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Edit Features Modal Component
interface EditFeaturesModalProps {
  plan: Plan;
  allFeatures: Feature[];
  onClose: () => void;
  onSubmit: (features: PlanFeature[]) => void;
  isLoading: boolean;
  error?: string;
}

const EditFeaturesModal: React.FC<EditFeaturesModalProps> = ({ 
  plan, 
  allFeatures, 
  onClose, 
  onSubmit, 
  isLoading, 
  error 
}) => {
  const [features, setFeatures] = useState<Map<string, { enabled: boolean; limit_value: number | null }>>(
    () => {
      const map = new Map();
      // Initialize with existing features
      plan.features.forEach(f => {
        map.set(f.feature_code, { enabled: f.enabled, limit_value: f.limit_value });
      });
      return map;
    }
  );

  const toggleFeature = (code: string) => {
    const current = features.get(code);
    if (current) {
      setFeatures(new Map(features.set(code, { ...current, enabled: !current.enabled })));
    } else {
      setFeatures(new Map(features.set(code, { enabled: true, limit_value: null })));
    }
  };

  const updateLimit = (code: string, value: string) => {
    const current = features.get(code) || { enabled: true, limit_value: null };
    const limitValue = value === '' ? null : parseInt(value);
    setFeatures(new Map(features.set(code, { ...current, limit_value: limitValue })));
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
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg">
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
                      ? 'bg-cyan-500/5 border-cyan-500/20'
                      : 'bg-slate-900/30 border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-white">{feature.name}</p>
                      <p className="text-xs text-slate-400 font-mono">{feature.code}</p>
                      {feature.description && (
                        <p className="text-sm text-slate-400 mt-1">{feature.description}</p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleFeature(feature.code)}
                      className={`p-1 transition-colors ${
                        isEnabled ? 'text-cyan-400' : 'text-slate-500'
                      }`}
                    >
                      {isEnabled ? <FaToggleOn className="w-8 h-8" /> : <FaToggleOff className="w-8 h-8" />}
                    </button>
                  </div>
                  
                  {isEnabled && (
                    <div className="mt-3">
                      <label className="block text-xs text-slate-400 mb-1">Limit (optional)</label>
                      <input
                        type="number"
                        value={current?.limit_value ?? ''}
                        onChange={(e) => updateLimit(feature.code, e.target.value)}
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
            <p className="text-center text-slate-500 py-8">No features available</p>
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
            {isLoading ? 'Saving...' : 'Save Features'}
          </button>
        </div>
      </div>
    </div>
  );
};
