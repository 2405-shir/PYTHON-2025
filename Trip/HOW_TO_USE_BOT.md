# 🤖 Complete Travel Expense Bot Guide

## 📋 **Quick Start**
This bot tracks travel expenses across multiple cities with automatic currency conversion between RMB, GBP, and AED. All commands use Discord's slash command system - just type `/` and select from the menu.

---

## 💰 **EXPENSE MANAGEMENT**

### `/add-expense` - Add New Expenses
**Purpose:** Record new travel expenses with automatic currency conversion
**Required:** amount, currency, activity, category, city, payer
**Optional:** date (defaults to today), notes

**Examples:**
- `/add-expense amount:50 currency:RMB activity:Lunch category:Food city:Beijing payer:Sunil`
- `/add-expense amount:25 currency:GBP activity:Hotel category:Accommodation city:London payer:Couple notes:Booking.com reservation`

**Features:**
- Smart autocomplete for all fields
- Automatic conversion to RMB, GBP, and AED
- Cost splitting: Individual or 50/50 for couples
- Unique ID assigned for future reference

### `/list-expenses` - View Recent Expenses
**Purpose:** See recent expenses with IDs for editing/deleting
**Optional:** limit (1-20), city, category

**Examples:**
- `/list-expenses` (shows last 10 expenses)
- `/list-expenses limit:20 city:Shanghai`
- `/list-expenses category:Food`

### `/edit-expense` - Modify Existing Expenses
**Purpose:** Change any field of an existing expense
**Required:** expense_id
**Optional:** amount, currency, activity, category, city, payer, date, notes

**Examples:**
- `/edit-expense expense_id:5 amount:60` (change amount only)
- `/edit-expense expense_id:3 category:Transportation payer:Shirin` (change multiple fields)

### `/delete-expense` - Remove Expenses
**Purpose:** Permanently delete an expense
**Required:** expense_id, confirm (type "DELETE")

**Example:**
- `/delete-expense expense_id:7 confirm:DELETE`

---

## 📊 **ANALYSIS & REPORTING**

### `/summary` - Quick Overview
**Purpose:** Fast snapshot of total expenses and recent transactions
**Optional:** city, start_date, end_date

**Examples:**
- `/summary` (all expenses)
- `/summary city:Chengdu`
- `/summary start_date:2025-02-01 end_date:2025-02-28`

### `/category-breakdown` - Detailed Category Analysis
**Purpose:** See spending by category (Food, Transportation, etc.)
**Optional:** city, start_date, end_date

**Examples:**
- `/category-breakdown` (all categories)
- `/category-breakdown city:Guilin`

### `/spending-summary` - Flexible Currency Reporting
**Purpose:** View totals in ANY currency, grouped by person or category
**Required:** currency, grouping (person/category)
**Optional:** city, start_date, end_date

**Examples:**
- `/spending-summary currency:GBP grouping:person` (see Sunil vs Shirin totals in pounds)
- `/spending-summary currency:AED grouping:category city:Abu Dhabi` (category breakdown in dirhams for Abu Dhabi)

### `/trip-itinerary` - Day-by-Day Timeline
**Purpose:** Complete trip timeline with activities and costs
**Optional:** city, start_date, end_date, specific_date

**Examples:**
- `/trip-itinerary` (full trip timeline)
- `/trip-itinerary specific_date:2025-02-15` (single day view)
- `/trip-itinerary start_date:2025-02-10 end_date:2025-02-20 city:Beijing`

---

## 📁 **DOCUMENT MANAGEMENT**

### `/upload-document` - Attach Receipts
**Purpose:** Link receipts, tickets, reservations to expenses
**Required:** expense_id, document (file attachment)

**Example:**
- `/upload-document expense_id:4 document:[attach file]`

### `/list-documents` - View All Documents
**Purpose:** See all uploaded documents with expense details
**Optional:** limit (1-20)

**Example:**
- `/list-documents limit:15`

### `/delete-document` - Remove Documents
**Purpose:** Delete documents from expenses
**Required:** expense_id, filename

**Example:**
- `/delete-document expense_id:4 filename:receipt_lunch.pdf`

---

## 🔧 **UTILITIES & MANAGEMENT**

