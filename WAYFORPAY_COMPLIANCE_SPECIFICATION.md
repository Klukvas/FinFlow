# WayForPay Compliance Specification
## Recurring Payments & User Consent Implementation

**Document Version:** 1.0  
**Date:** 2026-01-28  
**Status:** Draft for Review  

---

## Executive Summary

This document specifies the requirements for making our SaaS subscription system compliant with WayForPay payment processor requirements, Ukrainian consumer protection laws, and international best practices for recurring payments.

**Key Compliance Areas:**
1. Explicit user consent for payment data storage and recurring charges
2. Clear disclosure of subscription terms before payment
3. Self-service cancellation capability
4. Audit trail of user consent and actions
5. Public accessibility of terms and cancellation instructions

---

## 1️⃣ User Consent Requirements (Legal & Frontend)

### 1.1 Legal Framework

**Applicable Regulations:**
- WayForPay Merchant Agreement (tokenization consent requirement)
- Ukrainian Law on Consumer Rights Protection (recurring payment disclosure)
- PCI DSS compliance (payment data storage consent)
- GDPR Article 6(1)(a) for EU users (explicit consent for data processing)

### 1.2 Consent Text Requirements

The consent must be shown BEFORE the user initiates payment and must include:

#### **English Version:**
```
□ I agree to subscribe to [PLAN_NAME] plan

By subscribing, I confirm that:
• My payment card details will be securely tokenized and stored by WayForPay payment processor
• I authorize automatic monthly charges of [AMOUNT] [CURRENCY] to my payment card
• Charges will occur on the [DAY] of each month starting from [START_DATE]
• I can cancel my subscription at any time from my account settings
• Upon cancellation, no future charges will be made

I have read and agree to the Terms of Service and Subscription & Payment Policy.
```

#### **Ukrainian Version (Required for UA users):**
```
□ Я погоджуюся оформити підписку на план [PLAN_NAME]

Підписуючись, я підтверджую, що:
• Дані моєї платіжної картки будуть безпечно токенізовані та збережені платіжною системою WayForPay
• Я надаю дозвіл на автоматичне щомісячне списання [AMOUNT] [CURRENCY] з моєї платіжної картки
• Списання відбуватиметься [DAY] числа кожного місяця, починаючи з [START_DATE]
• Я можу скасувати підписку в будь-який час в налаштуваннях мого облікового запису
• Після скасування жодних подальших списань не відбудеться

Я прочитав(-ла) та погоджуюся з Умовами надання послуг та Політикою підписки та оплати.
```

### 1.3 Consent Validation Rules

**Frontend Validation:**
- Consent checkbox MUST be explicitly checked (not pre-checked)
- "Pay Now" / "Subscribe" button MUST be disabled until consent is given
- Links to Terms and Policy must be visible and functional
- Amount, currency, and plan name must be clearly displayed
- Next billing date must be calculated and shown

**Backend Validation:**
- Verify consent_given flag is `true` in payment request
- Verify consent_version matches current version
- Reject payment creation if consent requirements not met

### 1.4 Consent Versioning

Maintain version control for consent text:
- **Version Format:** `v1.0.0` (semantic versioning)
- **Change Triggers:** Any material change to terms, pricing structure, or payment flow
- **Re-consent:** Users must re-consent if terms change materially
- **Storage:** Store consent version with each subscription

**Current Version:** `v1.0.0` (Initial implementation)

---

## 2️⃣ Subscription Modal UI/UX Flow

### 2.1 Modal Structure

```
┌─────────────────────────────────────────────────────┐
│  [X]                                                │
│                                                     │
│  🚀 Upgrade to [PLAN_NAME]                         │
│  ────────────────────────────────────────────────  │
│                                                     │
│  💎 Plan Features                                  │
│  • Unlimited expenses                              │
│  • Advanced analytics                              │
│  • Priority support                                │
│  • [...]                                           │
│                                                     │
│  💰 Subscription Details                           │
│  ┌───────────────────────────────────────────┐    │
│  │ Monthly price:        9.99 UAH            │    │
│  │ First billing date:   Jan 28, 2026        │    │
│  │ Next billing date:    Feb 28, 2026        │    │
│  │ Payment method:       Credit/Debit Card   │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  ⚠️ Important Information                          │
│  Your payment card will be securely stored by      │
│  WayForPay. You can cancel anytime from your       │
│  account settings. Learn more about how we         │
│  protect your data.                                │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │ ☐ I have read and agree to:              │     │
│  │   • Terms of Service                      │     │
│  │   • Subscription & Payment Policy         │     │
│  │                                            │     │
│  │ I authorize recurring monthly charges     │     │
│  │ of 9.99 UAH to my payment card and        │     │
│  │ understand that I can cancel anytime.     │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  [     Cancel     ]  [  Proceed to Payment  ]     │
│                           (disabled until ✓)       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2.2 User Interaction Flow

**Step 1: User clicks "Upgrade Plan" from SubscriptionLimits component**
- Modal opens with plan comparison
- User selects plan by clicking on plan card

**Step 2: Plan selection expands to show subscription details**
- Show monthly price clearly
- Calculate and display first billing date (today)
- Calculate and display next billing date (today + 30 days)
- Show payment method (card tokenization explanation)

**Step 3: Consent checkbox interaction**
- Checkbox is unchecked by default
- Text includes inline links to Terms and Policy
- Clicking links opens in new tab/window
- "Proceed to Payment" button is disabled (greyed out)

**Step 4: User checks consent checkbox**
- Button becomes enabled with animation
- Button shows active state with color change
- Optional: Show checkmark animation to confirm action

**Step 5: User clicks "Proceed to Payment"**
- Record consent timestamp, IP address, user agent
- Create payment record in backend
- Navigate to WayForPay checkout page
- Modal closes after successful navigation

### 2.3 Implementation Components

**New Component: `SubscriptionConsentModal.tsx`**
```typescript
interface SubscriptionConsentModalProps {
  isOpen: boolean;
  onClose: () => void;
  planCode: string;
  planName: string;
  monthlyPrice: number;
  currency: string;
  onConsent: (consentData: ConsentData) => Promise<void>;
}

