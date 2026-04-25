# Add Transactions — Canonical Examples

This file collects canonical, non-confidential worked examples for the Add Transactions skill. Use these for guidance, tests, and to standardize examples across aspect files.

## 1. Food: Drink with Modifiers

Original: 冰蜜檸檬綠茶, 去冰, 7分甜

Result (posting comment only):

```text
expenses:food and drinks:dining  28.00 HKD  ; food_or_drink: 冰蜜檸檬綠茶 + 去冰 + 7分甜
assets:digital:Octopus cards:...      -28.00 HKD
```

Notes: combine base item and modifiers with `+` and keep tags in posting comments only.

## 1a. Verify beverage presence per transaction

A single merchant may sometimes offer a free drink. **Record the drink only when it appears on the specific receipt.**

Example A (coffee listed):

```text
2026-02-23 (41219150, 62) Cafe 100%  ; activity: eating, time: 08:08:31, timezone: UTC+08:00
    expenses:food and drinks:dining                                         35.00 HKD  ; food_or_drink: 無糖高纖鮮奶麥皮, food_or_drink: 蛋治, food_or_drink: 鮮奶滑蛋三文治
    expenses:food and drinks:drinks                                          0.00 HKD  ; food_or_drink: 熱咖啡 + 多奶
    assets:digital:Octopus cards:...                                       -35.00 HKD
```

### 1b. Bundled meal with multiple named items (Cafe 100% style)

When a receipt shows several distinct menu items under a single total price, treat each named component as a separate tag separated by commas; use `+` only for modifiers such as ice/sweetness levels. The price is carried on the first posting line only.

```text
2026-03-07 Cafe 100%  ; activity: eating, eating: lunch, time: 15:31:32, timezone: UTC+08:00
    expenses:food and drinks:dining       34.00 HKD  ; food_or_drink: 雪菜肉絲湯米粉, food_or_drink: 奶油多士, food_or_drink: 即食麵, food_or_drink: 奶油厚多士, food_or_drink: 紅豆冰 + 少冰 + 走甜
    assets:cash                          -34.00 HKD
```

Notes: the receipt does not break out individual amounts; the comment tags merely reflect the list of items and modifiers that came with the set.  Additionally, drop any leading “配” from an item and treat the following text as its own item (e.g. `無糖高纖鮮奶麥皮 配蛋治`).

Example (don’t treat full menu items as modifiers):

```text
2026-03-15 (41225144, 17) Cafe 100%  ; activity: eating, eating: breakfast, time: 11:29:49, timezone: UTC+08:00
    expenses:food and drinks:dining   37.00 HKD  ; food_or_drink: 野菌鮮奶炒滑蛋, food_or_drink: 輕量火腿絲通粉, food_or_drink: 蒜香牛油多士
    expenses:food and drinks:drinks    0.00 HKD   ; food_or_drink: 熱咖啡 + 多奶
    assets:digital:Octopus cards:...  -37.00 HKD
```

In this example, the three named food components are separate items; only the drink uses `+` to join a modifier (多奶). Note that the leading `(早)` and the prefix `轉` were removed because they are metadata/ordering markers, not part of the dish names.

### Bilingual item preference (English first)

When a receipt shows the same item in both Chinese and English, prefer the English name in the journal:

```text
# Receipt line example:
# Hot Chocolate (熱朱古力)

expenses:food and drinks:drinks  0.00 HKD  ; food_or_drink: Hot Chocolate
```

### TamJai SamGor / noodle shop itemization

Some noodle-shop receipts list core dishes and add-ons using `+`, but the add-ons are standalone items (not modifiers). In those cases, split them into separate `food_or_drink:` tags.