### `/exchange-rates` - Live Currency Rates
**Purpose:** View current exchange rates with reverse conversions
**No parameters needed**

**Shows:**
- 1 RMB = £0.1040 GBP
- £1 = ¥9.62 RMB
- Updates every 4 hours automatically

### `/database-stats` - System Overview
**Purpose:** Comprehensive statistics and analytics
**No parameters needed**

**Shows:**
- Total expenses and amounts
- Top categories and cities
- Personal spending totals
- Document counts
- Date ranges

### `/export-data` - Backup Everything
**Purpose:** Download complete data backup as JSON file
**No parameters needed**

**Features:**
- Complete expense history
- All documents and metadata
- Timestamped backup file
- Easy import for restoration

### `/clear-database` - Reset Everything
**Purpose:** Permanently delete ALL data
**Required:** confirm (type "CLEAR ALL DATA")

**⚠️ WARNING:** This permanently deletes everything!

---

## 🌍 **SUPPORTED LOCATIONS**
- **Abu Dhabi** (UAE)
- **Beijing** (China)
- **Shanghai** (China)
- **Guilin** (China)
- **Chengdu** (China)
- **Chongqing** (China)
- **London** (UK)
- **Yangshuo** (China)

## 💱 **SUPPORTED CURRENCIES**
- **RMB/CNY** (Chinese Yuan) - Base currency
- **GBP** (British Pound) - Sunil's currency
- **AED** (UAE Dirham) - Shirin's currency
- **USD** (US Dollar) - Universal
- **EUR** (Euro) - Universal

## 📂 **EXPENSE CATEGORIES**
- **Transportation** 🚗 (flights, trains, taxis, buses)
- **Accommodation** 🏨 (hotels, Airbnb, hostels)
- **Food** 🍽️ (restaurants, groceries, snacks)
- **Activities** 🎯 (tours, attractions, entertainment)
- **Shopping** 🛍️ (souvenirs, clothes, gifts)
- **Official Stuff** 📋 (visas, permits, admin fees)
- **Connectivity** 📶 (SIM cards, WiFi, data)
- **Miscellaneous** 📦 (everything else)

---

## 💡 **PRO TIPS**

### Smart Usage:
- Use `/list-expenses` to find expense IDs before editing/deleting
- Set up regular `/export-data` backups for safety
- Use `specific_date` in itinerary for daily planning
- Filter reports by city and date for focused analysis

### Best Practices:
- Add notes to expenses for better tracking
- Upload receipts immediately after adding expenses
- Use consistent activity descriptions
- Check `/exchange-rates` for current conversion rates

### Date Format:
- Always use **YYYY-MM-DD** format (e.g., 2025-02-15)
- Bot validates all dates automatically

---

## 🆘 **TROUBLESHOOTING**

**Commands not showing?**
- Make sure bot has proper permissions in the server
- Try refreshing Discord or restarting the app

**Currency conversion issues?**
- Bot updates rates every 4 hours automatically
- Uses professional exchange rate APIs with fallbacks

**Can't find expense ID?**
- Use `/list-expenses` with filters to locate specific expenses
- IDs are shown in all expense listings

**Need help?**
- All commands include helpful error messages
- Use autocomplete for valid options
- Check this guide for examples and usage

---

## 🎯 **WORKFLOW EXAMPLES**

### Adding a Day's Expenses:
1. `/add-expense amount:200 currency:RMB activity:Train to Shanghai category:Transportation city:Shanghai payer:Sunil`
2. `/add-expense amount:80 currency:RMB activity:Hotel check-in category:Accommodation city:Shanghai payer:Couple`
3. `/upload-document expense_id:1 document:[train_ticket.pdf]`
4. `/trip-itinerary specific_date:2025-02-15` (review the day)

### Weekly Review:
1. `/spending-summary currency:GBP grouping:person start_date:2025-02-08 end_date:2025-02-14`
2. `/category-breakdown start_date:2025-02-08 end_date:2025-02-14`
3. `/export-data` (backup weekly data)

### Trip Planning:
1. `/exchange-rates` (check current rates)
2. `/database-stats` (see overall progress)
3. `/trip-itinerary city:Beijing` (review Beijing plans)

---

*Your travel expense bot is ready to track every penny of your adventure! 🌏💰*