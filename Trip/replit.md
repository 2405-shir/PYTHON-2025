# Travel Expense Discord Bot

## Overview

This is a Discord bot designed to track travel expenses for a couple (Sunil and Shirin) across multiple cities. The bot allows users to add expenses in Chinese RMB and automatically converts them to their respective home currencies (GBP for Sunil, AED for Shirin). The bot uses Discord's slash commands for user interaction and stores data in JSON files.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The bot follows a modular architecture with clear separation of concerns:

- **Main Bot (`main.py`)**: Entry point that initializes the Discord bot and coordinates all components
- **Commands Module (`bot/commands.py`)**: Handles Discord slash commands and user interactions
- **Database Module (`bot/database.py`)**: Manages expense data persistence using JSON files
- **Currency Module (`bot/currency.py`)**: Handles currency conversion and exchange rate management
- **Utils Module (`bot/utils.py`)**: Provides utility functions for formatting and validation

## Key Components

### Discord Bot Framework
- Uses `discord.py` library with slash commands (app_commands)
- Implements Discord intents for message content access
- Uses cogs pattern for command organization

### Data Storage
- **Primary Storage**: JSON files for simplicity and portability
- **Exchange Rates**: Stored in `data/exchange_rates.json`
- **Expenses**: Stored in `data/expenses.json`
- Auto-generates unique IDs for each expense entry

### Currency Conversion
- **Multi-Currency Input Support**: RMB, GBP, AED, USD, EUR with smart autocomplete
- **Base currency**: Chinese RMB (CNY) - all expenses converted to RMB first
- **Target currencies**: GBP (British Pound) for Sunil, AED (UAE Dirham) for Shirin
- **Automatic conversion**: Input amount → RMB → Individual target currencies
- **Display**: Shows original amount and converted RMB amount
- Fallback to default rates when API is unavailable
- Automatic rate updates on bot startup

### Command Structure
- **19 Slash Commands Available:**

  **💰 Expense Management:**
  - `/add-expense` - Add new travel expenses with automatic currency conversion
  - `/list-expenses` - List recent expenses with IDs for editing/deleting (with filtering options)
  - `/edit-expense` - Edit any field of existing expenses (amount, currency, activity, category, city, payer, date, notes)
  - `/delete-expense` - Permanently delete expenses (requires confirmation)

  **📊 Analysis & Reporting:**
  - `/summary` - Quick expense overview with recent transactions and city breakdown
  - `/category-breakdown` - Detailed spending analysis by expense categories with per-person totals
  - `/spending-summary` - Flexible total spending in any currency, grouped by person or category with filtering
  - `/trip-itinerary` - Complete day-by-day trip timeline with activities, costs, and notes
  - `/activity-stats` - Detailed activity statistics with multiple view types (overview, by-date, by-category, by-city)

  **📁 Document Management:**
  - `/upload-document` - Attach receipts, tickets, and documents to specific expenses
  - `/list-documents` - View all uploaded documents with expense details
  - `/delete-document` - Remove documents from expenses

  **🌈 Rainbow Charts:**
  - `/chart-spending` - Beautiful rainbow pie charts for spending analysis (by category, city, or person)
  - `/chart-activities` - Colorful pie charts for activity count analysis (by category or city)

  **🔧 Database & Utilities:**
  - `/exchange-rates` - Display current live exchange rates with reverse conversions
  - `/database-stats` - Comprehensive database statistics and analytics
  - `/export-data` - Export complete data backup as downloadable JSON file
  - `/clear-database` - Permanently clear all data (requires strong confirmation)
  - `/help` - Complete interactive guide with examples and workflows
- Predefined choices for cities, categories, and payers to ensure data consistency
- Optional date and notes fields for flexibility
- Real-time validation and error handling

## Data Flow

1. **User Input**: User executes slash command with expense details
2. **Validation**: Bot validates input parameters (date format, amounts, etc.)
3. **Currency Conversion**: RMB amount converted to GBP and AED using current rates
4. **Data Storage**: Expense saved to JSON database with unique ID
5. **Response**: Bot provides confirmation with formatted expense details

## External Dependencies

### Required Libraries
- `discord.py`: Discord API integration
- `requests`: HTTP requests for currency API
- `matplotlib`: Rainbow pie chart generation with professional styling
- `pillow`: Image processing for chart optimization
- Standard Python libraries: `json`, `os`, `datetime`, `asyncio`

### External Services
- **Discord API**: For bot functionality and slash commands
- **Currency Exchange API**: Planned integration for real-time rates (currently uses fallback rates)

### Environment Variables
- `DISCORD_BOT_TOKEN`: Discord bot authentication token

## Deployment Strategy

### Current Approach
- **Local Development**: JSON file storage for simplicity
- **Data Persistence**: Files stored in `data/` directory
- **Configuration**: Environment variables for sensitive data

### Scalability Considerations
- JSON storage is suitable for the current use case (personal expense tracking)
- Easy migration path to proper database (Postgres) if needed
- Modular design allows for component upgrades without major refactoring

### Key Design Decisions

1. **JSON over Database**: Chosen for simplicity and ease of deployment on platforms like Replit
2. **Predefined Choices**: Ensures data consistency and prevents typos in categories/cities
3. **Multi-currency Support**: Addresses the specific need for different home currencies
4. **Slash Commands**: Modern Discord interaction method with better UX than prefix commands
5. **Modular Architecture**: Facilitates maintenance and feature additions

The bot is designed to be lightweight, user-friendly, and specifically tailored for tracking travel expenses across multiple currencies and locations.