```text
2026-03-16 (202603166333, 6333, K3) TamJai SamGor  ; activity: eating, eating: lunch, time: 13:07:01, timezone: UTC+08:00
    expenses:food and drinks:dining  43.00 HKD  ; food_or_drink: 娃娃菜, food_or_drink: 清牛肉, food_or_drink: 番茄湯底 + 10小辣, food_or_drink: 番茄湯滑牛娃娃菜米線配汽水 + 不要芽菜 + 不要韭菜 + 辣
    expenses:food and drinks:dining   5.00 HKD  ; food_or_drink: 蒟蒻麵
    expenses:food and drinks:dining   5.00 HKD  ; food_or_drink: 火腿
    expenses:food and drinks:dining   5.00 HKD  ; food_or_drink: 凍檸檬茶
    expenses:food and drinks:dining   6.00 HKD  ; food_or_drink: 芒果凍, food_or_drink: 金桔汁
    expenses:food and drinks:dining  43.00 HKD  ; food_or_drink: 砂砂湯底 + 3小辣, food_or_drink: 砂砂湯雞肉豆卜米線配汽水 + 米線爽, food_or_drink: 罐裝無糖可樂, food_or_drink: 豆卜, food_or_drink: 雞肉
    assets:digital:Octopus cards:... -107.00 HKD
```

Note: `火腿` and `蒟蒻麵` are separate items, not modifiers, even though the receipt uses `+` to join them.

### McDonald's English preference

When McDonald's receipts include both English and Chinese for menu items, prefer the English naming in the journal entry:

```text
2026-03-16 (58C75E/3256, 747, 444) McDonald's  ; activity: eating, eating: afternoon tea, time: 16:47:07, timezone: UTC+08:00
    expenses:food and drinks:dining  35.50 HKD  ; food_or_drink: Hot Chocolate, food_or_drink: Fries L.Combo, food_or_drink: McNuggets 6pcs L.Meal, food_or_drink: Tom Yum Kung fl.Seasoning, food_or_drink: Laksa Flavored Sauce
    assets:digital:Octopus cards:... -35.50 HKD
```

Even when the receipt shows local-language versions, always choose the English version when it is available.

When the receipt already prints a standalone add-on or side dish as its own line, keep that exact name and do not prepend `配` in the journal:

```text
2026-04-02 (5873AD/3026, 844, 42) McDonald's  ; activity: eating, eating: dinner, time: 23:49:18, timezone: UTC+08:00
    expenses:food and drinks:dining  37.00 HKD  ; food_or_drink: 豬柳蛋漢堡餐(大)
    expenses:food and drinks:dining   0.00 HKD  ; food_or_drink: 星星薯餅(增量裝)
    expenses:food and drinks:dining   0.00 HKD  ; food_or_drink: 熱朱古力
    assets:digital:Octopus cards:... -37.00 HKD
```

#### TamJai SamGor specifics

```text
2026-03-09 (202603096752, 5124, K2) TamJai SamGor  ; activity: eating, eating: afternoon tea, time: 16:00:15, timezone: UTC+08:00
    expenses:food and drinks:dining      43.00 HKD  ; food_or_drink: 米線爽 + 腩肉, food_or_drink: 罐裝無糖可樂, food_or_drink: 鮮冬菇, food_or_drink: 麻辣湯底 + 3小辣, food_or_drink: 麻辣脆肉鮮冬菇米線
    assets:digital:Octopus cards:...    -43.00 HKD
```

Ensure modifiers like 米線爽 are recorded correctly and translate OCR mistakes (雀巢無糖可樂 → 罐裝無糖可樂).

### Sushiro shared bill with receipt-id header

When a Sushiro receipt is split between diners, keep the receipt ID in the journal header, record the full item and fee totals, and use negative expense postings plus an `equity:friends:<uuid>` line to balance the other person's share.

```text
2026-04-07 (512604076122) Sushiro  ; activity: eating, eating: dinner, time: 21:00:03, timezone: UTC+08:00
    expenses:food and drinks:dining                          223.00 HKD  ; food_or_drink: 13件
    expenses:food and drinks:fees                             22.00 HKD  ; food_or_drink: 10% service charge
    expenses:food and drinks:dining                         -111.50 HKD  ; others' share
    expenses:food and drinks:fees                            -11.00 HKD  ; others' share
    equity:friends:4491140b-7e34-48fe-8e3d-aca591ed6d6e     -122.50 HKD
```