interface ConsentData {
  consentGiven: boolean;
  consentVersion: string;
  consentTimestamp: string;
  ipAddress: string; // captured from backend
  userAgent: string;
  planCode: string;
  amount: number;
  currency: string;
}
```

### 2.4 Accessibility Requirements

- Consent checkbox must have clear label with aria-label
- Links must be keyboard navigable
- Button states must be clearly indicated for screen readers
- Focus management: auto-focus on consent checkbox when modal opens
- ESC key closes modal
- Color contrast ratio > 4.5:1 for text

---

## 3️⃣ Subscription Cancellation Flow

### 3.1 User Journey

```
User Account → Billing/Subscription → [Cancel Subscription] Button
                                              ↓
                                    Cancellation Confirmation Modal
                                              ↓
                          [Cancel Immediately] or [Cancel at Period End]
                                              ↓
                                    Cancellation Processed
                                              ↓
                                    Confirmation Email Sent
```

### 3.2 Cancellation Options

**Option A: Immediate Cancellation**
- Subscription status → `canceled`
- `canceled_at` → current timestamp
- `auto_renew` → `false`
- Access: Immediate loss of premium features (grace period: 24 hours)
- Refund: Pro-rata refund for unused days (optional, business decision)

**Option B: Cancel at Period End** (Recommended)
- Subscription status → `active` (remains active)
- `auto_renew` → `false`
- `canceled_at` → current timestamp (for audit trail)
- Access: Full access until `expires_at` date
- Next billing: Will not occur (scheduler skips subscriptions with `auto_renew=false`)

### 3.3 Cancellation Confirmation Modal

```
┌─────────────────────────────────────────────────────┐
│  ⚠️ Cancel Subscription?                            │
│  ────────────────────────────────────────────────  │
│                                                     │
│  You are about to cancel your [PLAN_NAME]          │
│  subscription.                                      │
│                                                     │
│  📅 Current billing period ends: [DATE]            │
│  💰 You've paid: [AMOUNT] [CURRENCY]               │
│                                                     │
│  What happens when you cancel?                     │
│  • No future charges will be made                  │
│  • You'll keep access until [PERIOD_END_DATE]      │
│  • Your data will be preserved                     │
│  • You can re-subscribe anytime                    │
│                                                     │
│  Are you sure you want to cancel?                  │
│                                                     │
│  Reason (optional):                                │
│  ┌──────────────────────────────────────────┐     │
│  │ [Dropdown: Too expensive / Not using /    │     │
│  │  Missing features / Other]                │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  [  Keep Subscription  ]  [  Cancel Subscription ] │
│       (primary)                   (danger)          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 3.4 Post-Cancellation UX

**Immediate Feedback:**
- Success toast: "Subscription canceled. You'll have access until [DATE]."
- Update subscription card to show "Canceled" badge
- Show "Reactivate Subscription" button

**Email Notification:**
- Subject: "Your subscription has been canceled"
- Include: Cancellation date, access end date, reactivation link
- Call-to-action: "Change your mind? Reactivate now"

**In-App Indicators:**
- Subscription status badge: "Canceled (Active until [DATE])"
- Banner on billing page: "Your subscription will end on [DATE]"
- Remove auto-renew indicator

### 3.5 Cancellation API Endpoint

**Endpoint:** `DELETE /api/v1/subscriptions/my-subscription`

**Request:**
```json
{
  "cancellation_reason": "too_expensive" | "not_using" | "missing_features" | "other",
  "cancellation_comment": "Optional free text",
  "cancel_immediately": false  // false = cancel at period end
}
```

