import React from 'react';
import { Link } from 'react-router-dom';
import { FaExclamationTriangle, FaArrowLeft } from 'react-icons/fa';

export const AccessDenied: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="text-center px-6">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-red-500/10 rounded-full mb-6">
          <FaExclamationTriangle className="w-10 h-10 text-red-400" />
        </div>
        
        <h1 className="text-4xl font-bold text-white mb-4">403</h1>
        <h2 className="text-xl font-semibold text-slate-300 mb-2">Access Denied</h2>
        <p className="text-slate-400 mb-8 max-w-md">
          You don't have permission to access this resource. 
          Admin privileges are required.
        </p>
        
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-colors"
        >
          <FaArrowLeft className="w-4 h-4" />
          Back to Login
        </Link>
      </div>
    </div>
  );
};