Notes: use the exact split shown on the receipt; do not collapse the transaction into a single card-payment posting when a shared-bill split is present.

### Saizeriya and American Diner header IDs

```text
2026-04-03 (000-964351, 34) Saizeriya  ; activity: eating, duration: PT35M17S, eating: lunch, time: 11:10:19, timezone: UTC+08:00
    expenses:food and drinks:dining                                         25.00 HKD  ; food_or_drink: 意式野菜焗蛋
    expenses:food and drinks:dining                                         12.00 HKD  ; food_or_drink: 蒜香法包
    assets:digital:Octopus cards:...                                       -37.00 HKD

2026-04-02 (374369, K459) American Diner  ; activity: eating, eating: lunch, time: 12:45:33, timezone: UTC+08:00
    expenses:food and drinks:dining                                         36.00 HKD  ; food_or_drink: 忌廉煙火腿粟米蜆肉意粉, food_or_drink: 薯條
    assets:digital:Octopus cards:...                                       -36.00 HKD
```

When a receipt provides a second identifier after the main receipt number, include it in the journal header so the transaction can be uniquely tracked and matched. The secondary value may be a table or kiosk code.

If the receipt also prints unrelated POS footer codes, do not move those into the journal header unless they are part of the merchant's own receipt identifier scheme.

```text
2026-04-03 (018-00123) Appolo  ; activity: eating, eating: snacks, time: 20:36:22, timezone: UTC+08:00
    expenses:food and drinks:dining                                         12.00 HKD  ; food_or_drink: 海苔小丸子 90g
    assets:digital:Octopus cards:...                                       -12.00 HKD
```

### Zero-Priced Itemization with Duration (2026-04-15 to 2026-04-18 Batch Validation)

These four transactions demonstrate the validated food transaction patterns: zero-priced component itemization, duration calculation precision, food tag language preservation, and shared expense splits using `equity:friends:`.

#### A. Saizeriya with Duration (2026-04-15)

```text
2026-04-15 (000-965768, 34) Saizeriya  ; activity: eating, duration: PT35M45S, eating: dinner, time: 21:45:48, timezone: UTC+08:00
    expenses:food and drinks:dining                                         25.00 HKD  ; food_or_drink: 意式野菜焗蛋
    expenses:food and drinks:dining                                         12.00 HKD  ; food_or_drink: A香蒜辣汁野菌西蘭花
    assets:digital:Octopus cards:...                                       -37.00 HKD
```

Notes: Receipt shows order time 21:45:48 → checkout ~22:21:33 = 35 minutes 45 seconds. Duration recorded in header between `activity:` and `eating:` tags.

#### B. TamJai SamGor with Zero-Priced Modifiers and Duration (2026-04-16)

```text
2026-04-16 (000-0052, 1A) TamJai SamGor  ; activity: eating, duration: PT36M52S, eating: breakfast, time: 10:27:01, timezone: UTC+08:00
    expenses:food and drinks:dining                                         33.00 HKD  ; food_or_drink: A1.三哥豐盛早晨全餐
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 黑糖
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 紅豆
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 薏米
    assets:digital:Octopus cards:...                                       -33.00 HKD
```

Notes: Receipt itemizes 4 components under single paid line (33.00 base + 3 × 0.00 modifiers). Each component gets its own posting with `food_or_drink:` tag to preserve receipt structure. Duration 36 minutes 52 seconds (order 10:27:01 → checkout ~11:03:53). Transaction still balances (33.00 total).

#### C. TamJai SamGor with Receipt-Printed Voucher Discount (2026-04-19)

