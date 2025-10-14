import React from 'react';
import { Skeleton } from '../shared/Skeleton';

export const ProfileSkeleton = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" data-testid="profile-skeleton-title" />
          <Skeleton className="h-4 w-96" data-testid="profile-skeleton-subtitle" />
        </div>
        <Skeleton className="h-10 w-48" data-testid="profile-skeleton-button" />
      </div>

      {/* Profile Information */}
      <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
        <div className="flex items-start space-x-6">
          {/* Avatar */}
          <div className="flex-shrink-0">
            <Skeleton 
              variant="circular" 
              width={96} 
              height={96} 
              data-testid="profile-skeleton-avatar" 
            />
          </div>

          {/* User Info */}
          <div className="flex-1 space-y-4">
            <div className="space-y-2">
              <Skeleton className="h-7 w-48" data-testid="profile-skeleton-username" />
              <Skeleton className="h-5 w-64" data-testid="profile-skeleton-email" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                {/* Username Field */}
                <div className="flex items-center space-x-3">
                  <Skeleton 
                    variant="circular" 
                    width={20} 
                    height={20} 
                    data-testid="profile-skeleton-username-icon" 
                  />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-32" data-testid="profile-skeleton-username-label" />
                    <Skeleton className="h-5 w-40" data-testid="profile-skeleton-username-value" />
                  </div>
                </div>

                {/* Currency Field */}
                <div className="flex items-center space-x-3">
                  <Skeleton 
                    variant="circular" 
                    width={20} 
                    height={20} 
                    data-testid="profile-skeleton-currency-icon" 
                  />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-32" data-testid="profile-skeleton-currency-label" />
                    <Skeleton className="h-5 w-24" data-testid="profile-skeleton-currency-value" />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {/* Email Field */}
                <div className="flex items-center space-x-3">
                  <Skeleton 
                    variant="circular" 
                    width={20} 
                    height={20} 
                    data-testid="profile-skeleton-email-icon" 
                  />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-24" data-testid="profile-skeleton-email-label" />
                    <Skeleton className="h-5 w-48" data-testid="profile-skeleton-email-value" />
                  </div>
                </div>

                {/* ID Field */}
                <div className="flex items-center space-x-3">
                  <Skeleton 
                    variant="circular" 
                    width={20} 
                    height={20} 
                    data-testid="profile-skeleton-id-icon" 
                  />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-36" data-testid="profile-skeleton-id-label" />
                    <Skeleton className="h-5 w-20" data-testid="profile-skeleton-id-value" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Account Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((index) => (
          <div 
            key={index} 
            className="theme-surface rounded-lg theme-shadow theme-border border p-6"
            data-testid={`profile-skeleton-stat-card-${index}`}
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Skeleton 
                  variant="circular" 
                  width={32} 
                  height={32} 
                  data-testid={`profile-skeleton-stat-icon-${index}`}
                />
              </div>
              <div className="ml-4 space-y-2 flex-1">
                <Skeleton className="h-4 w-32" data-testid={`profile-skeleton-stat-label-${index}`} />
                <Skeleton className="h-6 w-24" data-testid={`profile-skeleton-stat-value-${index}`} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