**Response:**
```json
{
  "success": true,
  "subscription": {
    "id": 123,
    "status": "active",  // or "canceled" if immediate
    "auto_renew": false,
    "canceled_at": "2026-01-28T10:30:00Z",
    "expires_at": "2026-02-28T10:30:00Z",
    "access_ends_at": "2026-02-28T10:30:00Z"
  },
  "message": "Subscription canceled successfully. You'll have access until Feb 28, 2026."
}
```

---

## 4️⃣ Backend Implementation Requirements

### 4.1 Database Schema Changes

#### **Subscriptions Table (Already has most fields)**

Add new fields:
```sql
ALTER TABLE subscriptions ADD COLUMN consent_given BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE subscriptions ADD COLUMN consent_version VARCHAR(16);
ALTER TABLE subscriptions ADD COLUMN consent_timestamp TIMESTAMP;
ALTER TABLE subscriptions ADD COLUMN consent_ip_address VARCHAR(45);
ALTER TABLE subscriptions ADD COLUMN consent_user_agent TEXT;
ALTER TABLE subscriptions ADD COLUMN cancellation_reason VARCHAR(32);
ALTER TABLE subscriptions ADD COLUMN cancellation_comment TEXT;
ALTER TABLE subscriptions ADD COLUMN cancellation_ip_address VARCHAR(45);
```

#### **New Table: subscription_consent_log**

```sql
CREATE TABLE subscription_consent_log (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id VARCHAR(128) NOT NULL,
    consent_version VARCHAR(16) NOT NULL,
    consent_text TEXT NOT NULL,  -- Store full text at time of consent
    consent_language VARCHAR(8) NOT NULL,  -- 'en', 'uk'
    consent_given_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    browser_fingerprint VARCHAR(64),
    metadata JSONB,  -- Additional context
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_consent_log_user ON subscription_consent_log(user_id);
CREATE INDEX idx_consent_log_subscription ON subscription_consent_log(subscription_id);
```

### 4.2 API Changes

#### **Payment Creation (Modified)**

**Endpoint:** `POST /api/v1/payments`

**Request:**
```json
{
  "purpose": "SUBSCRIPTION",
  "plan_code": "professional",
  "amount": "9.99",
  "currency": "UAH",
  "return_url": "https://app.example.com/payment/return",
  "metadata": {
    "consent_given": true,
    "consent_version": "v1.0.0",
    "consent_timestamp": "2026-01-28T10:30:00Z",
    "consent_language": "en"
  }
}
```

**Backend Validation:**
```python
def validate_subscription_consent(request: CreatePaymentRequest):
    if request.purpose == PaymentPurpose.SUBSCRIPTION:
        metadata = request.metadata or {}
        
        if not metadata.get('consent_given'):
            raise ValidationError(
                "User consent required for subscription payments",
                error_code="@payment_service/CONSENT_REQUIRED"
            )
        
        if not metadata.get('consent_version'):
            raise ValidationError(
                "Consent version required",
                error_code="@payment_service/CONSENT_VERSION_REQUIRED"
            )
        
        # Validate consent version matches current
        current_version = settings.current_consent_version  # e.g., "v1.0.0"
        if metadata.get('consent_version') != current_version:
            raise ValidationError(
                f"Consent version mismatch. Current: {current_version}",
                error_code="@payment_service/CONSENT_VERSION_MISMATCH"
            )
```

#### **New: Consent Recording (subscription_service)**

**Endpoint:** `POST /api/v1/subscriptions/consent`

**Request:**
```json
{
  "subscription_id": 123,
  "consent_version": "v1.0.0",
  "consent_language": "en",
  "plan_code": "professional",
  "amount": "9.99",
  "currency": "UAH"
}
```

**Headers:**
```
X-User-Id: user_123
X-Real-IP: 192.168.1.1
User-Agent: Mozilla/5.0...
```

**Backend Logic:**
```python
def record_subscription_consent(
    subscription_id: int,
    user_id: str,
    consent_data: ConsentRecordRequest,
    ip_address: str,
    user_agent: str,
) -> ConsentLog:
    # Get current consent text from config/database
    consent_text = get_consent_text(
        version=consent_data.consent_version,
        language=consent_data.consent_language
    )
    
    # Create consent log entry
    consent_log = SubscriptionConsentLog(
        subscription_id=subscription_id,
        user_id=user_id,
        consent_version=consent_data.consent_version,
        consent_text=consent_text,
        consent_language=consent_data.consent_language,
        consent_given_at=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={
            "plan_code": consent_data.plan_code,
            "amount": str(consent_data.amount),
            "currency": consent_data.currency,
        }
    )
    
    db.add(consent_log)
    db.commit()
    
    # Update subscription with consent info
    subscription = db.query(Subscription).filter_by(id=subscription_id).first()
    subscription.consent_given = True
    subscription.consent_version = consent_data.consent_version
    subscription.consent_timestamp = datetime.utcnow()
    subscription.consent_ip_address = ip_address
    subscription.consent_user_agent = user_agent
    
    db.commit()
    
    return consent_log
```