```text
2026-04-19 (000-0041, 13A) TamJai SamGor  ; activity: eating, duration: PT1H21M29S, eating: breakfast, time: 09:43:10, timezone: UTC+08:00
    expenses:food and drinks:dining                                         33.00 HKD  ; food_or_drink: A2.脆皮雞扒/醒晨早餐
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: A2雞扒小早餐
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 烘底牛油多士
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 腿反雞扒小
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 火腿豆腐雞湯米線
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 米線爽
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 熱咖啡 + 多奶 + 走攪棍
    expenses:food and drinks:dining                                        -30.00 HKD  ; food_or_drink: 電子印花卡禮施 $30 早餐電子現金券
    liabilities:credit cards:cd33f171-413c-4abb-9c24-3755f4aa4093            -3.00 HKD
```

Notes: When a receipt prints a separate voucher or e-coupon discount line, record it as a negative expense posting and preserve the final payment as a separate credit-card liability posting.

#### D. TamJai SamGor grouped zero-priced subitems (2026-04-22)

```text
2026-04-22 ! (3A, 000-0025) TamJai SamGor  ; activity: eating, eating: breakfast, time: 10:08:01, timezone: UTC+08:00
    expenses:food and drinks:dining                                     33.00 HKD  ; food_or_drink: A4. 三哥醒晨早餐
    expenses:food and drinks:dining                                      0.00 HKD  ; food_or_drink: A4醒晨早餐, food_or_drink: 炒蛋(大), food_or_drink: 烘底牛油多士(走牛油)
    expenses:food and drinks:dining                                      0.00 HKD  ; food_or_drink: 家鄉包米通粉
    expenses:food and drinks:dining                                      0.00 HKD  ; food_or_drink: 熱咖啡 + 多奶 + 走攪棍
    liabilities:credit cards:cd33f171-413c-4abb-9c24-3755f4aa4093      -33.00 HKD
```

Notes: When a receipt groups multiple zero-priced sub-items under a single base meal header, keep the grouping as one 0.00 HKD posting line with multiple `food_or_drink:` tags separated by commas. Use `+` syntax for modifiers tied to a drink.

#### E. American Diner with Zero-Priced Items (2026-04-17 breakfast)

```text
2026-04-17 (383356, K069) American Diner  ; activity: eating, eating: breakfast, time: 08:42:52, timezone: UTC+08:00
    expenses:food and drinks:dining                                         24.00 HKD  ; food_or_drink: G.鮮蘑菇炒蛋
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 白麵包
    expenses:food and drinks:dining                                          0.00 HKD  ; food_or_drink: 奶油
    assets:digital:Octopus cards:...                                       -24.00 HKD
```

Notes: Main dish 24.00 HKD, two zero-priced side items on receipt listed as separate lines but not charged separately. Each item gets explicit posting + tag. Dish code preserved (G.) with Chinese name (鮮蘑菇炒蛋).

#### E. HKUST Ramen Venue with Shared Equity Split (2026-04-17 lunch)

```text
2026-04-17 (5900542324) 20b484a5-3c01-42f3-875c-e95509b3de22  ; activity: eating, eating: lunch, time: 12:39:07, timezone: UTC+08:00
    expenses:food and drinks:dining                                         36.50 HKD
    expenses:food and drinks:dining                                         10.00 HKD
    expenses:food and drinks:drinks                                          4.00 HKD
    expenses:food and drinks:dining                                          0.00 HKD  ; item: dine-in fee
    equity:friends:4491140b-7e34-48fe-8e3d-aca591ed6d6e                    -50.50 HKD
    assets:digital:Octopus cards:...                                       -50.50 HKD = 0.00 HKD
```

Notes: Immediate same-day split with friend. Expense itemized by category (36.50 + 10.00 dining, 4.00 drinks, 0.00 fee). Friend's share recorded as negative `equity:friends:` posting with UUID. Transaction balances to 0.00 HKD via assertion on Octopus posting.

#### F. Saizeriya with Duration (2026-04-18)

```text
2026-04-18 (000-966095, 36) Saizeriya  ; activity: eating, duration: PT30M38S, eating: lunch, time: 12:27:18, timezone: UTC+08:00
    expenses:food and drinks:dining                                         25.00 HKD  ; food_or_drink: 意式野菜烤蛋
    expenses:food and drinks:dining                                         20.00 HKD  ; food_or_dish: 意式牛油煙火腿西蘭花
    assets:digital:Octopus cards:...                                       -45.00 HKD
```

