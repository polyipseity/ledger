---
name: Account Hierarchy & Meanings
description: Complete documentation of all account types (50+) across assets, equity, liabilities, expenses, and revenues with their purposes and meanings.
---

# Account Hierarchy & Meanings

Complete documentation of all account types and their purposes, organized by the five major accounting categories.

## Asset Accounts

Assets represent what you own or are owed.

- **assets:accumulated depreciation**: Contra-asset tracking depreciation of owned objects. Net of this account against objects gives book value.
- **assets:accrued revenues**: Income earned but not yet received (education scholarships, insurance payouts, tutoring fees awaiting collection)
- **assets:banks**: Bank accounts with UUIDs identifying specific institutions and account types (e.g., `assets:banks:<bank-uuid>:HKD savings`)
- **assets:cash**: Physical cash holdings in wallet or at home
- **assets:deferred expenses**: Prepaid expenses (education tuition, accommodations, insurance premiums, cloud service subscriptions)
- **assets:deferred assets:objects**: Objects purchased but not yet put into use or activated
- **assets:digital**: Digital payment accounts including:
  - Octopus cards (public transportation/retail payment cards)
  - Stripe (online payment processor accounts)
  - Game Zone (arcade/gaming venue accounts)
  - University accounts (campus meal plans, library, etc.)
- **assets:loans**: Money lent to friends/clients with balance assertions tracking what's owed back
- **assets:objects**: Physical owned items with depreciation tracking:
  - Clothing (apparel and accessories)
  - Consumer electronics (devices, accessories)
  - Tools (equipment, devices)
  - Decorations (non-essential items)
- **assets:special:rewards**: Loyalty points and vouchers:
  - Store rewards (store-specific loyalty programs)
  - Credit card points (accumulated from card usage)
  - Club points/e-currency (membership program points)
- **assets:trusts**: Trust or retirement accounts (retirement master trust accounts identified by account numbers)

## Equity Accounts

Equity represents ownership or net worth components.

- **equity:conversions**: Currency and point conversion tracking with rate metadata. Each conversion pair (e.g., HKD-USD, HKD-_PT/D) has dual-side accounts to track rates and balances.
- **equity:external:self.alternatives**: Links to alternative scenario tracking when using separate alternatives journal. Maintains connection between main and alternatives journals.
- **equity:friends**: Informal debts and credits with friends (money borrowed from/lent to friends, shared expenses)
- **equity:kins**: Family-related equity including:
  - Special gifts from family members
  - Family member-specific sub-accounts
  - Family financial arrangements
- **equity:organizations**: Institutional relationships (e.g., university as equity holder for scholarship relationships)
- **equity:unaccounted**: Balancing account for reconciliation differences. When totals don't balance, differences are placed here temporarily.
- **equity:opening/closing balances**: Monthly journal boundary transactions that mark the transition between months
- **equity:unknown**: Unidentified transaction counterparties when source/destination isn't clear

## Liability Accounts

Liabilities represent what you owe.

- **liabilities:accrued expenses**: Expenses incurred but not yet paid:
  - Insurance premiums (health, life, liability)
  - Utility levies or surcharges
  - Internet/telecom service bills
- **liabilities:credit cards**: Credit card balances with UUID identifiers for specific cards. Tracks amount owed to card issuers.
- **liabilities:deferred revenues**: Income received but not yet earned (e.g., prepaid services, advance payments)
- **liabilities:loans**: Money borrowed from friends or colleagues with balance assertions tracking repayment status

## Expense Accounts

Expenses represent money spent.

- **expenses:depreciation**: Periodic depreciation entries for owned assets (opposite side of assets:accumulated depreciation)
- **expenses:education**: Education-related spending:
  - Books (textbooks, reference books)
  - Tuition (course fees, enrollment fees)
  - Incidental (school supplies, exam fees)
- **expenses:fees**: Various fees:
  - Banking fees (account maintenance, transaction fees)
  - Payment processing fees (currency conversion, payment system fees)
  - Government fees (application, registration)
  - Transit system fees (fare cards, special charges)
- **expenses:food and drinks**: Food and beverage spending:
  - Dining (restaurant meals, takeout)
  - Drinks (beverages at establishments)
  - Fruits (produce purchases)
  - Snacks (packaged food items)
  - Use detailed `food_or_drink:` tags for specific items
- **expenses:gaming**: Gaming/entertainment:
  - Arcade games (maimai, other rhythm games)
  - Gaming venues
- **expenses:healthcare**: Medical spending:
  - Medication (prescription, over-the-counter)
  - Medical services (doctor visits, treatments)
- **expenses:insurances**: Insurance spending:
  - Health insurance premiums
  - Life insurance premiums
  - Levy insurance or surcharges
- **expenses:services**: Service spending:
  - Cloud storage (Apple iCloud, Google Drive)
  - Internet (ISP, broadband)
  - Photography (printing, editing services)
  - Support/warranty (AppleCare+, extended warranties)
- **expenses:transport**: Transportation spending:
  - Buses (public bus transit)
  - Trains (MTR, high-speed rail)
  - Ferries (water transport)
  - Light rail (LRT systems)
  - Minibuses (public minibus)
  - Taxis (licensed taxis)
  - Trams (electric trams)
  - Airplanes (flights)
- **expenses:writeoffs**: Removing items from books:
  - Expired vouchers (no longer redeemable)
  - Lost items (items no longer recoverable)

## Revenue Accounts

Revenues represent money earned.

- **revenues:donations**: Money received as donations:
  - GitHub Sponsors (sponsorship donations)
  - Buy Me a Coffee (crowdfunding tips)
- **revenues:education:scholarships**: Academic scholarships with reward identifiers tracking award sources
- **revenues:incomes**: General income:
  - Tutoring (private teaching)
  - Work (employment, freelance)
  - Bonuses (performance bonuses, special bonuses)
  - Education (teaching assistant, educational work)
- **revenues:insurances:life**: Life insurance payouts and dividends
- **revenues:interests**: Interest income:
  - Bank interest (savings account interest)
  - Investment interest
- **revenues:rewards**: Loyalty program rewards:
  - Credit card points (converted to cash/statement credit)
  - Store loyalty rewards
  - Competition prizes (contest winnings)

## Account ID Format

Many accounts use UUIDs as identifiers:

- **Purpose**: Maintain privacy by separating account identifiers from confidential details
- **Mapping**: See `private.yaml` (encrypted as `private.yaml.gpg`) for UUID → confidential string mappings
- **Example**: `assets:banks:<bank-uuid>` resolves to actual bank name through private mapping
- **Usage**: UUIDs appear consistently as payees and account identifiers throughout journals