#### **New: Cancel Subscription**

**Endpoint:** `DELETE /api/v1/subscriptions/my-subscription`

**Request:**
```json
{
  "cancellation_reason": "too_expensive",
  "cancellation_comment": "Can't afford right now",
  "cancel_immediately": false
}
```

**Backend Logic:**
```python
def cancel_subscription(
    user_id: str,
    cancel_request: CancelSubscriptionRequest,
    ip_address: str,
) -> Subscription:
    subscription = get_user_subscription(user_id)
    
    if not subscription:
        raise NotFoundError("No active subscription found")
    
    if subscription.status == "canceled":
        raise ValidationError("Subscription already canceled")
    
    # Set auto_renew to false (prevents future charges)
    subscription.auto_renew = False
    subscription.canceled_at = datetime.utcnow()
    subscription.cancellation_reason = cancel_request.cancellation_reason
    subscription.cancellation_comment = cancel_request.cancellation_comment
    subscription.cancellation_ip_address = ip_address
    
    # If immediate cancellation requested
    if cancel_request.cancel_immediately:
        subscription.status = "canceled"
        subscription.expires_at = datetime.utcnow()
        
        # Trigger feature access revocation
        events.publish_subscription_changed(
            user_id=user_id,
            plan_code="basic",  # Downgrade to free plan
            status="canceled",
        )
    
    # If cancel at period end (recommended)
    else:
        # Status remains "active"
        # expires_at remains the end of current period
        # Scheduler will not renew due to auto_renew=false
        pass
    
    db.commit()
    
    # Send cancellation email
    send_cancellation_email(subscription)
    
    # Log cancellation event
    log_subscription_event(
        subscription_id=subscription.id,
        event_type="CANCELED",
        metadata={
            "reason": cancel_request.cancellation_reason,
            "immediate": cancel_request.cancel_immediately,
        }
    )
    
    return subscription
```

### 4.3 Scheduler Service Changes

**Current Logic:**
```python
# scheduler_service/jobs/subscription_renewal.py

def process_subscriptions_due_for_renewal():
    # Get subscriptions where next_billing_date <= today
    due_subscriptions = db.query(Subscription).filter(
        Subscription.next_billing_date <= date.today(),
        Subscription.status == "active"
    ).all()
```

**New Logic (with cancellation check):**
```python
def process_subscriptions_due_for_renewal():
    # Get subscriptions where next_billing_date <= today
    # AND auto_renew is True (exclude canceled subscriptions)
    due_subscriptions = db.query(Subscription).filter(
        Subscription.next_billing_date <= date.today(),
        Subscription.status == "active",
        Subscription.auto_renew == True,  # NEW: Check auto_renew flag
        Subscription.recurring_token.isnot(None),  # Must have token
    ).all()
    
    for subscription in due_subscriptions:
        try:
            # Create recurring payment via payment_service
            payment = await payment_service.create_recurring_payment(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                plan_code=subscription.plan_code,
                amount=get_plan_price(subscription.plan_code),
                currency="UAH",
                recurring_token=subscription.recurring_token,
            )
            
            if payment.status == PaymentStatus.PAID:
                # Update subscription
                subscription.next_billing_date = calculate_next_billing_date(subscription)
                subscription.expires_at = subscription.next_billing_date
                subscription.last_payment_id = str(payment.id)
            else:
                # Payment failed - mark as past_due
                subscription.status = "past_due"
                send_payment_failed_email(subscription)
        
        except Exception as e:
            logger.error(f"Failed to renew subscription {subscription.id}: {e}")
            # Don't crash - continue to next subscription
```

### 4.4 Idempotency & Safety

**Idempotency Keys:**
- Payment creation: Use `user_id + plan_code + timestamp` hash
- Cancellation: Check if already canceled before processing
- Consent recording: Use `subscription_id + consent_version + timestamp` hash

**Rate Limiting:**
- Payment creation: 3 requests per minute per user
- Cancellation: 1 request per minute per user
- Consent recording: 5 requests per minute per user

**Transaction Safety:**
- Use database transactions for all multi-step operations
- Implement retry logic with exponential backoff
- Store events in audit log before state changes
- Use pessimistic locking for critical updates

---

## 5️⃣ Public URLs & Legal Pages

### 5.1 Required Public Pages

WayForPay requires these pages to be publicly accessible (no login required):

#### **Page 1: Subscription Terms & Payment Policy**

**URL:** `https://yourapp.com/legal/subscription-terms`

**Content Requirements:**
- Service description
- Subscription plans and pricing
- Billing cycle explanation
- Payment methods accepted
- Tokenization and data storage disclosure
- Automatic renewal terms
- Cancellation policy and process
- Refund policy
- Currency and taxes
- Contact information for billing support

