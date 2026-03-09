import React from "react";
import { Link } from "react-router-dom";
import {
 FaArrowLeft,
 FaCheckCircle,
 FaEnvelope,
 FaComments,
} from "react-icons/fa";

export const CancelHelpPage: React.FC = () => {
 return (
 <div className="min-h-screen bg-surface">
 <div className="max-w-4xl mx-auto px-4 py-8">
 {/* Header */}
 <div className="mb-8">
 <Link
 to="/"
 className="inline-flex items-center gap-2 text-content-secondary hover:text-content mb-4"
 >
 <FaArrowLeft className="w-4 h-4" />
 Back to Home
 </Link>
 <h1 className="text-4xl font-bold text-content mb-2">
 How to Cancel Your Subscription
 </h1>
 <p className="text-content-secondary">
 You can cancel your subscription at any time, with no questions
 asked.
 </p>
 </div>

 {/* Content */}
 <div className="space-y-8">
 {/* Quick Steps */}
 <section className="bg-surface-alt p-6 rounded-lg border border-[var(--color-border)]">
 <h2 className="text-2xl font-bold text-content mb-4">
 Quick Steps
 </h2>
 <ol className="space-y-4">
 <li className="flex items-start gap-4">
 <div className="w-8 h-8 rounded-full bg-accent-base text-white flex items-center justify-center font-bold flex-shrink-0">
 1
 </div>
 <div className="flex-1 pt-1">
 <p className="text-content">
 <strong>Log in to your account</strong> at{" "}
 <Link to="/login" className="text-accent-base hover:underline">
 finflow.ltd/login
 </Link>
 </p>
 </div>
 </li>
 <li className="flex items-start gap-4">
 <div className="w-8 h-8 rounded-full bg-accent-base text-white flex items-center justify-center font-bold flex-shrink-0">
 2
 </div>
 <div className="flex-1 pt-1">
 <p className="text-content">
 <strong>Go to Account → Billing</strong> from the navigation
 menu
 </p>
 </div>
 </li>
 <li className="flex items-start gap-4">
 <div className="w-8 h-8 rounded-full bg-accent-base text-white flex items-center justify-center font-bold flex-shrink-0">
 3
 </div>
 <div className="flex-1 pt-1">
 <p className="text-content">
 <strong>Click "Cancel Subscription"</strong> button
 </p>
 </div>
 </li>
 <li className="flex items-start gap-4">
 <div className="w-8 h-8 rounded-full bg-accent-base text-white flex items-center justify-center font-bold flex-shrink-0">
 4
 </div>
 <div className="flex-1 pt-1">
 <p className="text-content">
 <strong>Choose cancellation option:</strong>
 </p>
 <ul className="list-disc pl-6 mt-2 space-y-1 text-content-secondary">
 <li>
 <strong className="text-content">
 Cancel at period end
 </strong>{" "}
 (Recommended) - Keep access until your billing date
 </li>
 <li>
 <strong className="text-content">
 Cancel immediately
 </strong>{" "}
 - Lose access now, possible refund
 </li>
 </ul>
 </div>
 </li>
 <li className="flex items-start gap-4">
 <div className="w-8 h-8 rounded-full bg-accent-base text-white flex items-center justify-center font-bold flex-shrink-0">
 5
 </div>
 <div className="flex-1 pt-1">
 <p className="text-content">
 <strong>Confirm cancellation</strong> - You'll receive a
 confirmation email
 </p>
 </div>
 </li>
 </ol>
 </section>

 {/* What Happens */}
 <section>
 <h2 className="text-2xl font-bold text-content mb-4">
 What Happens After Cancellation
 </h2>
 <div className="space-y-3">
 <div className="flex items-start gap-3 p-4 rounded-lg bg-surface-alt border border-[var(--color-border)]">
 <FaCheckCircle className="w-5 h-5 text-success-base flex-shrink-0 mt-0.5" />
 <div>
 <p className="font-semibold text-content">
 No future charges
 </p>
 <p className="text-sm text-content-secondary">
 Your payment method will not be charged again. The automatic
 renewal is stopped immediately.
 </p>
 </div>
 </div>

 <div className="flex items-start gap-3 p-4 rounded-lg bg-surface-alt border border-[var(--color-border)]">
 <FaCheckCircle className="w-5 h-5 text-success-base flex-shrink-0 mt-0.5" />
 <div>
 <p className="font-semibold text-content">
 Keep access until period ends
 </p>
 <p className="text-sm text-content-secondary">
 If you choose "Cancel at period end," you'll retain full
 access to premium features until the end of your current
 billing period.
 </p>
 </div>
 </div>

 <div className="flex items-start gap-3 p-4 rounded-lg bg-surface-alt border border-[var(--color-border)]">
 <FaCheckCircle className="w-5 h-5 text-success-base flex-shrink-0 mt-0.5" />
 <div>
 <p className="font-semibold text-content">
 Your data is preserved
 </p>
 <p className="text-sm text-content-secondary">
 All your data remains intact. We don't delete anything when
 you cancel. You can reactivate anytime.
 </p>
 </div>
 </div>

 <div className="flex items-start gap-3 p-4 rounded-lg bg-surface-alt border border-[var(--color-border)]">
 <FaCheckCircle className="w-5 h-5 text-success-base flex-shrink-0 mt-0.5" />
 <div>
 <p className="font-semibold text-content">
 Reactivate anytime
 </p>
 <p className="text-sm text-content-secondary">
 Changed your mind? You can reactivate your subscription from
 the same Billing page with just one click.
 </p>
 </div>
 </div>
 </div>
 </section>

 {/* Access After Cancellation */}
 <section>
 <h2 className="text-2xl font-bold text-content mb-4">
 Access After Cancellation
 </h2>
 <div className="bg-surface-alt p-6 rounded-lg border border-[var(--color-border)]">
 <p className="text-content mb-4">
 After your subscription period ends (or immediately if you chose
 immediate cancellation):
 </p>
 <ul className="list-disc pl-6 space-y-2 text-content-secondary">
 <li>Your account will be downgraded to the Free plan</li>
 <li>You'll have access to Free plan features</li>
 <li>Premium features will be disabled but not deleted</li>
 <li>Your data remains accessible (within Free plan limits)</li>
 <li>You can export your data anytime</li>
 </ul>
 </div>
 </section>

 {/* Reactivation */}
 <section>
 <h2 className="text-2xl font-bold text-content mb-4">
 How to Reactivate
 </h2>
 <p className="text-content mb-4">
 Changed your mind? Reactivating is easy:
 </p>
 <ol className="list-decimal pl-6 space-y-2 text-content-secondary">
 <li>Go to Account → Billing</li>
 <li>Click "Reactivate Subscription" button</li>
 <li>Your previous payment method will be charged immediately</li>
 <li>Premium features are restored instantly</li>
 </ol>
 </section>

 {/* Cancellation Policy */}
 <section>
 <h2 className="text-2xl font-bold text-content mb-4">
 Cancellation Policy
 </h2>
 <div className="bg-surface-alt p-6 rounded-lg border border-[var(--color-border)]">
 <p className="text-content mb-4">
 <strong>
 You have the right to cancel at any time, for any reason.
 </strong>
 </p>
 <p className="text-content-secondary mb-4">
 Per our{" "}
 <Link
 to="/subscription-terms"
 className="text-accent-base hover:underline"
 >
 Subscription Terms
 </Link>
 , we support your right to cancel your subscription without
 penalty. There are no cancellation fees, and you don't need to
 provide a reason.
 </p>
 <p className="text-content-secondary">
 Refunds are handled according to our{" "}
 <Link
 to="/subscription-terms"
 className="text-accent-base hover:underline"
 >
 Refund Policy
 </Link>
 .
 </p>
 </div>
 </section>

 {/* Need Help */}
 <section className="mt-12">
 <h2 className="text-2xl font-bold text-content mb-4">
 Need Help?
 </h2>
 <div className="grid md:grid-cols-2 gap-4">
 <div className="p-6 rounded-lg bg-surface-alt border border-[var(--color-border)]">
 <FaEnvelope className="w-8 h-8 text-accent-base mb-4" />
 <h3 className="text-lg font-semibold text-content mb-2">
 Email Support
 </h3>
 <p className="text-content-secondary mb-4">
 If you have trouble canceling or questions about billing
 </p>
 <a
 href="mailto:finflow@flux-lab.dev"
 className="text-accent-base hover:underline font-medium"
 >
 finflow@flux-lab.dev
 </a>
 </div>

 <div className="p-6 rounded-lg bg-surface-alt border border-[var(--color-border)]">
 <FaComments className="w-8 h-8 text-accent-base mb-4" />
 <h3 className="text-lg font-semibold text-content mb-2">
 Live Chat
 </h3>
 <p className="text-content-secondary mb-4">
 Available Monday-Friday, 9:00 AM - 6:00 PM EET
 </p>
 <button className="text-accent-base hover:underline font-medium">
 Start Chat →
 </button>
 </div>
 </div>
 </section>

 {/* Related Links */}
 <section className="mt-8 pt-8 border-t border-[var(--color-border)]">
 <h2 className="text-xl font-bold text-content mb-4">
 Related Articles
 </h2>
 <ul className="space-y-2">
 <li>
 <Link
 to="/subscription-terms"
 className="text-accent-base hover:underline"
 >
 Subscription Terms & Payment Policy
 </Link>
 </li>
 <li>
 <Link to="/terms" className="text-accent-base hover:underline">
 Terms of Service
 </Link>
 </li>
 <li>
 <Link to="/privacy" className="text-accent-base hover:underline">
 Privacy Policy
 </Link>
 </li>
 <li>
 <Link to="/refund" className="text-accent-base hover:underline">
 Refund Policy
 </Link>
 </li>
 </ul>
 </section>
 </div>
 </div>
 </div>
 );
};

export default CancelHelpPage;
