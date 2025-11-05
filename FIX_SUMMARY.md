# Critical Fixes - November 4, 2025

## Issues Identified

### 1. ❌ **Timezone Issue - Pre-market Scan Running at Wrong Time**
**Problem:** Scan runs at 8:30 AM EST (7:30 AM CST) instead of 8:30 AM CST (9:30 AM EST)
**Impact:** Scan runs 1 hour before market open instead of at market open
**Root Cause:** Config uses ET timezone, but user is in CST

### 2. ❌ **Scoring Weights Showing Zero**
**Problem:** All scores show as 0.0, reasoning is incorrect
**Impact:** Cannot properly rank tickers, all appear equal
**Root Cause:** Need to verify weights are being applied correctly in weighted_score function

### 3. ❌ **Options Data Format Error from Alpaca**
**Problem:** Getting format errors when fetching options data
**Impact:** Cannot get option chains, IV rank, open interest
**Root Cause:** Alpaca API response format may have changed or date format issue

## Solutions

### Fix 1: Timezone Configuration
**Change:** Update config to allow timezone selection
**Implementation:**
- Add `timezone` setting to config
- Convert scan time from user's timezone to ET
- Update all scheduling to respect user timezone

### Fix 2: Scoring Weights
**Change:** Ensure weights are normalized and applied correctly
**Implementation:**
- Verify weights sum to 1.0 or normalize them
- Add debug logging to show individual metric contributions
- Ensure metrics are properly scaled (0-100)

### Fix 3: Options Data Fetching
**Change:** Update options API calls to handle new format
**Implementation:**
- Fix date format in GetOptionContractsRequest
- Add better error handling
- Fall back to REST API if trading client fails
- Add retry logic

## Testing Checklist

- [ ] Scan runs at correct time (8:30 AM CST = 9:30 AM EST)
- [ ] Scores are non-zero and properly calculated
- [ ] Reasoning shows correct weight contributions
- [ ] Options data fetches successfully
- [ ] IV rank calculates correctly
- [ ] Discord notifications show proper data