**Sample Structure:**
```markdown
# Subscription Terms & Payment Policy

Last updated: [DATE]

## 1. Subscription Plans
We offer the following subscription plans:
- Basic: Free (no payment required)
- Professional: $9.99/month
- Enterprise: $29.99/month

## 2. Billing and Payment
- Subscriptions are billed monthly
- Payment is processed automatically on your billing date
- We accept Visa, Mastercard via WayForPay
- Your payment card details are securely tokenized and stored by WayForPay payment processor

## 3. Automatic Renewal
Your subscription will automatically renew each month unless you cancel.
You authorize us to charge your payment method on file for each renewal.

## 4. Cancellation
You can cancel your subscription at any time from your Account → Billing page.
Upon cancellation:
- No future charges will be made
- You'll retain access until the end of your current billing period
- Your data will be preserved

## 5. Refunds
[Your refund policy]

## 6. Payment Security
We use WayForPay, a PCI DSS compliant payment processor.
We do not store your full card details on our servers.

## 7. Contact
For billing inquiries: billing@yourapp.com
```

#### **Page 2: How to Cancel Your Subscription**

**URL:** `https://yourapp.com/help/cancel-subscription`

**Content Requirements:**
- Step-by-step cancellation instructions with screenshots
- What happens after cancellation
- Access period after cancellation
- Reactivation process
- Contact information if help needed

**Sample Structure:**
```markdown
# How to Cancel Your Subscription

You can cancel your subscription at any time, with no questions asked.

## Cancellation Steps

1. Log in to your account
2. Go to Account → Billing / Subscription
3. Click "Cancel Subscription" button
4. Choose cancellation option:
   - Cancel at period end (recommended) - keep access until [DATE]
   - Cancel immediately - lose access now, possible pro-rata refund
5. Confirm cancellation

## What Happens After Cancellation

✅ No future charges will be made
✅ You keep access until the end of your current billing period
✅ Your data is preserved and not deleted
✅ You can reactivate anytime

## Access After Cancellation

After cancellation, you'll still have full access to your premium features until [PERIOD_END_DATE].
After that date, your account will be downgraded to the Free plan.

## Reactivation

Changed your mind? You can reactivate your subscription anytime:
1. Go to Account → Billing
2. Click "Reactivate Subscription"
3. Your previous payment method will be charged

## Need Help?

If you have trouble canceling or questions about billing:
📧 Email: billing@yourapp.com
💬 Live Chat: Available Mon-Fri 9am-6pm EET

## Cancellation Policy

Per our Terms of Service, you have the right to cancel at any time.
Refunds are handled according to our Refund Policy.
```

#### **Page 3: Privacy Policy (Update required)**

**URL:** `https://yourapp.com/legal/privacy`

**New Section to Add:**
```markdown
## Payment Information and Tokenization

When you subscribe to a paid plan, we use WayForPay as our payment processor.

**What we collect:**
- Transaction history (amounts, dates, status)
- Billing email address
- Payment token reference (not your full card details)

**What WayForPay stores:**
- Tokenized payment card information
- Card holder name
- Last 4 digits of card number
- Card expiration date

**How we use this information:**
- Process monthly subscription charges
- Send billing receipts
- Provide customer support for billing issues

**Your rights:**
- You can request deletion of your payment token by canceling your subscription
- You can request a copy of your transaction history
- You can update your payment method at any time

**Data retention:**
- Active subscriptions: Payment tokens stored indefinitely
- Canceled subscriptions: Payment tokens deleted after 90 days
- Transaction history: Retained for 7 years for accounting purposes
```

### 5.2 Footer Links

Add to website footer (all pages):
```html
<footer>
  <!-- ... other footer content ... -->
  <div class="legal-links">
    <a href="/legal/terms">Terms of Service</a>
    <a href="/legal/privacy">Privacy Policy</a>
    <a href="/legal/subscription-terms">Subscription Terms</a>
    <a href="/help/cancel-subscription">Cancel Subscription</a>
  </div>
</footer>
```

### 5.3 WayForPay Merchant Account Configuration

Provide these URLs in WayForPay merchant portal:
- **Return URL:** `https://yourapp.com/payment/return`
- **Callback URL:** `https://api.yourapp.com/v1/payment/callback`
- **Terms URL:** `https://yourapp.com/legal/subscription-terms`
- **Privacy URL:** `https://yourapp.com/legal/privacy`

---

## 6️⃣ Email Notifications

### 6.1 Subscription Confirmation Email

**Trigger:** After first successful payment  
**Template:**