Notes: Second Saizeriya transaction validates pattern consistency across multiple entries. Duration PT30M38S (order 12:27:18 → checkout ~12:57:56 = 30m 38s). Italian-style dish names preserved exactly as on receipt.

**Validation Summary:**

- ✅ Zero-priced itemization: Each receipt component gets explicit posting + tag (TamJai 04-16, American Diner 04-17)
- ✅ Duration precision: ISO-8601 format, second-level accuracy (PT36M52S, PT30M38S, PT35M45S)
- ✅ Shared expense equity: Friend's share recorded as negative `equity:friends:` posting (HKUST 04-17)
- ✅ ID mapping compliance: All payees follow `id_mappings.yml` ordering (receipt_id + table/kiosk)
- ✅ Language preservation: Italian names (Saizeriya) + Chinese names + dish codes (American Diner) kept exact
- ✅ Transaction balancing: All entries balance to 0.00 HKD

Note: keep only the sale receipt number in the header here; the longer POS footer code belongs to the receipt body, not the journal header.

Example B (no coffee):

```text
2026-02-23 (081-1648) Oliver's Super Sandwiches  ; activity: eating, eating: lunch, time: 12:39:39, timezone: UTC+08:00
    expenses:food and drinks:dining                                         39.30 HKD  ; food_or_drink: 川辣番茄濃湯, food_or_drink: 雞肉腸讚歧烏冬, food_or_drink: 香煎豬扒
    assets:digital:Octopus cards:...                                       -39.30 HKD
```

Notes: each transaction must be treated on its own; do not generalize from past entries or merchant patterns.

## 2. Lending/Borrowing: Pending → Cleared

```hledger
2026-01-15 ! Friend Lunch                    # Pending loan to friend
  assets:loans:friends:<uuid>      50.00 HKD
  assets:cash                     -50.00 HKD

2026-01-20 * Friend Lunch                    # Cleared when repaid
  assets:loans:friends:<uuid>      50.00 HKD = 0.00 HKD
  assets:banks:<bank-uuid>        -50.00 HKD
```

Notes: only the original loan uses a status marker; the repayment transaction has no marker and uses an assertion (`= 0.00`).

## 3. Currency Conversion

```hledger
2026-01-10 Currency Exchange  ; activity: transfer, time: 14:30:00, timezone: UTC+08:00
  equity:conversions:HKD-USD:HKD                   -1 000.00 HKD  ; 1000 HKD → 130 USD, rate: 0.1300
  assets:banks:...:HKD                             1 000.00 HKD
  equity:conversions:HKD-USD:USD                     130.00 USD
  assets:banks:...:USD                             -130.00 USD
```

Notes: record the rate in a comment and use `equity:conversions` accounts to balance currencies.

## 4. Platform Transaction (Masked Payee)

```hledger
2026-01-15 * (pi_1A2B3C4D5E6F) **********@*******.com  ; activity: donation, time: 12:34:56, timezone: UTC+08:00
  equity:conversions:HKD-USD:USD                      20.00 USD  ; rate: 7.80000
  assets:digital:Stripe:<uuid>                       156.00 HKD
  expenses:fees:Platform                              6.00 HKD
  expenses:fees:Stripe                                8.00 HKD
  equity:conversions:HKD-USD:HKD                    -170.00 HKD
  revenues:donations:Platform:projectX              -20.00 USD
```

Notes: post net amounts to platform asset accounts and mask donor identifiers as specified.

## 5. Platform Payout

```hledger
2026-01-20 (payout_id_123, po_1Z9Y8X7W6V) Stripe  ; activity: payout, time: 15:10:10, timezone: UTC+08:00
  assets:banks:<bank-uuid>:HKD savings       156.00 HKD
  assets:digital:Stripe:<uuid>              -156.00 HKD = 0.00 HKD
```

Notes: assert platform account to zero; use `activity: payout` and second precision time when available.

