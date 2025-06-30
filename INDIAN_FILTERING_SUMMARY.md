# Indian Project Filtering Implementation

## Overview

The AutoWork Minimal Bot has been enhanced with specific filtering for Indian (INR) projects that targets:

- **Minimum budget**: ₹15,000 INR
- **Client requirements**: Only clients WITHOUT payment verification
- **Deposit status**: Only clients WITHOUT deposits made
- **Payment method**: Only clients WITHOUT payment methods verified

## Configuration Changes

### Updated `bot_config.json`

```json
{
  "currency_filtering": {
    "enabled": true,
    "inr_pkr_strict_filtering": true,
    "inr_minimum_budget": 15000.0,
    "pkr_minimum_budget": 69500.0,
    "require_payment_verified_for_inr_pkr": false,
    "require_identity_verified_for_inr_pkr": false,
    "skip_phone_email_only_for_inr_pkr": false,
    "indian_project_filters": {
      "enabled": true,
      "min_inr_budget": 15000.0,
      "skip_payment_verified_clients": true,
      "skip_deposit_made_clients": true,
      "require_no_payment_method": true,
      "log_filtered_projects": true
    }
  }
}
```

## Key Features

### 1. Budget Filtering
- **Minimum budget**: ₹15,000 INR (reduced from ₹20,000)
- **Currency detection**: Automatically detects INR projects
- **Budget validation**: Ensures projects meet minimum requirements

### 2. Client Filtering
- **Payment verification**: Skips clients with payment verification
- **Deposit status**: Skips clients who have made deposits
- **Payment method**: Skips clients with verified payment methods
- **Rating threshold**: Very low rating threshold (3.0) for safety

### 3. Logging and Tracking
- **Detailed logging**: Logs all filtered projects with reasons
- **Statistics tracking**: Tracks Indian project filtering statistics
- **Performance monitoring**: Monitors filter effectiveness

## Implementation Details

### New Methods Added

#### `analyze_client_for_inr_pkr(employer_id)`
- **Purpose**: Special client analysis for INR projects
- **Logic**: Targets clients WITHOUT payment verification/deposits/methods
- **Returns**: Client suitability analysis with detailed reasons

#### `should_bid_on_indian_project(project)`
- **Purpose**: Special filtering for Indian projects
- **Checks**: Budget requirements and client suitability
- **Logging**: Detailed logging of filtered projects

### Integration Points

The Indian filtering is integrated into the main filtering pipeline:

1. **Currency detection**: Identifies INR projects
2. **Budget validation**: Ensures ₹15,000+ minimum
3. **Client analysis**: Checks for unverified clients
4. **Logging**: Records all filtering decisions

## Filtering Logic

### For INR Projects:
```
IF currency == 'INR':
    IF budget < ₹15,000:
        REJECT: "Budget too low"
    
    IF client.payment_verified == True:
        REJECT: "Payment verified (we want unverified clients)"
    
    IF client.deposit_made == True:
        REJECT: "Deposit made (we want clients without deposits)"
    
    IF client.payment_method_verified == True:
        REJECT: "Payment method verified (we want clients without payment methods)"
    
    IF client.rating < 3.0:
        REJECT: "Very low rating"
    
    ACCEPT: "Suitable for INR project"
```

### For Non-INR Projects:
- Normal filtering applies
- No special Indian project restrictions

## Usage

### Running the Bot
```bash
# Set your token
export FREELANCER_OAUTH_TOKEN="your_token_here"

# Run the bot
python autowork_minimal.py
```

### Monitoring Indian Projects
The bot will log Indian project activity:

```
🇮🇳 INR Project Filtered: Project Title... - Budget too low (₹5000 < ₹15000)
🇮🇳 INR Project Filtered: Project Title... - Client not suitable: Payment verified
🇮🇳 INR Project Approved: Project Title... - Indian project passed all filters
```

## Statistics Tracking

The bot tracks Indian project filtering statistics:

- `indian_filtered`: Number of INR projects filtered out
- Detailed reasons for each filtered project
- Success rate of Indian project bids

## Safety Features

1. **Rating threshold**: Minimum 3.0 rating for safety
2. **Budget minimum**: Ensures profitable projects only
3. **Detailed logging**: Full transparency of filtering decisions
4. **Error handling**: Graceful handling of API errors

## Configuration Options

### Enable/Disable
```json
"indian_project_filters": {
  "enabled": true  // Set to false to disable
}
```

### Adjust Budget
```json
"min_inr_budget": 15000.0  // Change minimum budget
```

### Modify Client Requirements
```json
"skip_payment_verified_clients": true,    // Skip verified clients
"skip_deposit_made_clients": true,        // Skip clients with deposits
"require_no_payment_method": true         // Skip clients with payment methods
```

### Logging Control
```json
"log_filtered_projects": true  // Enable/disable detailed logging
```

## Benefits

1. **Targeted filtering**: Focuses on specific Indian project requirements
2. **Risk management**: Avoids clients with payment verification
3. **Profit optimization**: Ensures minimum profitable budgets
4. **Transparency**: Full logging of all decisions
5. **Flexibility**: Easy configuration adjustments

## Testing

To test the Indian filtering:

```bash
# Run the main test suite
python test_minimal_bot.py

# Check configuration
python -c "import json; config = json.load(open('bot_config.json')); print('Indian filters:', config['currency_filtering']['indian_project_filters'])"
```

The bot is now configured to specifically target Indian projects with ₹15,000+ budgets and clients without payment verification, deposits, or payment methods! 