```
Subject: Welcome to [PLAN_NAME] - Subscription Confirmed

Hi [USER_NAME],

Your subscription to [PLAN_NAME] is now active! 🎉

SUBSCRIPTION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plan: [PLAN_NAME]
Price: [AMOUNT] [CURRENCY] per month
Started: [DATE]
Next billing: [NEXT_BILLING_DATE]

WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [Feature 1]
✓ [Feature 2]
✓ [Feature 3]

PAYMENT INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Payment method: •••• [LAST_4_DIGITS]
Automatic renewal: Enabled
Next charge: [NEXT_BILLING_DATE]

You can manage your subscription or cancel anytime:
[Manage Subscription Button]

Questions? Reply to this email or visit our Help Center.

Thanks for subscribing!
The [APP_NAME] Team
```

### 6.2 Cancellation Confirmation Email

**Trigger:** User cancels subscription  
**Template:**

```
Subject: Subscription Canceled - We're Sorry to See You Go

Hi [USER_NAME],

We've processed your cancellation request for [PLAN_NAME].

CANCELLATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Canceled on: [CANCELLATION_DATE]
Access until: [ACCESS_END_DATE]
No future charges: Confirmed ✓

WHAT HAPPENS NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ You'll keep full access until [ACCESS_END_DATE]
✓ No future charges will be made
✓ Your data will be preserved
✓ You can reactivate anytime

REACTIVATE ANYTIME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Changed your mind? Reactivate with one click:
[Reactivate Subscription Button]

We'd love to hear why you canceled (optional):
[Feedback Form Link]

Thanks for being a subscriber!
The [APP_NAME] Team
```

### 6.3 Upcoming Renewal Reminder Email

**Trigger:** 3 days before next billing  
**Template:**

```
Subject: Upcoming Renewal - [PLAN_NAME] Subscription

Hi [USER_NAME],

Your [PLAN_NAME] subscription will renew in 3 days.

RENEWAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Renewal date: [NEXT_BILLING_DATE]
Amount: [AMOUNT] [CURRENCY]
Payment method: •••• [LAST_4_DIGITS]

MANAGE YOUR SUBSCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Update Payment Method]
[View Billing History]
[Cancel Subscription]

Questions? Contact us anytime.

The [APP_NAME] Team
```

### 6.4 Failed Payment Email

**Trigger:** Recurring payment fails  
**Template:**

```
Subject: ⚠️ Payment Failed - Action Required

Hi [USER_NAME],

We couldn't process your subscription payment for [PLAN_NAME].

PAYMENT ISSUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Attempted: [ATTEMPT_DATE]
Amount: [AMOUNT] [CURRENCY]
Payment method: •••• [LAST_4_DIGITS]
Reason: [FAILURE_REASON]

ACTION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please update your payment method to avoid service interruption.

[Update Payment Method Button]

We'll retry the payment in 3 days. If unsuccessful, your subscription
will be paused and premium features will be disabled.

Need help? Contact support.

The [APP_NAME] Team
```

---

## 7️⃣ Implementation Checklist

### Backend Tasks

- [ ] **Database Migrations**
  - [ ] Add consent fields to `subscriptions` table
  - [ ] Create `subscription_consent_log` table
  - [ ] Add cancellation fields to `subscriptions` table

- [ ] **Subscription Service**
  - [ ] Implement consent recording endpoint
  - [ ] Implement cancellation endpoint
  - [ ] Add consent validation to payment creation
  - [ ] Create consent text configuration
  - [ ] Implement consent versioning system

- [ ] **Payment Service**
  - [ ] Add consent validation to `create_payment`
  - [ ] Store consent data in payment metadata
  - [ ] Update payment callback to handle consent

- [ ] **Scheduler Service**
  - [ ] Update renewal logic to check `auto_renew` flag
  - [ ] Skip canceled subscriptions
  - [ ] Add retry logic for failed payments

- [ ] **Email Service**
  - [ ] Subscription confirmation email template
  - [ ] Cancellation confirmation email template
  - [ ] Renewal reminder email template (3 days before)
  - [ ] Failed payment email template

### Frontend Tasks

- [ ] **Subscription Modal**
  - [ ] Create `SubscriptionConsentModal` component
  - [ ] Add consent checkbox with validation
  - [ ] Show subscription details (price, dates)
  - [ ] Add links to Terms and Policy
  - [ ] Implement consent state management
  - [ ] Capture consent timestamp

- [ ] **Billing Page**
  - [ ] Add "Cancel Subscription" button
  - [ ] Create cancellation confirmation modal
  - [ ] Show subscription status clearly
  - [ ] Add "Reactivate" button for canceled subscriptions
  - [ ] Display next billing date / access end date

- [ ] **Payment Flow**
  - [ ] Include consent data in payment request
  - [ ] Pass consent version to backend
  - [ ] Handle consent validation errors

### Legal Pages

- [ ] **Create/Update Pages**
  - [ ] Subscription Terms & Payment Policy page
  - [ ] How to Cancel Your Subscription help page
  - [ ] Update Privacy Policy with payment section
  - [ ] Add footer links to all legal pages

