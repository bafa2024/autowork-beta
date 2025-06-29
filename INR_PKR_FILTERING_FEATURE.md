# INR/PKR Currency Filtering Feature

## Overview

The AutoWorkMinimal bot now includes enhanced filtering for projects with INR (Indian Rupee) and PKR (Pakistani Rupee) currencies. This feature implements stricter requirements for these currencies to ensure higher quality projects and better client verification.

## Key Features

### 1. Higher Minimum Budget Requirements

**INR Projects:**
- Fixed projects: Minimum ₹16,000 (instead of ₹20,000)
- Hourly projects: Minimum ₹1,600 (instead of ₹1,600)

**PKR Projects:**
- Fixed projects: Minimum ₨55,600 (instead of ₨69,500)
- Hourly projects: Minimum ₨5,560 (instead of ₨5,560)

### 2. Stricter Client Verification

For INR and PKR projects, the bot requires:

- **Payment Method Verification**: Client must have verified payment methods
- **Identity Verification**: Client must have completed identity verification
- **Skip Phone/Email Only**: Projects from clients with only phone/email verification are automatically skipped

### 3. Separate Tracking

The bot now tracks INR/PKR filtering separately:
- `inr_pkr_low_budget`: Projects rejected due to low budget in INR/PKR
- `inr_pkr_client_verification_failed`: Projects rejected due to insufficient client verification for INR/PKR

## Configuration

The feature is controlled by the `currency_filtering` section in `bot_config.json`:

```json
{
  "currency_filtering": {
    "enabled": true,
    "inr_pkr_strict_filtering": true,
    "inr_minimum_budget": 16000.0,
    "pkr_minimum_budget": 55600.0,
    "require_payment_verified_for_inr_pkr": true,
    "require_identity_verified_for_inr_pkr": true,
    "skip_phone_email_only_for_inr_pkr": true
  }
}
```

### Configuration Options

- `enabled`: Enable/disable currency filtering
- `inr_pkr_strict_filtering`: Enable strict filtering for INR/PKR currencies
- `inr_minimum_budget`: Minimum budget for INR projects (₹16,000)
- `pkr_minimum_budget`: Minimum budget for PKR projects (₨55,600)
- `require_payment_verified_for_inr_pkr`: Require payment verification for INR/PKR projects
- `require_identity_verified_for_inr_pkr`: Require identity verification for INR/PKR projects
- `skip_phone_email_only_for_inr_pkr`: Skip projects from clients with only phone/email verification

## Implementation Details

### 1. Enhanced Budget Checking

The `get_minimum_budget_for_currency()` method now checks for custom INR/PKR minimums from the configuration before falling back to default values.

### 2. Strict Client Analysis

A new method `analyze_client_for_inr_pkr()` performs stricter verification checks specifically for INR/PKR projects:

- Payment method verification (REQUIRED)
- Identity verification (REQUIRED)
- Skip clients with only phone/email verification

### 3. Project Filtering Logic

The `should_bid_on_project()` method now:

1. Detects INR/PKR currencies
2. Applies strict client verification if enabled
3. Uses higher minimum budget thresholds
4. Tracks rejections separately for analytics

## Testing

A comprehensive test script `test_inr_pkr_filtering.py` validates:

- Minimum budget thresholds for different currencies
- Project rejection for low budgets
- Client verification requirements
- Configuration loading
- Skip statistics tracking

### Test Results

The test script confirms:
- ✅ INR projects below ₹16,000 are rejected
- ✅ PKR projects below ₨55,600 are rejected
- ✅ Strict client verification is applied for INR/PKR projects
- ✅ Separate tracking for INR/PKR rejections
- ✅ Configuration is loaded correctly

## Benefits

1. **Higher Quality Projects**: Higher minimum budgets filter out low-value projects
2. **Better Client Verification**: Ensures clients have proper payment and identity verification
3. **Reduced Risk**: Avoids projects from unverified clients
4. **Better Analytics**: Separate tracking provides insights into INR/PKR project filtering
5. **Configurable**: All thresholds and requirements can be adjusted via configuration

## Usage

The feature is automatically enabled when:
1. `currency_filtering.enabled` is set to `true`
2. `currency_filtering.inr_pkr_strict_filtering` is set to `true`

The bot will automatically apply stricter filtering to any project with INR or PKR currency, requiring:
- Higher minimum budgets
- Payment method verification
- Identity verification
- Skip phone/email only clients

## Monitoring

The bot tracks INR/PKR filtering statistics in the `skipped_projects` dictionary:
- `inr_pkr_low_budget`: Count of INR/PKR projects rejected for low budget
- `inr_pkr_client_verification_failed`: Count of INR/PKR projects rejected for client verification

These statistics are included in performance analytics and can be monitored via Redis or logs.

## Future Enhancements

Potential improvements could include:
- Currency-specific quality scoring
- Dynamic minimum budget adjustment based on market conditions
- Additional verification requirements for specific currencies
- Currency-specific bid message templates
- Currency-specific delivery time adjustments 