import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export const SubscriptionTermsPage: React.FC = () => {
  const lastUpdated = "February 25, 2026";

  return (
    <div className="min-h-screen bg-surface">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-content-secondary hover:text-content mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-content mb-2">
            Subscription Terms & Payment Policy
          </h1>
          <p className="text-content-secondary">Last updated: {lastUpdated}</p>
        </div>

        {/* Content */}
        <div className="prose prose-lg max-w-none text-content">
          <div className="space-y-8">
            {/* Section 1 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">1. Subscription Plans</h2>
              <p className="mb-4">We offer the following subscription plans:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  <strong>Basic Plan:</strong> Free - Limited features for
                  personal use
                </li>
                <li>
                  <strong>Professional Plan:</strong> 9.99 USD/month - Enhanced
                  features for professionals
                </li>
                <li>
                  <strong>Enterprise Plan:</strong> 29.99 USD/month - Full
                  features for teams and businesses
                </li>
              </ul>
            </section>

            {/* Section 2 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">
                2. Billing and Payment
              </h2>
              <ul className="list-disc pl-6 space-y-2">
                <li>Subscriptions are billed on a monthly basis</li>
                <li>
                  Payment is processed automatically on your billing date (the
                  date you first subscribed)
                </li>
                <li>
                  We accept Visa and Mastercard via Paddle, our secure payment
                  processor
                </li>
                <li>
                  Your payment card details are securely tokenized and stored by
                  the payment provider. We do not store your full card details
                  on our servers.
                </li>
                <li>All prices are in US Dollars (USD)</li>
              </ul>
            </section>

            {/* Section 3 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">3. Automatic Renewal</h2>
              <p className="mb-4">
                Your subscription will automatically renew each month unless you
                cancel. By subscribing, you authorize us to charge your payment
                method on file for each renewal.
              </p>
              <p className="mb-4">Key points:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Charges occur monthly on your billing date</li>
                <li>You will be charged the same amount each month</li>
                <li>
                  You can cancel your subscription at any time to stop future
                  charges (see Section 4)
                </li>
                <li>
                  We'll send you a reminder email 3 days before each renewal
                </li>
              </ul>
            </section>

            {/* Section 4 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">4. Cancellation</h2>
              <p className="mb-4">
                You can cancel your subscription at any time from your Account →
                Billing page. No phone calls or emails to support are required.
              </p>
              <p className="mb-4">
                <strong>What happens when you cancel:</strong>
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>No future charges will be made to your payment method</li>
                <li>
                  You'll retain full access until the end of your current
                  billing period
                </li>
                <li>Your data will be preserved and not deleted</li>
                <li>You can reactivate your subscription at any time</li>
              </ul>
              <p className="mt-4">
                For detailed cancellation instructions, see our{" "}
                <Link
                  to="/cancel-subscription"
                  className="text-accent-base hover:underline"
                >
                  Cancellation Help Page
                </Link>
                .
              </p>
            </section>

            {/* Section 5 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">5. Refunds</h2>
              <p className="mb-4">
                We offer a <strong>10-day money-back guarantee</strong> for
                first-time subscription payments:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  <strong>First-time subscriptions:</strong> Full refund if
                  requested within 10 days of first payment — no questions asked
                </li>
                <li>
                  <strong>Service outages:</strong> Pro-rata refund for
                  documented service unavailability exceeding 24 hours
                </li>
                <li>
                  <strong>Unauthorized charges:</strong> Full refund for charges
                  made after cancellation
                </li>
              </ul>
              <p className="mt-4">
                After the 10-day period, subscription payments are
                non-refundable. To request a refund, contact us at{" "}
                <a
                  href="mailto:finflow@flux-lab.dev"
                  className="text-accent-base hover:underline"
                >
                  finflow@flux-lab.dev
                </a>{" "}
                with your account email and order details. Refunds are typically
                processed within 5-10 business days.
              </p>
            </section>

            {/* Section 6 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">6. Payment Security</h2>
              <p className="mb-4">
                We use Paddle, a PCI DSS Level 1 compliant payment processor, to
                handle all payment transactions.
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Your card details are tokenized and encrypted</li>
                <li>We do not store your full card number on our servers</li>
                <li>
                  Only the last 4 digits and expiration date are visible to us
                </li>
                <li>All payment data transmission uses TLS 1.2+ encryption</li>
              </ul>
            </section>

            {/* Section 7 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">7. Price Changes</h2>
              <p className="mb-4">
                We reserve the right to change subscription prices. If we
                increase prices:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>We'll notify you at least 30 days in advance via email</li>
                <li>
                  The new price will apply to your next billing cycle after the
                  notice period
                </li>
                <li>
                  You can cancel your subscription before the new price takes
                  effect
                </li>
              </ul>
            </section>

            {/* Section 8 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">8. Failed Payments</h2>
              <p className="mb-4">If your payment fails:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>We'll notify you immediately via email</li>
                <li>We'll retry the payment after 3 days</li>
                <li>
                  After 3 failed attempts, your subscription will be paused
                </li>
                <li>
                  You can update your payment method anytime from your Account →
                  Billing page
                </li>
              </ul>
            </section>

            {/* Section 9 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">
                9. Contact Information
              </h2>
              <p className="mb-4">For billing inquiries or support:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  Email:{" "}
                  <a
                    href="mailto:finflow@flux-lab.dev"
                    className="text-accent-base hover:underline"
                  >
                    finflow@flux-lab.dev
                  </a>
                </li>
                <li>
                  Support:{" "}
                  <a
                    href="mailto:finflow@flux-lab.dev"
                    className="text-accent-base hover:underline"
                  >
                    finflow@flux-lab.dev
                  </a>
                </li>
                <li>Business hours: Monday-Friday, 9:00 AM - 6:00 PM EET</li>
              </ul>
            </section>

            {/* Section 10 */}
            <section>
              <h2 className="text-2xl font-bold mb-4">10. Governing Law</h2>
              <p className="mb-4">
                These subscription terms are governed by the laws of Ukraine.
                Any disputes shall be resolved in accordance with Ukrainian
                consumer protection laws.
              </p>
            </section>

            {/* Related Links */}
            <section className="mt-12 pt-8 border-t border-[var(--border)]">
              <h2 className="text-2xl font-bold mb-4">Related Documents</h2>
              <ul className="space-y-2">
                <li>
                  <Link
                    to="/terms"
                    className="text-accent-base hover:underline"
                  >
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link
                    to="/privacy"
                    className="text-accent-base hover:underline"
                  >
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link
                    to="/cancel-subscription"
                    className="text-accent-base hover:underline"
                  >
                    How to Cancel Your Subscription
                  </Link>
                </li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionTermsPage;