- [ ] **WayForPay Configuration**
  - [ ] Add Terms URL to merchant account
  - [ ] Add Privacy URL to merchant account
  - [ ] Verify all URLs are publicly accessible

### Testing

- [ ] **User Flow Testing**
  - [ ] Test subscription signup with consent
  - [ ] Test payment with and without consent
  - [ ] Test cancellation (immediate and period-end)
  - [ ] Test reactivation after cancellation
  - [ ] Test consent text in Ukrainian and English

- [ ] **Backend Testing**
  - [ ] Unit tests for consent validation
  - [ ] Unit tests for cancellation logic
  - [ ] Integration tests for payment flow
  - [ ] Test scheduler with canceled subscriptions
  - [ ] Test email notifications

- [ ] **Compliance Testing**
  - [ ] Verify consent text meets requirements
  - [ ] Verify audit trail is complete
  - [ ] Verify cancellation is self-service
  - [ ] Verify public pages are accessible

---

## 8️⃣ Compliance Verification

### Pre-Launch Checklist

- [ ] **User Consent**
  - [ ] Consent text reviewed by legal counsel
  - [ ] Consent is explicit (not pre-checked)
  - [ ] Consent includes all required disclosures
  - [ ] Consent is recorded with timestamp and IP

- [ ] **Cancellation**
  - [ ] Cancellation is self-service (no support required)
  - [ ] Cancellation process is clear and simple
  - [ ] Cancellation stops future charges immediately
  - [ ] User retains access until period end

- [ ] **Transparency**
  - [ ] Subscription terms are publicly accessible
  - [ ] Cancellation instructions are publicly accessible
  - [ ] Privacy policy discloses payment data storage
  - [ ] Pricing is clearly displayed before payment

- [ ] **Technical**
  - [ ] Scheduler checks auto_renew before charging
  - [ ] Consent validation is enforced
  - [ ] Audit trail is complete and immutable
  - [ ] Idempotency is implemented

---

## 9️⃣ Post-Launch Monitoring

### Key Metrics to Track

- **Consent Rate:** % of users who consent vs. abandon
- **Cancellation Rate:** % of subscriptions canceled per month
- **Cancellation Reasons:** Distribution of reasons (price, features, etc.)
- **Failed Payments:** % of recurring payments that fail
- **Reactivation Rate:** % of canceled users who reactivate

### Audit Requirements

- Review consent logs monthly for completeness
- Verify cancellation flow is working correctly
- Monitor customer support tickets for billing issues
- Ensure all public pages remain accessible

### Compliance Reviews

- **Quarterly:** Review consent text for accuracy
- **Annually:** Legal review of all policies and terms
- **As needed:** Update when regulations change

---

## 10️⃣ Risk Mitigation

### Potential Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| User doesn't read consent | Legal liability | Make consent text prominent, clear, and concise |
| User can't find cancellation | Chargebacks | Add cancellation link in emails, billing page, footer |
| Failed payment not retried | Revenue loss | Implement retry logic with 3 attempts |
| Consent not recorded | Compliance issue | Validate consent before payment creation |
| Public pages down | WayForPay rejection | Monitor uptime, use CDN for legal pages |

---

## Appendix A: Code Snippets

### A.1 Frontend: Consent Checkbox Component

```typescript
// components/subscription/ConsentCheckbox.tsx
import React from 'react';
import { useTranslation } from 'react-i18next';

interface ConsentCheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  planName: string;
  amount: number;
  currency: string;
  nextBillingDate: string;
}

export const ConsentCheckbox: React.FC<ConsentCheckboxProps> = ({
  checked,
  onChange,
  planName,
  amount,
  currency,
  nextBillingDate,
}) => {
  const { t } = useTranslation();
  
  return (
    <div className="space-y-3 p-4 border rounded-lg">
      <label className="flex items-start gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="mt-1 w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <div className="flex-1 text-sm">
          <p className="font-medium mb-2">
            {t('subscription.consent.title', 'I agree to subscribe to {{planName}}', { planName })}
          </p>
          <ul className="space-y-1 text-gray-600">
            <li>
              • {t('subscription.consent.tokenization', 
                'My payment card details will be securely tokenized and stored by WayForPay')}
            </li>
            <li>
              • {t('subscription.consent.recurring', 
                'I authorize automatic monthly charges of {{amount}} {{currency}}', 
                { amount, currency })}
            </li>
            <li>
              • {t('subscription.consent.billingDate', 
                'Charges will occur on {{date}} of each month', 
                { date: nextBillingDate })}
            </li>
            <li>
              • {t('subscription.consent.cancellation', 
                'I can cancel my subscription at any time')}
            </li>
          </ul>
          <p className="mt-3 text-xs">
            {t('subscription.consent.agreement', 'I have read and agree to the')}{' '}
            <a 
              href="/legal/terms" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {t('legal.terms', 'Terms of Service')}
            </a>
            {' '}{t('common.and', 'and')}{' '}
            <a 
              href="/legal/subscription-terms" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {t('legal.subscriptionTerms', 'Subscription & Payment Policy')}
            </a>
            .
          </p>
        </div>
      </label>
    </div>
  );
};
```

