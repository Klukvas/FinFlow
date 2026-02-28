# Bank Integrations Roadmap

## Current: Monobank (Ukraine)

**Status:** Implemented  
**Auth:** Personal token (X-Token header)  
**API:** api.monobank.ua — client info, statements, webhook  
**Coverage:** ~40% of Ukrainian users  

## Planned: PrivatBank (Ukraine)

**Status:** Planned  
**Auth:** Merchant signature (Autoclient API) — more complex than Monobank  
**API:** api.privatbank.ua — statements, balances  
**Coverage:** Monobank + PrivatBank = ~80% of Ukrainian users  
**Effort:** Medium — new client, mapper, different auth flow  

## Planned: Enable Banking (EU — 31 country)

**Status:** Planned (for EU market expansion)  
**Auth:** OAuth-like flow — redirect user to bank → callback with code → session → accounts/transactions  
**API:** REST, JWT RS256, accounts, balances, transactions with pagination  
**Coverage:** 2500+ banks in 31 EU/EEA countries (AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, GR, HU, IS, IE, IT, LV, LI, LT, LU, MT, NL, NO, PL, PT, RO, SK, SI, ES, SE)  
**Ukraine:** Not supported  
**Sandbox:** Free  
**Docs:** https://enablebanking.com/docs/api/reference/  
**Note:** Replacement for Nordigen/GoCardless which closed free tier registration in September 2025  

## Architecture

The `bank_sync_service` is designed for multi-bank support:
- `BankConnection.bank_type` field distinguishes providers (`monobank`, `privatbank`, `enable_banking`)
- Each provider has its own client module (`monobank_client.py`, etc.)
- `TransactionMapper` converts provider-specific formats to FinFlow expenses/incomes
- Deduplication via `synced_transactions.external_transaction_id`

## Alternatives Considered

| Provider | Coverage | Pricing | Status |
|----------|----------|---------|--------|
| Nordigen/GoCardless | 2400+ EU banks | Was free | Closed to new users (Sep 2025) |
| Enable Banking | 2500+ EU banks (31 countries) | Free sandbox, paid production | Recommended for EU |
| Plaid | US, CA, UK, EU | From $0.30/connection | Too expensive for MVP |
| Salt Edge | 5000+ global | Paid | Enterprise-oriented |
| Tink | 6000+ EU banks | Paid | Enterprise-oriented |
| TrueLayer | 3000+ EU banks | Paid | UK-focused |