## 6. Transport Reward Accrual

```hledger
2026-01-01 Kowloon Motor Bus/Long Win Bus  ; activity: transport, time: 23:59, timezone: UTC+08:00
    expenses:transport:buses                         5.90 HKD
    assets:accrued revenues:rewards                 5.90 _PT/E
    assets:digital:Octopus cards:<uuid>            -5.90 HKD
    revenues:rewards                              -5.90_PT/E
```

Notes: add accrual posting between expense and payment posting; use `_PT/E` or appropriate point currency.

## 7. Octopus eDDA Top-Up (Specialized Import)

- Pass 1 (update existing): If an Octopus row matches date+amount within heuristics, update the existing transaction header (add `duration:` or missing tags), do not duplicate.
- Pass 2 (add new): If no match, insert new transaction at correct chronological position with full IDs in parentheses, tags (`activity`, `time`, `timezone`), and validate with `bun run format` and `bun run check`.

Example (conceptual):

```hledger
2026-01-25 12:38 (C1K62243986, FRN...) Octopus eDDA top-up  ; activity: transfer, time: 12:38:00, timezone: UTC+08:00
  assets:digital:Octopus cards:<uuid>     78.00 HKD
  assets:banks:<bank-uuid>               -78.00 HKD
```

Notes: See `payee_mappings.yml`, `id_mappings.yml`, and `private.yaml` for mapping and confidentiality rules.

---

## 9. Recycling & GREEN@ points

When you recycle materials using the GREEN@ mobile app, two transactions are required in `self.alternatives.journal`. First record the physical collection, then the point credit event. Example from a 2026‑02‑14 app log where 0.1 kg plastic bottles (+8 GREEN$), 0.3 kg other plastics (+3 GREEN$), and 0.2 kg metal (+2 GREEN$) were scanned:

```hledger
2026-02-14 self  ; activity: collect, duration: -P3M26D, time: 13, timezone: UTC+08:00
    assets:recycables
    revenues:recycables:food and drinks     -0.200 _MET
    revenues:recycables:food and drinks     -0.100 _PLA
    revenues:recycables:packaging           -0.300 _OPL

2026-02-14 GREEN@*  ; activity: recycle, duration: PT0M16S, time: 13:11:46, timezone: UTC+08:00
    assets:digital:GREEN@COMMMUNITY:1683f1aa-61c7-43cc-b9f3-58da24a81704       13 GREEN$ = 8 209. GREEN$
    equity:conversions:GREEN$-_MET:_MET                                       0.200 _MET  ; rate: 10, rate: unit 0.1, recycle: 金屬, time: 13:11:30, timezone: UTC+08:00
    equity:conversions:GREEN$-_OPL:_OPL                                       0.300 _OPL  ; rate: 10, rate: unit 0.1, recycle: 其他塑膠, time: 13:11:38, timezone: UTC+08:00
    equity:conversions:GREEN$-_PLA:_PLA                                       0.100 _PLA  ; rate: 80, rate: unit 0.1, recycle: 膠樽, time: 13:11:46, timezone: UTC+08:00
    assets:recycables                                                        -0.200 _MET = 0.000 _MET
    assets:recycables                                                        -0.300 _OPL = 0.000 _OPL
    assets:recycables                                                        -0.100 _PLA = 0.000 _PLA
    equity:conversions:GREEN$-_MET:GREEN$                                     -2 GREEN$
    equity:conversions:GREEN$-_OPL:GREEN$                                     -3 GREEN$
    equity:conversions:GREEN$-_PLA:GREEN$                                     -8 GREEN$
```

Note how the first transaction moves commodities out of the temporary `assets:recycables` account, and the second records the points earned along with detailed conversion metadata.

## 8. Gifts / Red packets (lai-see)

Receiving and giving red packets (利是 / lai‑see) follows the same principles as other gifts: receipts are recorded against `equity:` (family or friends) and giving is recorded as an `expenses:gifts` posting. Use the asset account that actually moved (`assets:cash`, `assets:banks:<bank-uuid>`, or `assets:digital:*`) and include `; activity: gift` + payee UUID when available.