### A.2 Backend: Consent Validation

```python
# subscription_service/app/utils/consent.py
from typing import Dict
from datetime import datetime
from pydantic import BaseModel

CURRENT_CONSENT_VERSION = "v1.0.0"

class ConsentData(BaseModel):
    consent_given: bool
    consent_version: str
    consent_timestamp: str
    plan_code: str
    amount: str
    currency: str

def validate_consent(metadata: Dict) -> None:
    """Validate that user consent is properly recorded"""
    if not metadata.get('consent_given'):
        raise ValidationError(
            "User consent required for subscription",
            error_code="@subscription_service/CONSENT_REQUIRED"
        )
    
    consent_version = metadata.get('consent_version')
    if consent_version != CURRENT_CONSENT_VERSION:
        raise ValidationError(
            f"Consent version mismatch. Expected {CURRENT_CONSENT_VERSION}, got {consent_version}",
            error_code="@subscription_service/CONSENT_VERSION_MISMATCH"
        )
    
    # Validate timestamp is recent (within last hour)
    consent_timestamp = metadata.get('consent_timestamp')
    if consent_timestamp:
        consent_time = datetime.fromisoformat(consent_timestamp.replace('Z', '+00:00'))
        time_diff = (datetime.now(consent_time.tzinfo) - consent_time).total_seconds()
        
        if time_diff > 3600:  # 1 hour
            raise ValidationError(
                "Consent timestamp is too old",
                error_code="@subscription_service/CONSENT_EXPIRED"
            )
```

### A.3 Backend: Cancellation Logic

```python
# subscription_service/app/services/subscriptions.py
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.models import Subscription
from ..schemas.subscription import CancelSubscriptionRequest
from .events import EventBus

class SubscriptionService:
    def cancel_subscription(
        self, 
        user_id: str, 
        request: CancelSubscriptionRequest,
        ip_address: str,
        db: Session
    ) -> Subscription:
        # Get user's active subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "past_due"])
        ).first()
        
        if not subscription:
            raise NotFoundError("No active subscription found")
        
        # Prevent double cancellation
        if subscription.status == "canceled":
            raise ValidationError("Subscription already canceled")
        
        # Record cancellation metadata
        subscription.auto_renew = False
        subscription.canceled_at = datetime.utcnow()
        subscription.cancellation_reason = request.cancellation_reason
        subscription.cancellation_comment = request.cancellation_comment
        subscription.cancellation_ip_address = ip_address
        
        # Handle immediate vs period-end cancellation
        if request.cancel_immediately:
            subscription.status = "canceled"
            subscription.expires_at = datetime.utcnow()
            
            # Publish event to revoke features
            EventBus.publish_subscription_changed(
                user_id=user_id,
                plan_code="basic",  # Downgrade to free
                status="canceled",
                expires_at="",
                version=1
            )
        else:
            # Keep status active, but prevent renewal
            # expires_at stays as current period end
            pass
        
        db.commit()
        db.refresh(subscription)
        
        # Send cancellation confirmation email
        from ..services.email import send_cancellation_email
        send_cancellation_email(subscription)
        
        return subscription
```

---

## Appendix B: Consent Text Translations

### English (v1.0.0)

```
I agree to subscribe to {plan_name} plan

By subscribing, I confirm that:
• My payment card details will be securely tokenized and stored by WayForPay payment processor
• I authorize automatic monthly charges of {amount} {currency} to my payment card
• Charges will occur on the {day} of each month starting from {start_date}
• I can cancel my subscription at any time from my account settings
• Upon cancellation, no future charges will be made

I have read and agree to the Terms of Service and Subscription & Payment Policy.
```

### Ukrainian (v1.0.0)

```
Я погоджуюся оформити підписку на план {plan_name}

Підписуючись, я підтверджую, що:
• Дані моєї платіжної картки будуть безпечно токенізовані та збережені платіжною системою WayForPay
• Я надаю дозвіл на автоматичне щомісячне списання {amount} {currency} з моєї платіжної картки
• Списання відбуватиметься {day} числа кожного місяця, починаючи з {start_date}
• Я можу скасувати підписку в будь-який час в налаштуваннях мого облікового запису
• Після скасування жодних подальших списань не відбудеться

Я прочитав(-ла) та погоджуюся з Умовами надання послуг та Політикою підписки та оплати.
```

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-28 | System Analyst | Initial specification |

---

## Approval

**Reviewed by:**
- [ ] Legal Counsel
- [ ] Product Manager
- [ ] Engineering Lead
- [ ] Compliance Officer

**Approved by:**
- [ ] CTO / Technical Director
- [ ] CEO / Executive Management

---

**END OF DOCUMENT**