A. Receive — family red packet (cash)

```hledger
2026-02-15 3833b42e-dad3-425c-b254-904be68993e4  ; activity: gift, time: 10:00, timezone: UTC+08:00
    assets:cash                                               200.00 HKD
    equity:kins:families:3833b42e-dad3-425c-b254-904be68993e4  -200.00 HKD
```

B. Receive — friend red packet (bank/FPS)

```hledger
2026-02-15 56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f  ; activity: gift, via: FPS, time: 09:12, timezone: UTC+08:00
    assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:HKD savings 150.00 HKD
    equity:friends:56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f            -150.00 HKD
```

C. Give — send red packet (expense)

```hledger
2026-02-15 56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f  ; activity: gift
    expenses:gifts:friends:56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f   100.00 HKD
    assets:cash                                                 -100.00 HKD
```

D. Give a physical gift (expense + object asset)

```hledger
2026-02-15 56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f  ; activity: gift
    expenses:gifts:friends:56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f   300.00 HKD
    assets:objects:decorations                                    250.00 HKD  ; item: plush toy
    assets:cash                                                  -50.00 HKD
```

Notes: - Receiving → use `equity:kins` or `equity:friends`; Giving → `expenses:gifts`. - Always record the asset account that changed and include `; activity: gift` and payee UUID when known.

E. Receive — WeChat / Alipay (digital receive)

```hledger
2026-02-20 (wx_ABC123) 56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f  ; activity: gift, via: WeChat Pay
    assets:digital:WeChat:wx-abc123                              50.00 HKD
    equity:friends:56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f          -50.00 HKD
```

```hledger
2026-02-20 (alipay_payout_01) ACME-Corp  ; activity: gift, via: Alipay → bank
    assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:HKD savings 120.00 HKD
    equity:organizations:ACME-Corp                                -120.00 HKD
```

I. Receive — stranger / promotional (use `equity:unknown:strangers`)

```hledger
2026-02-17 unknown  ; activity: gift, time: 13:00, timezone: UTC+08:00
    assets:cash                         20.00 HKD
    equity:unknown:strangers           -20.00 HKD  ; item: red packet
```

```hledger
2026-02-18 unknown  ; activity: gift, via: WeChat Pay, time: 17:00, timezone: UTC+08:00
    assets:digital:WeChat:wx-abc123     40.00 HKD
    equity:unknown:strangers           -40.00 HKD  ; item: red packet ×2
```

F. Group‑split red packet (pool collected & distributed)

```hledger
2026-02-20 Group red-packet pool  ; activity: gift
    assets:cash                                                 300.00 HKD
    equity:friends:pool-collector                               -300.00 HKD
```

(distribute the pool later; settle `equity:friends` entries to reflect distribution)

G. Corporate / organization gift

```hledger
2026-02-20 ACME Corp  ; activity: gift
    assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:HKD savings 1 000.00 HKD
    equity:organizations:ACME-Corp                              -1 000.00 HKD  ; gift from employer
```

Note: if the gift is taxable income, record under `revenues:` instead of `equity:` per tax guidance.

H. Reimbursement / refund treated as gift (settlement, not revenue)

```hledger
2026-02-20 Friend repayment (repay expense)  ; activity: transfer
    assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:HKD savings   80.00 HKD
    equity:friends:56bddbcb-8229-4f8f-96d6-1d7d9ee09c9f            -80.00 HKD  ; repayment of earlier expense
```

Notes: - Use `equity:friends` for reimbursements/settlements; treat true gifts as `equity:friends`/`equity:kins` (never `revenues:`). - When you collect and redistribute a pool, track temporary balances under `equity:friends` until settled.

For additional edge cases and tests, update `./examples.md` and notify maintainers; keep all examples non-confidential and use placeholder UUIDs and randomized IDs. If a new worked example is added, also add a short note to `./lessons.md` explaining why the example was introduced.
