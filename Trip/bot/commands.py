import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os
from pathlib import Path
from typing import Literal, Optional, List, Dict
from .database import ExpenseDatabase
from .currency import CurrencyConverter
from .utils import create_summary_embed, create_breakdown_embed, create_itinerary_embed, validate_date
from .charts import ChartGenerator

# Define choices for slash commands
CITIES = [
    "Abu Dhabi", "Beijing", "Shanghai", "Guilin", 
    "Chengdu", "Chongqing", "London", "Yangshuo"
]

CATEGORIES = [
    "Official Stuff", "Transportation", "Accommodation", "Food",
    "Activities", "Shopping", "Connectivity", "Miscellaneous"
]

PAYERS = ["Sunil", "Shirin", "Couple"]

CURRENCIES = ["RMB", "GBP", "AED", "USD", "EUR"]

class ExpenseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = ExpenseDatabase()
        self.currency = CurrencyConverter()
        self.charts = ChartGenerator()
    
    # Autocomplete functions
    async def city_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for cities"""
        choices = []
        for city in CITIES:
            if current.lower() in city.lower():
                choices.append(app_commands.Choice(name=city, value=city))
        return choices[:25]  # Discord limit
    
    async def category_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for categories"""
        choices = []
        for category in CATEGORIES:
            if current.lower() in category.lower():
                choices.append(app_commands.Choice(name=category, value=category))
        return choices[:25]  # Discord limit
    
    async def payer_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for payers"""
        choices = []
        for payer in PAYERS:
            if current.lower() in payer.lower():
                choices.append(app_commands.Choice(name=payer, value=payer))
        return choices[:25]  # Discord limit
    
    async def currency_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for currencies"""
        choices = []
        for currency in CURRENCIES:
            if current.lower() in currency.lower():
                choices.append(app_commands.Choice(name=currency, value=currency))
        return choices[:25]  # Discord limit
    
    @app_commands.command(name="add-expense", description="Add a new travel expense")
    @app_commands.describe(
        city="Type to search cities (Abu Dhabi, Beijing, Shanghai, etc.)",
        activity="Description of the activity or expense",
        amount="Amount to spend",
        currency="Type to search currency (RMB, GBP, AED, USD, EUR)",
        category="Type to search categories (Food, Transport, etc.)",
        payer="Type to search payers (Sunil, Shirin, Couple)",
        date="Date in YYYY-MM-DD format (optional, defaults to today)",
        notes="Additional notes (optional)"
    )
    @app_commands.autocomplete(city=city_autocomplete)
    @app_commands.autocomplete(currency=currency_autocomplete)
    @app_commands.autocomplete(category=category_autocomplete)
    @app_commands.autocomplete(payer=payer_autocomplete)
    async def add_expense(
        self,
        interaction: discord.Interaction,
        city: str,
        activity: str,
        amount: float,
        currency: str,
        category: str,
        payer: str,
        date: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Add a new expense entry"""
        try:
            # Validate city, category, and payer
            if city not in CITIES:
                await interaction.response.send_message(
                    f"❌ Invalid city '{city}'. Please select from: {', '.join(CITIES)}",
                    ephemeral=True
                )
                return
            
            if category not in CATEGORIES:
                await interaction.response.send_message(
                    f"❌ Invalid category '{category}'. Please select from: {', '.join(CATEGORIES)}",
                    ephemeral=True
                )
                return
            
            if payer not in PAYERS:
                await interaction.response.send_message(
                    f"❌ Invalid payer '{payer}'. Please select from: {', '.join(PAYERS)}",
                    ephemeral=True
                )
                return
            
            if currency not in CURRENCIES:
                await interaction.response.send_message(
                    f"❌ Invalid currency '{currency}'. Please select from: {', '.join(CURRENCIES)}",
                    ephemeral=True
                )
                return
            
            # Validate and parse date
            if date:
                if not validate_date(date):
                    await interaction.response.send_message(
                        "❌ Invalid date format. Please use YYYY-MM-DD format.",
                        ephemeral=True
                    )
                    return
                expense_date = date
            else:
                expense_date = datetime.now().strftime("%Y-%m-%d")
            
            # Validate amount
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be greater than 0.",
                    ephemeral=True
                )
                return
            
            # Convert input currency to RMB first
            rates = await self.currency.get_rates()
            
            # Convert input amount to RMB (base currency)
            if currency == "RMB":
                amount_rmb = amount
            elif currency == "GBP":
                # Convert GBP to RMB (inverse of RMB to GBP rate)
                gbp_to_rmb_rate = 1 / rates.get('GBP', 0.11) if rates.get('GBP', 0.11) != 0 else 9.09
                amount_rmb = amount * gbp_to_rmb_rate
            elif currency == "AED":
                # Convert AED to RMB (inverse of RMB to AED rate)
                aed_to_rmb_rate = 1 / rates.get('AED', 0.52) if rates.get('AED', 0.52) != 0 else 1.92
                amount_rmb = amount * aed_to_rmb_rate
            elif currency == "USD":
                # Convert USD to RMB (inverse of RMB to USD rate)
                usd_to_rmb_rate = 1 / rates.get('USD', 0.14) if rates.get('USD', 0.14) != 0 else 7.14
                amount_rmb = amount * usd_to_rmb_rate
            elif currency == "EUR":
                # Convert EUR to RMB (inverse of RMB to EUR rate)
                eur_to_rmb_rate = 1 / rates.get('EUR', 0.13) if rates.get('EUR', 0.13) != 0 else 7.69
                amount_rmb = amount * eur_to_rmb_rate
            else:
                amount_rmb = amount  # Fallback to treating as RMB
            
            # Now calculate individual amounts in RMB and convert to target currencies
            if payer == "Couple":
                # Split the RMB amount in half
                sunil_rmb = amount_rmb / 2
                shirin_rmb = amount_rmb / 2
                sunil_gbp = sunil_rmb * rates.get('GBP', 0.11)
                shirin_aed = shirin_rmb * rates.get('AED', 0.52)
            elif payer == "Sunil":
                sunil_rmb = amount_rmb
                shirin_rmb = 0
                sunil_gbp = amount_rmb * rates.get('GBP', 0.11)
                shirin_aed = 0
            else:  # Shirin
                sunil_rmb = 0
                shirin_rmb = amount_rmb
                sunil_gbp = 0
                shirin_aed = amount_rmb * rates.get('AED', 0.52)
            
            # Create expense entry
            expense = {
                'id': self.db.get_next_id(),
                'city': city,
                'activity': activity,
                'category': category,
                'date': expense_date,
                'original_amount': amount,
                'original_currency': currency,
                'total_rmb': amount_rmb,
                'payer': payer,
                'sunil_rmb': sunil_rmb,
                'shirin_rmb': shirin_rmb,
                'sunil_gbp': sunil_gbp,
                'shirin_aed': shirin_aed,
                'notes': notes or "",
                'documents': [],
                'created_at': datetime.now().isoformat()
            }
            
            # Save to database
            self.db.add_expense(expense)
            
            # Create response embed
            embed = discord.Embed(
                title="✅ Expense Added Successfully",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="🏙️ City", value=city, inline=True)
            embed.add_field(name="📅 Date", value=expense_date, inline=True)
            embed.add_field(name="🏷️ Category", value=category, inline=True)
            
            embed.add_field(name="🎯 Activity", value=activity, inline=False)
            
            # Show original amount and converted amount
            if currency == "RMB":
                amount_display = f"¥{amount:,.2f} RMB"
            else:
                from .utils import format_currency
                original_display = format_currency(amount, currency)
                rmb_display = f"¥{amount_rmb:,.2f} RMB"
                amount_display = f"{original_display} → {rmb_display}"
            
            embed.add_field(name="💰 Amount", value=amount_display, inline=True)
            embed.add_field(name="💳 Payer", value=payer, inline=True)
            
            if payer == "Couple":
                embed.add_field(
                    name="💵 Split Details",
                    value=f"Sunil: ¥{sunil_rmb:,.2f} (£{sunil_gbp:,.2f})\nShirin: ¥{shirin_rmb:,.2f} (AED {shirin_aed:,.2f})",
                    inline=False
                )
            elif payer == "Sunil":
                embed.add_field(name="💵 Sunil's Share", value=f"¥{sunil_rmb:,.2f} (£{sunil_gbp:,.2f})", inline=False)
            else:
                embed.add_field(name="💵 Shirin's Share", value=f"¥{shirin_rmb:,.2f} (AED {shirin_aed:,.2f})", inline=False)
            
            if notes:
                embed.add_field(name="📝 Notes", value=notes, inline=False)
            
            embed.set_footer(text=f"Expense ID: {expense['id']}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error adding expense: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="summary", description="Get expense summary")
    @app_commands.describe(
        city="Filter by city (optional) - type to search",
        start_date="Start date in YYYY-MM-DD format (optional)",
        end_date="End date in YYYY-MM-DD format (optional)"
    )
    @app_commands.autocomplete(city=city_autocomplete)
    async def summary(
        self,
        interaction: discord.Interaction,
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Generate expense summary"""
        try:
            # Validate city if provided
            if city and city not in CITIES:
                await interaction.response.send_message(
                    f"❌ Invalid city '{city}'. Please select from: {', '.join(CITIES)}",
                    ephemeral=True
                )
                return
            
            # Validate dates
            if start_date and not validate_date(start_date):
                await interaction.response.send_message(
                    "❌ Invalid start date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            if end_date and not validate_date(end_date):
                await interaction.response.send_message(
                    "❌ Invalid end date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            # Get filtered expenses
            expenses = self.db.get_expenses(city=city, start_date=start_date, end_date=end_date)
            
            if not expenses:
                await interaction.response.send_message(
                    "📊 No expenses found for the specified criteria.",
                    ephemeral=True
                )
                return
            
            # Create summary embed
            embed = create_summary_embed(expenses, city, start_date, end_date)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating summary: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="category-breakdown", description="Get expense breakdown by category")
    @app_commands.describe(
        city="Filter by city (optional) - type to search",
        start_date="Start date in YYYY-MM-DD format (optional)",
        end_date="End date in YYYY-MM-DD format (optional)"
    )
    @app_commands.autocomplete(city=city_autocomplete)
    async def category_breakdown(
        self,
        interaction: discord.Interaction,
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Generate category breakdown"""
        try:
            # Validate city if provided
            if city and city not in CITIES:
                await interaction.response.send_message(
                    f"❌ Invalid city '{city}'. Please select from: {', '.join(CITIES)}",
                    ephemeral=True
                )
                return
            
            # Validate dates
            if start_date and not validate_date(start_date):
                await interaction.response.send_message(
                    "❌ Invalid start date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            if end_date and not validate_date(end_date):
                await interaction.response.send_message(
                    "❌ Invalid end date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            # Get filtered expenses
            expenses = self.db.get_expenses(city=city, start_date=start_date, end_date=end_date)
            
            if not expenses:
                await interaction.response.send_message(
                    "📊 No expenses found for the specified criteria.",
                    ephemeral=True
                )
                return
            
            # Create breakdown embed
            embed = create_breakdown_embed(expenses, city, start_date, end_date)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating breakdown: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="trip-itinerary", description="Generate complete trip itinerary with all expenses by date")
    @app_commands.describe(
        city="Filter by specific city (optional) - type to search",
        start_date="Trip start date in YYYY-MM-DD format (optional)",
        end_date="Trip end date in YYYY-MM-DD format (optional)",
        specific_date="View single day itinerary in YYYY-MM-DD format (optional)"
    )
    @app_commands.autocomplete(city=city_autocomplete)
    async def trip_itinerary(
        self,
        interaction: discord.Interaction,
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        specific_date: Optional[str] = None
    ):
        """Generate complete trip itinerary with day-by-day breakdown"""
        try:
            # Validate city if provided
            if city and city not in CITIES:
                await interaction.response.send_message(
                    f"❌ Invalid city '{city}'. Please select from: {', '.join(CITIES)}",
                    ephemeral=True
                )
                return
            
            # Validate dates
            if start_date and not validate_date(start_date):
                await interaction.response.send_message(
                    "❌ Invalid start date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            if end_date and not validate_date(end_date):
                await interaction.response.send_message(
                    "❌ Invalid end date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            if specific_date and not validate_date(specific_date):
                await interaction.response.send_message(
                    "❌ Invalid specific date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            # Handle specific date - override start/end dates
            if specific_date:
                start_date = specific_date
                end_date = specific_date
            
            # Get filtered expenses
            expenses = self.db.get_expenses(city=city, start_date=start_date, end_date=end_date)
            
            if not expenses:
                await interaction.response.send_message(
                    "📊 No expenses found for the specified criteria.",
                    ephemeral=True
                )
                return
            
            # Create itinerary embed
            embed = create_itinerary_embed(expenses, city, start_date, end_date)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating itinerary: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="upload-document", description="Upload a document for an expense")
    @app_commands.describe(
        expense_id="ID of the expense to attach document to",
        document="PDF or text document to upload"
    )
    async def upload_document(
        self,
        interaction: discord.Interaction,
        expense_id: int,
        document: discord.Attachment
    ):
        """Upload a document for an expense"""
        try:
            # Check if expense exists
            expense = self.db.get_expense_by_id(expense_id)
            if not expense:
                await interaction.response.send_message(
                    f"❌ Expense with ID {expense_id} not found.",
                    ephemeral=True
                )
                return
            
            # Validate file type
            allowed_extensions = ['.pdf', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            file_extension = os.path.splitext(document.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                await interaction.response.send_message(
                    f"❌ File type {file_extension} not allowed. Supported types: {', '.join(allowed_extensions)}",
                    ephemeral=True
                )
                return
            
            # Check file size (10MB limit)
            if document.size > 10 * 1024 * 1024:
                await interaction.response.send_message(
                    "❌ File size too large. Maximum size is 10MB.",
                    ephemeral=True
                )
                return
            
            # Save document
            filename = f"{expense_id}_{document.filename}"
            filepath = f"documents/{filename}"
            
            # Create documents directory if it doesn't exist
            os.makedirs("documents", exist_ok=True)
            
            # Download and save file
            await document.save(fp=Path(filepath))
            
            # Update expense with document info
            document_info = {
                'filename': document.filename,
                'filepath': filepath,
                'size': document.size,
                'uploaded_at': datetime.now().isoformat()
            }
            
            self.db.add_document_to_expense(expense_id, document_info)
            
            # Create response embed
            embed = discord.Embed(
                title="📎 Document Uploaded Successfully",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="📄 Filename", value=document.filename, inline=True)
            embed.add_field(name="💾 Size", value=f"{document.size:,} bytes", inline=True)
            embed.add_field(name="🆔 Expense ID", value=str(expense_id), inline=True)
            
            embed.add_field(
                name="🎯 Associated Expense",
                value=f"{expense['activity']} - {expense['city']}",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error uploading document: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="exchange-rates", description="Show current exchange rates")
    async def exchange_rates(self, interaction: discord.Interaction):
        """Display current exchange rates"""
        try:
            # Force update rates
            await self.currency.update_rates()
            rate_info = self.currency.get_rate_info()
            
            embed = discord.Embed(
                title="💱 Current Exchange Rates",
                description="All rates are from 1 Chinese Yuan (RMB)",
                color=0xf39c12,
                timestamp=datetime.now()
            )
            
            rates = rate_info['rates']
            
            # Add rate fields
            embed.add_field(
                name="🇬🇧 British Pound (GBP)",
                value=f"1 RMB = £{rates['GBP']:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="🇦🇪 UAE Dirham (AED)",
                value=f"1 RMB = AED {rates['AED']:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="🇺🇸 US Dollar (USD)",
                value=f"1 RMB = ${rates['USD']:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="🇪🇺 Euro (EUR)",
                value=f"1 RMB = €{rates['EUR']:.4f}",
                inline=True
            )
            
            # Show reverse rates for common conversions
            embed.add_field(
                name="💷 Reverse Rates",
                value=(
                    f"£1 = ¥{1/rates['GBP']:.2f} RMB\n"
                    f"AED 1 = ¥{1/rates['AED']:.2f} RMB\n"
                    f"$1 = ¥{1/rates['USD']:.2f} RMB"
                ),
                inline=False
            )
            
            # Last updated info
            last_updated = rate_info['last_updated']
            if last_updated:
                try:
                    update_time = datetime.fromisoformat(last_updated)
                    embed.set_footer(text=f"Last updated: {update_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                except:
                    embed.set_footer(text="Using live exchange rates")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error fetching exchange rates: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="spending-summary", description="Get total spending in any currency by person or category")
    @app_commands.describe(
        currency="Choose currency for display (RMB, GBP, AED, USD, EUR)",
        grouping="Group by person or category",
        city="Filter by specific city (optional)",
        start_date="Start date in YYYY-MM-DD format (optional)",
        end_date="End date in YYYY-MM-DD format (optional)"
    )
    @app_commands.autocomplete(currency=currency_autocomplete)
    @app_commands.autocomplete(city=city_autocomplete)
    async def spending_summary(
        self,
        interaction: discord.Interaction,
        currency: str,
        grouping: Literal["person", "category"],
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Generate spending summary in chosen currency"""
        try:
            # Validate currency
            if currency not in CURRENCIES:
                await interaction.response.send_message(
                    f"❌ Invalid currency '{currency}'. Please select from: {', '.join(CURRENCIES)}",
                    ephemeral=True
                )
                return
            
            # Validate city if provided
            if city and city not in CITIES:
                await interaction.response.send_message(
                    f"❌ Invalid city '{city}'. Please select from: {', '.join(CITIES)}",
                    ephemeral=True
                )
                return
            
            # Validate dates
            if start_date and not validate_date(start_date):
                await interaction.response.send_message(
                    "❌ Invalid start date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            if end_date and not validate_date(end_date):
                await interaction.response.send_message(
                    "❌ Invalid end date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            # Get filtered expenses
            expenses = self.db.get_expenses(city=city, start_date=start_date, end_date=end_date)
            
            if not expenses:
                await interaction.response.send_message(
                    "📊 No expenses found for the specified criteria.",
                    ephemeral=True
                )
                return
            
            # Get current exchange rates
            rates = await self.currency.get_rates()
            
            # Create spending summary embed
            embed = await self.create_spending_summary_embed(
                expenses, currency, grouping, rates, city, start_date, end_date
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating spending summary: {str(e)}",
                ephemeral=True
            )
    
    async def create_spending_summary_embed(
        self, 
        expenses, 
        target_currency: str, 
        grouping: str, 
        rates: dict,
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> discord.Embed:
        """Create spending summary embed in chosen currency"""
        from .utils import format_currency
        
        # Convert RMB to target currency
        def convert_rmb_to_target(amount_rmb: float) -> float:
            if target_currency == "RMB":
                return amount_rmb
            elif target_currency == "GBP":
                return amount_rmb * rates.get('GBP', 0.11)
            elif target_currency == "AED":
                return amount_rmb * rates.get('AED', 0.52)
            elif target_currency == "USD":
                return amount_rmb * rates.get('USD', 0.14)
            elif target_currency == "EUR":
                return amount_rmb * rates.get('EUR', 0.13)
            return amount_rmb
        
        # Create embed
        embed = discord.Embed(
            title=f"💰 Spending Summary in {target_currency}",
            color=0x27ae60,
            timestamp=datetime.now()
        )
        
        # Add filter information
        filter_info = []
        if city:
            filter_info.append(f"🏙️ City: {city}")
        if start_date:
            filter_info.append(f"📅 From: {start_date}")
        if end_date:
            filter_info.append(f"📅 To: {end_date}")
        
        if filter_info:
            embed.add_field(name="🔍 Filters Applied", value="\n".join(filter_info), inline=False)
        
        if grouping == "person":
            # Calculate totals by person
            sunil_total = sum(exp['sunil_rmb'] for exp in expenses)
            shirin_total = sum(exp['shirin_rmb'] for exp in expenses)
            combined_total = sunil_total + shirin_total
            
            # Convert to target currency
            sunil_converted = convert_rmb_to_target(sunil_total)
            shirin_converted = convert_rmb_to_target(shirin_total)
            combined_converted = convert_rmb_to_target(combined_total)
            
            embed.add_field(
                name="👨 Sunil's Total",
                value=format_currency(sunil_converted, target_currency),
                inline=True
            )
            
            embed.add_field(
                name="👩 Shirin's Total",
                value=format_currency(shirin_converted, target_currency),
                inline=True
            )
            
            embed.add_field(
                name="💑 Combined Total",
                value=format_currency(combined_converted, target_currency),
                inline=True
            )
            
            # Add percentage breakdown
            if combined_converted > 0:
                sunil_percentage = (sunil_converted / combined_converted) * 100
                shirin_percentage = (shirin_converted / combined_converted) * 100
                
                embed.add_field(
                    name="📊 Spending Breakdown",
                    value=f"Sunil: {sunil_percentage:.1f}%\nShirin: {shirin_percentage:.1f}%",
                    inline=False
                )
        
        else:  # grouping == "category"
            # Calculate totals by category
            categories = {}
            for exp in expenses:
                cat = exp['category']
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += exp['total_rmb']
            
            # Sort categories by amount
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            # Convert and display each category
            total_all_categories = 0
            for category, amount_rmb in sorted_categories:
                converted_amount = convert_rmb_to_target(amount_rmb)
                total_all_categories += converted_amount
                
                # Use emoji for categories
                from .utils import get_expense_emoji
                emoji = get_expense_emoji(category)
                
                embed.add_field(
                    name=f"{emoji} {category}",
                    value=format_currency(converted_amount, target_currency),
                    inline=True
                )
            
            # Add total
            embed.add_field(
                name="💰 Grand Total",
                value=format_currency(total_all_categories, target_currency),
                inline=False
            )
            
            # Add top spending category
            if sorted_categories:
                top_category, top_amount = sorted_categories[0]
                top_converted = convert_rmb_to_target(top_amount)
                percentage = (top_converted / total_all_categories * 100) if total_all_categories > 0 else 0
                
                embed.add_field(
                    name="🔝 Highest Spending",
                    value=f"{top_category}: {percentage:.1f}% of total",
                    inline=False
                )
        
        # Add trip statistics
        stats_text = (
            f"**Total Transactions:** {len(expenses)}\n"
            f"**Trip Duration:** {len(set(exp['date'] for exp in expenses))} days\n"
            f"**Cities Visited:** {len(set(exp['city'] for exp in expenses))}"
        )
        embed.add_field(name="📈 Trip Statistics", value=stats_text, inline=False)
        
        # Footer with exchange rate info
        if target_currency != "RMB":
            rate = rates.get(target_currency, 0)
            embed.set_footer(text=f"Exchange rate: 1 RMB = {rate:.4f} {target_currency}")
        
        return embed
    
    @app_commands.command(name="list-expenses", description="List recent expenses with IDs for editing/deleting")
    @app_commands.describe(
        limit="Number of expenses to show (1-20, default 10)",
        city="Filter by specific city (optional)",
        category="Filter by specific category (optional)"
    )
    @app_commands.autocomplete(city=city_autocomplete)
    @app_commands.autocomplete(category=category_autocomplete)
    async def list_expenses(
        self,
        interaction: discord.Interaction,
        limit: Optional[int] = 10,
        city: Optional[str] = None,
        category: Optional[str] = None
    ):
        """List expenses with IDs for management"""
        try:
            # Validate limit
            if limit and (limit < 1 or limit > 20):
                await interaction.response.send_message(
                    "❌ Limit must be between 1 and 20",
                    ephemeral=True
                )
                return
            
            # Get filtered expenses
            expenses = self.db.get_expenses(city=city)
            
            # Filter by category if specified
            if category:
                expenses = [exp for exp in expenses if exp['category'] == category]
            
            if not expenses:
                await interaction.response.send_message(
                    "📋 No expenses found matching your criteria",
                    ephemeral=True
                )
                return
            
            # Limit results
            limited_expenses = expenses[:limit or 10]
            
            embed = discord.Embed(
                title="📋 Expense List",
                description=f"Showing {len(limited_expenses)} of {len(expenses)} expenses",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            # Add filter info
            filter_info = []
            if city:
                filter_info.append(f"🏙️ City: {city}")
            if category:
                filter_info.append(f"📂 Category: {category}")
            if filter_info:
                embed.add_field(name="🔍 Filters", value="\n".join(filter_info), inline=False)
            
            # List expenses
            expense_list = []
            for exp in limited_expenses:
                from .utils import format_currency, get_expense_emoji
                emoji = get_expense_emoji(exp['category'])
                
                expense_text = (
                    f"**ID: {exp['id']}** | {exp['date']} | {exp['city']}\n"
                    f"{emoji} {exp['activity']} ({exp['category']})\n"
                    f"💰 {format_currency(exp['total_rmb'], 'RMB')} - Paid by {exp['payer']}"
                )
                
                if exp['notes']:
                    expense_text += f"\n📝 {exp['notes'][:50]}{'...' if len(exp['notes']) > 50 else ''}"
                
                expense_list.append(expense_text)
            
            # Split into chunks to avoid Discord limits
            chunk_size = 5
            for i in range(0, len(expense_list), chunk_size):
                chunk = expense_list[i:i + chunk_size]
                field_name = f"Expenses {i+1}-{min(i+chunk_size, len(expense_list))}"
                embed.add_field(
                    name=field_name,
                    value="\n\n".join(chunk),
                    inline=False
                )
            
            embed.set_footer(text="Use /edit-expense or /delete-expense with the ID number")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error listing expenses: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="edit-expense", description="Edit an existing expense")
    @app_commands.describe(
        expense_id="ID of the expense to edit (use /list-expenses to find IDs)",
        amount="New amount",
        currency="New currency if changing amount",
        activity="New activity description",
        category="New category",
        city="New city",
        payer="New payer",
        date="New date (YYYY-MM-DD format)",
        notes="New notes"
    )
    @app_commands.autocomplete(currency=currency_autocomplete)
    @app_commands.autocomplete(category=category_autocomplete)
    @app_commands.autocomplete(city=city_autocomplete)
    @app_commands.autocomplete(payer=payer_autocomplete)
    async def edit_expense(
        self,
        interaction: discord.Interaction,
        expense_id: int,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        activity: Optional[str] = None,
        category: Optional[str] = None,
        city: Optional[str] = None,
        payer: Optional[str] = None,
        date: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Edit an existing expense"""
        try:
            # Get existing expense
            expense = self.db.get_expense_by_id(expense_id)
            if not expense:
                await interaction.response.send_message(
                    f"❌ Expense with ID {expense_id} not found. Use /list-expenses to see available IDs.",
                    ephemeral=True
                )
                return
            
            # Validate new values if provided
            if currency and currency not in CURRENCIES:
                await interaction.response.send_message(
                    f"❌ Invalid currency '{currency}'. Please select from: {', '.join(CURRENCIES)}",
                    ephemeral=True
                )
                return
            
            if category and category not in CATEGORIES:
                await interaction.response.send_message(
                    f"❌ Invalid category '{category}'. Please select from: {', '.join(CATEGORIES)}",
                    ephemeral=True
                )
                return
            
            if city and city not in CITIES:
                await interaction.response.send_message(
                    f"❌ Invalid city '{city}'. Please select from: {', '.join(CITIES)}",
                    ephemeral=True
                )
                return
            
            if payer and payer not in PAYERS:
                await interaction.response.send_message(
                    f"❌ Invalid payer '{payer}'. Please select from: {', '.join(PAYERS)}",
                    ephemeral=True
                )
                return
            
            if date and not validate_date(date):
                await interaction.response.send_message(
                    "❌ Invalid date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
            
            if amount is not None and amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be greater than 0",
                    ephemeral=True
                )
                return
            
            # Prepare updates
            updates = {}
            if activity is not None:
                updates['activity'] = activity
            if category is not None:
                updates['category'] = category
            if city is not None:
                updates['city'] = city
            if payer is not None:
                updates['payer'] = payer
            if date is not None:
                updates['date'] = date
            if notes is not None:
                updates['notes'] = notes
            
            # Handle amount and currency changes
            if amount is not None:
                # Use provided currency or keep original
                update_currency = currency or expense['original_currency']
                
                # Convert to RMB and calculate shares
                rates = await self.currency.get_rates()
                if update_currency == "RMB":
                    amount_rmb = amount
                else:
                    # Convert from other currency to RMB
                    if update_currency == "GBP":
                        amount_rmb = amount / rates.get('GBP', 0.11)
                    elif update_currency == "AED":
                        amount_rmb = amount / rates.get('AED', 0.52)
                    elif update_currency == "USD":
                        amount_rmb = amount / rates.get('USD', 0.14)
                    elif update_currency == "EUR":
                        amount_rmb = amount / rates.get('EUR', 0.13)
                    else:
                        amount_rmb = amount
                
                # Calculate individual shares
                if updates.get('payer', expense['payer']) == "Couple":
                    sunil_rmb = amount_rmb / 2
                    shirin_rmb = amount_rmb / 2
                elif updates.get('payer', expense['payer']) == "Sunil":
                    sunil_rmb = amount_rmb
                    shirin_rmb = 0
                else:  # Shirin
                    sunil_rmb = 0
                    shirin_rmb = amount_rmb
                
                # Convert to individual currencies
                sunil_gbp = sunil_rmb * rates.get('GBP', 0.11)
                shirin_aed = shirin_rmb * rates.get('AED', 0.52)
                
                # Add amount updates
                updates.update({
                    'original_amount': amount,
                    'original_currency': update_currency,
                    'total_rmb': amount_rmb,
                    'sunil_rmb': sunil_rmb,
                    'sunil_gbp': sunil_gbp,
                    'shirin_rmb': shirin_rmb,
                    'shirin_aed': shirin_aed
                })
            
            if not updates:
                await interaction.response.send_message(
                    "❌ No changes provided. Please specify what you want to edit.",
                    ephemeral=True
                )
                return
            
            # Update expense
            success = self.db.update_expense(expense_id, updates)
            
            if success:
                # Get updated expense
                updated_expense = self.db.get_expense_by_id(expense_id)
                
                # Create confirmation embed
                embed = discord.Embed(
                    title="✅ Expense Updated Successfully",
                    color=0x27ae60,
                    timestamp=datetime.now()
                )
                
                from .utils import format_currency, get_expense_emoji
                emoji = get_expense_emoji(updated_expense['category'])
                
                embed.add_field(
                    name=f"{emoji} Updated Expense",
                    value=(
                        f"**ID:** {updated_expense['id']}\n"
                        f"**Date:** {updated_expense['date']}\n"
                        f"**City:** {updated_expense['city']}\n"
                        f"**Activity:** {updated_expense['activity']}\n"
                        f"**Category:** {updated_expense['category']}\n"
                        f"**Amount:** {format_currency(updated_expense['original_amount'], updated_expense['original_currency'])}\n"
                        f"**Paid by:** {updated_expense['payer']}"
                    ),
                    inline=False
                )
                
                if updated_expense['notes']:
                    embed.add_field(name="📝 Notes", value=updated_expense['notes'], inline=False)
                
                # Show cost breakdown
                embed.add_field(
                    name="💰 Cost Breakdown",
                    value=(
                        f"**Total:** {format_currency(updated_expense['total_rmb'], 'RMB')}\n"
                        f"**Sunil:** {format_currency(updated_expense['sunil_gbp'], 'GBP')}\n"
                        f"**Shirin:** {format_currency(updated_expense['shirin_aed'], 'AED')}"
                    ),
                    inline=True
                )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"❌ Failed to update expense {expense_id}",
                    ephemeral=True
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error editing expense: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="delete-expense", description="Delete an expense permanently")
    @app_commands.describe(
        expense_id="ID of the expense to delete (use /list-expenses to find IDs)",
        confirm="Type 'DELETE' to confirm permanent deletion"
    )
    async def delete_expense(
        self,
        interaction: discord.Interaction,
        expense_id: int,
        confirm: str
    ):
        """Delete an expense permanently"""
        try:
            # Check confirmation
            if confirm.upper() != "DELETE":
                await interaction.response.send_message(
                    "❌ To delete an expense, you must type 'DELETE' in the confirm field.",
                    ephemeral=True
                )
                return
            
            # Get expense details before deletion
            expense = self.db.get_expense_by_id(expense_id)
            if not expense:
                await interaction.response.send_message(
                    f"❌ Expense with ID {expense_id} not found. Use /list-expenses to see available IDs.",
                    ephemeral=True
                )
                return
            
            # Delete expense
            success = self.db.delete_expense(expense_id)
            
            if success:
                from .utils import format_currency, get_expense_emoji
                emoji = get_expense_emoji(expense['category'])
                
                embed = discord.Embed(
                    title="🗑️ Expense Deleted",
                    description="The expense has been permanently removed from your records.",
                    color=0xe74c3c,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name=f"{emoji} Deleted Expense",
                    value=(
                        f"**ID:** {expense['id']}\n"
                        f"**Date:** {expense['date']}\n"
                        f"**City:** {expense['city']}\n"
                        f"**Activity:** {expense['activity']}\n"
                        f"**Amount:** {format_currency(expense['original_amount'], expense['original_currency'])}\n"
                        f"**Total:** {format_currency(expense['total_rmb'], 'RMB')}"
                    ),
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"❌ Failed to delete expense {expense_id}",
                    ephemeral=True
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error deleting expense: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="list-documents", description="List all uploaded documents")
    @app_commands.describe(limit="Number of documents to show (1-20, default 10)")
    async def list_documents(self, interaction: discord.Interaction, limit: Optional[int] = 10):
        """List all uploaded documents"""
        try:
            if limit and (limit < 1 or limit > 20):
                await interaction.response.send_message(
                    "❌ Limit must be between 1 and 20",
                    ephemeral=True
                )
                return
            
            documents = self.db.get_all_documents()
            
            if not documents:
                await interaction.response.send_message(
                    "📁 No documents found",
                    ephemeral=True
                )
                return
            
            limited_docs = documents[:limit or 10]
            
            embed = discord.Embed(
                title="📁 Document List",
                description=f"Showing {len(limited_docs)} of {len(documents)} documents",
                color=0x9b59b6,
                timestamp=datetime.now()
            )
            
            doc_list = []
            for doc in limited_docs:
                doc_text = (
                    f"**{doc['filename']}** ({doc['file_type']})\n"
                    f"📎 Expense ID: {doc['expense_id']} | {doc['expense_date']}\n"
                    f"🏙️ {doc['expense_city']} - {doc['expense_activity']}\n"
                    f"⏰ Uploaded: {doc['uploaded_at'][:16]}"
                )
                doc_list.append(doc_text)
            
            # Split into chunks
            chunk_size = 4
            for i in range(0, len(doc_list), chunk_size):
                chunk = doc_list[i:i + chunk_size]
                field_name = f"Documents {i+1}-{min(i+chunk_size, len(doc_list))}"
                embed.add_field(
                    name=field_name,
                    value="\n\n".join(chunk),
                    inline=False
                )
            
            embed.set_footer(text="Use /delete-document with expense ID and filename to remove")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error listing documents: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="delete-document", description="Delete a document from an expense")
    @app_commands.describe(
        expense_id="ID of the expense containing the document",
        filename="Name of the file to delete"
    )
    async def delete_document(
        self,
        interaction: discord.Interaction,
        expense_id: int,
        filename: str
    ):
        """Delete a document from an expense"""
        try:
            success = self.db.delete_document(expense_id, filename)
            
            if success:
                embed = discord.Embed(
                    title="🗑️ Document Deleted",
                    description=f"Successfully deleted **{filename}** from expense {expense_id}",
                    color=0xe74c3c,
                    timestamp=datetime.now()
                )
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"❌ Document '{filename}' not found in expense {expense_id}",
                    ephemeral=True
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error deleting document: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="database-stats", description="Show comprehensive database statistics")
    async def database_stats(self, interaction: discord.Interaction):
        """Show comprehensive database statistics"""
        try:
            stats = self.db.get_database_stats()
            
            embed = discord.Embed(
                title="📊 Database Statistics",
                color=0x2c3e50,
                timestamp=datetime.now()
            )
            
            # Basic stats
            from .utils import format_currency
            embed.add_field(
                name="📈 Overview",
                value=(
                    f"**Total Expenses:** {stats['total_expenses']}\n"
                    f"**Total Amount:** {format_currency(stats['total_amount_rmb'], 'RMB')}\n"
                    f"**Total Documents:** {stats['total_documents']}\n"
                    f"**Next ID:** {stats['next_id']}"
                ),
                inline=True
            )
            
            # Personal totals
            embed.add_field(
                name="👥 Personal Totals",
                value=(
                    f"**Sunil:** {format_currency(stats['sunil_total_gbp'], 'GBP')}\n"
                    f"**Shirin:** {format_currency(stats['shirin_total_aed'], 'AED')}"
                ),
                inline=True
            )
            
            # Date range
            if 'date_range' in stats and stats['date_range']:
                embed.add_field(
                    name="📅 Date Range",
                    value=(
                        f"**From:** {stats['date_range']['earliest']}\n"
                        f"**To:** {stats['date_range']['latest']}"
                    ),
                    inline=True
                )
            
            # Top categories (up to 5)
            if stats['categories']:
                sorted_cats = sorted(stats['categories'].items(), key=lambda x: x[1]['total_rmb'], reverse=True)
                cat_text = []
                for cat, data in sorted_cats[:5]:
                    from .utils import get_expense_emoji
                    emoji = get_expense_emoji(cat)
                    cat_text.append(f"{emoji} {cat}: {data['count']} ({format_currency(data['total_rmb'], 'RMB')})")
                
                embed.add_field(
                    name="🏷️ Top Categories",
                    value="\n".join(cat_text),
                    inline=False
                )
            
            # Top cities (up to 5)
            if stats['cities']:
                sorted_cities = sorted(stats['cities'].items(), key=lambda x: x[1]['total_rmb'], reverse=True)
                city_text = []
                for city, data in sorted_cities[:5]:
                    city_text.append(f"🏙️ {city}: {data['count']} ({format_currency(data['total_rmb'], 'RMB')})")
                
                embed.add_field(
                    name="🗺️ Top Cities",
                    value="\n".join(city_text),
                    inline=False
                )
            
            # Database info
            if stats['created_at']:
                try:
                    created = datetime.fromisoformat(stats['created_at'])
                    updated = datetime.fromisoformat(stats['last_updated'])
                    embed.set_footer(text=f"Created: {created.strftime('%Y-%m-%d')} | Last Updated: {updated.strftime('%Y-%m-%d %H:%M')}")
                except:
                    embed.set_footer(text="Database operational")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating database stats: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="export-data", description="Export all data for backup")
    async def export_data(self, interaction: discord.Interaction):
        """Export all data for backup"""
        try:
            export = self.db.export_data()
            
            # Create a formatted JSON string
            import json
            export_text = json.dumps(export, indent=2, ensure_ascii=False)
            
            # Create embed
            embed = discord.Embed(
                title="💾 Data Export",
                description="Your complete travel expense data backup",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            stats = self.db.get_database_stats()
            embed.add_field(
                name="📊 Export Summary",
                value=(
                    f"**Total Expenses:** {stats['total_expenses']}\n"
                    f"**Total Documents:** {stats['total_documents']}\n"
                    f"**Export Size:** {len(export_text)} characters\n"
                    f"**Export Time:** {export['export_timestamp'][:16]}"
                ),
                inline=False
            )
            
            # Save to file
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
                temp_file = f.name
            
            # Send file
            with open(temp_file, 'rb') as f:
                file = discord.File(f, filename=f"travel_expenses_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                await interaction.response.send_message(embed=embed, file=file)
            
            # Clean up temp file
            os.unlink(temp_file)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error exporting data: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="clear-database", description="⚠️ Clear ALL data permanently")
    @app_commands.describe(
        confirm="Type 'CLEAR ALL DATA' to confirm permanent deletion of everything"
    )
    async def clear_database(self, interaction: discord.Interaction, confirm: str):
        """Clear all data permanently - DANGEROUS OPERATION"""
        try:
            if confirm != "CLEAR ALL DATA":
                await interaction.response.send_message(
                    "❌ To clear all data, you must type exactly 'CLEAR ALL DATA' in the confirm field.\n⚠️ This will permanently delete ALL expenses, documents, and settings.",
                    ephemeral=True
                )
                return
            
            # Get stats before clearing
            stats_before = self.db.get_database_stats()
            
            # Clear data
            success = self.db.clear_all_data()
            
            if success:
                embed = discord.Embed(
                    title="🗑️ Database Cleared",
                    description="All data has been permanently deleted",
                    color=0xe74c3c,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📊 Deleted Data",
                    value=(
                        f"**Expenses:** {stats_before['total_expenses']}\n"
                        f"**Documents:** {stats_before['total_documents']}\n"
                        f"**Categories:** {len(stats_before['categories'])}\n"
                        f"**Cities:** {len(stats_before['cities'])}"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="✅ Fresh Start",
                    value="Database has been reset to initial state. You can now start adding new expenses.",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "❌ Failed to clear database",
                    ephemeral=True
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error clearing database: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="help", description="Complete guide on how to use the travel expense bot")
    @app_commands.describe(
        category="Choose help category (optional) - expense, analysis, documents, utilities, or examples"
    )
    async def help_command(
        self,
        interaction: discord.Interaction,
        category: Optional[Literal["expense", "analysis", "documents", "utilities", "examples"]] = None
    ):
        """Show comprehensive help guide"""
        try:
            if category == "expense":
                embed = self.create_expense_help_embed()
            elif category == "analysis":
                embed = self.create_analysis_help_embed()
            elif category == "documents":
                embed = self.create_documents_help_embed()
            elif category == "utilities":
                embed = self.create_utilities_help_embed()
            elif category == "examples":
                embed = self.create_examples_help_embed()
            else:
                embed = self.create_main_help_embed()
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error showing help: {str(e)}",
                ephemeral=True
            )
    
    def create_main_help_embed(self) -> discord.Embed:
        """Create main help overview embed"""
        embed = discord.Embed(
            title="🤖 Welcome to Shir and Bubba's Travel Tracker!",
            description="Your complete guide to tracking travel expenses across multiple cities with automatic currency conversion",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="💰 Expense Management (4 commands)",
            value=(
                "`/add-expense` - Add new expenses with auto-conversion\n"
                "`/list-expenses` - View recent expenses with IDs\n"
                "`/edit-expense` - Modify existing expenses\n"
                "`/delete-expense` - Remove expenses permanently"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Analysis & Reporting (5 commands)",
            value=(
                "`/summary` - Quick expense overview\n"
                "`/category-breakdown` - Spending by categories\n"
                "`/spending-summary` - Totals in any currency\n"
                "`/trip-itinerary` - Day-by-day timeline\n"
                "`/activity-stats` - Detailed activity statistics"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🌈 Rainbow Charts (2 commands)",
            value=(
                "`/chart-spending` - Beautiful pie charts for spending\n"
                "`/chart-activities` - Colorful pie charts for activities"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📁 Document Management (3 commands)",
            value=(
                "`/upload-document` - Attach receipts to expenses\n"
                "`/list-documents` - View all documents\n"
                "`/delete-document` - Remove documents"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 Utilities & Management (4 commands)",
            value=(
                "`/exchange-rates` - Live currency rates\n"
                "`/database-stats` - System statistics\n"
                "`/export-data` - Backup all data\n"
                "`/clear-database` - Reset everything (⚠️)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💱 Supported Currencies",
            value="RMB (base), GBP (Sunil), AED (Shirin), USD, EUR",
            inline=True
        )
        
        embed.add_field(
            name="🌍 Supported Cities",
            value="Abu Dhabi, Beijing, Shanghai, Guilin, Chengdu, Chongqing, London, Yangshuo",
            inline=True
        )
        
        embed.add_field(
            name="📂 Categories",
            value="Transportation, Accommodation, Food, Activities, Shopping, Official Stuff, Connectivity, Miscellaneous",
            inline=False
        )
        
        embed.add_field(
            name="🚀 Quick Start Examples",
            value=(
                "**Add your first expense:**\n"
                "`/add-expense amount:50 currency:RMB activity:Lunch category:Food city:Beijing payer:Shirin`\n\n"
                "**See your trip overview:**\n"
                "`/summary` or `/activity-stats view:overview`\n\n"
                "**Create beautiful charts:**\n"
                "`/chart-spending chart_type:by-category currency:GBP`\n\n"
                "**Check today's activities:**\n"
                "`/trip-itinerary specific_date:2025-07-28`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔍 Get Detailed Help",
            value=(
                "Use `/help category:expense` for expense commands\n"
                "Use `/help category:analysis` for reporting commands\n"
                "Use `/help category:documents` for document commands\n"
                "Use `/help category:utilities` for system commands\n"
                "Use `/help category:examples` for complete workflows"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 All commands use autocomplete - just start typing and select options!")
        
        return embed
    
    def create_expense_help_embed(self) -> discord.Embed:
        """Create expense management help embed"""
        embed = discord.Embed(
            title="💰 Expense Management Commands",
            description="Add, view, edit, and delete travel expenses",
            color=0x27ae60,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📝 `/add-expense` - Add New Expense",
            value=(
                "**Required:** amount, currency, activity, category, city, payer\n"
                "**Optional:** date (defaults today), notes\n"
                "**Example:** `/add-expense amount:50 currency:RMB activity:Lunch category:Food city:Beijing payer:Sunil`\n"
                "• Automatic currency conversion\n"
                "• Cost splitting: Individual or 50/50 couple\n"
                "• Unique ID assigned for reference"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 `/list-expenses` - View Recent Expenses",
            value=(
                "**Optional:** limit (1-20), city, category\n"
                "**Examples:**\n"
                "• `/list-expenses` (shows last 10)\n"
                "• `/list-expenses limit:20 city:Shanghai`\n"
                "• `/list-expenses category:Food`\n"
                "Shows expense IDs needed for editing/deleting"
            ),
            inline=False
        )
        
        embed.add_field(
            name="✏️ `/edit-expense` - Modify Existing",
            value=(
                "**Required:** expense_id\n"
                "**Optional:** Any field (amount, currency, activity, etc.)\n"
                "**Examples:**\n"
                "• `/edit-expense expense_id:5 amount:60`\n"
                "• `/edit-expense expense_id:3 category:Transportation payer:Shirin`\n"
                "Updates currencies and cost splits automatically"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🗑️ `/delete-expense` - Remove Permanently",
            value=(
                "**Required:** expense_id, confirm (type 'DELETE')\n"
                "**Example:** `/delete-expense expense_id:7 confirm:DELETE`\n"
                "⚠️ **Warning:** This permanently deletes the expense!\n"
                "Safety confirmation required to prevent accidents"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Use /list-expenses to find expense IDs before editing or deleting")
        
        return embed
    
    def create_analysis_help_embed(self) -> discord.Embed:
        """Create analysis and reporting help embed"""
        embed = discord.Embed(
            title="📊 Analysis & Reporting Commands",
            description="Comprehensive expense analysis and trip reporting",
            color=0xe74c3c,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📈 `/summary` - Quick Overview",
            value=(
                "**Optional:** city, start_date, end_date\n"
                "**Examples:**\n"
                "• `/summary` (all expenses)\n"
                "• `/summary city:Chengdu`\n"
                "• `/summary start_date:2025-02-01 end_date:2025-02-28`\n"
                "Shows totals, recent transactions, city breakdown"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🏷️ `/category-breakdown` - Category Analysis",
            value=(
                "**Optional:** city, start_date, end_date\n"
                "**Examples:**\n"
                "• `/category-breakdown` (all categories)\n"
                "• `/category-breakdown city:Guilin`\n"
                "Shows detailed spending by Food, Transport, etc.\n"
                "Includes per-person totals and transaction counts"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💱 `/spending-summary` - Flexible Currency View",
            value=(
                "**Required:** currency, grouping (person/category)\n"
                "**Optional:** city, start_date, end_date\n"
                "**Examples:**\n"
                "• `/spending-summary currency:GBP grouping:person`\n"
                "• `/spending-summary currency:AED grouping:category city:Abu Dhabi`\n"
                "View totals in ANY currency with live conversion"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🗓️ `/trip-itinerary` - Day-by-Day Timeline",
            value=(
                "**Optional:** city, start_date, end_date, specific_date\n"
                "**Examples:**\n"
                "• `/trip-itinerary` (full trip)\n"
                "• `/trip-itinerary specific_date:2025-02-15` (single day)\n"
                "• `/trip-itinerary start_date:2025-02-10 end_date:2025-02-20`\n"
                "Complete timeline with activities, costs, notes"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 `/activity-stats` - Detailed Activity Statistics",
            value=(
                "**Required:** view (overview/by-date/by-category/by-city)\n"
                "**Optional:** city, start_date, end_date\n"
                "**Examples:**\n"
                "• `/activity-stats view:overview` (total activities & patterns)\n"
                "• `/activity-stats view:by-date` (daily activity breakdown)\n"
                "• `/activity-stats view:by-category city:Beijing`\n"
                "Shows activity counts, percentages, and analysis"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📅 Date Format",
            value="Always use **YYYY-MM-DD** format (e.g., 2025-02-15)",
            inline=False
        )
        
        embed.set_footer(text="💡 Combine filters for precise analysis - city + date range works on all commands")
        
        return embed
    
    def create_documents_help_embed(self) -> discord.Embed:
        """Create document management help embed"""
        embed = discord.Embed(
            title="📁 Document Management Commands",
            description="Upload, view, and manage receipts and documents",
            color=0x9b59b6,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📎 `/upload-document` - Attach Files",
            value=(
                "**Required:** expense_id, document (file attachment)\n"
                "**Example:** `/upload-document expense_id:4 document:[attach file]`\n"
                "**Supported:** PDF, images, text files\n"
                "• Links documents to specific expenses\n"
                "• Automatic file type detection\n"
                "• Stores upload timestamp and metadata"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 `/list-documents` - View All Documents",
            value=(
                "**Optional:** limit (1-20, default 10)\n"
                "**Example:** `/list-documents limit:15`\n"
                "**Shows:**\n"
                "• Filename and file type\n"
                "• Associated expense ID and details\n"
                "• Upload date and time\n"
                "• Expense activity and city"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🗑️ `/delete-document` - Remove Files",
            value=(
                "**Required:** expense_id, filename\n"
                "**Example:** `/delete-document expense_id:4 filename:receipt_lunch.pdf`\n"
                "• Removes document from expense\n"
                "• Use exact filename from document list\n"
                "• Expense remains, only document is deleted"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Best Practices",
            value=(
                "• Upload receipts immediately after adding expenses\n"
                "• Use descriptive filenames (e.g., 'hotel_receipt_beijing.pdf')\n"
                "• Use `/list-documents` to find exact filenames for deletion\n"
                "• Keep important documents backed up separately"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Find expense IDs with /list-expenses before uploading documents")
        
        return embed
    
    def create_utilities_help_embed(self) -> discord.Embed:
        """Create utilities and management help embed"""
        embed = discord.Embed(
            title="🔧 Utilities & Management Commands",
            description="System utilities, rates, statistics, and data management",
            color=0xf39c12,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="💱 `/exchange-rates` - Live Currency Rates",
            value=(
                "**No parameters needed**\n"
                "**Shows:**\n"
                "• Current rates from 1 RMB to all currencies\n"
                "• Reverse rates (£1 = ¥X.XX RMB)\n"
                "• Last update timestamp\n"
                "• Updates automatically every 4 hours"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 `/database-stats` - System Statistics",
            value=(
                "**No parameters needed**\n"
                "**Shows:**\n"
                "• Total expenses and amounts\n"
                "• Personal spending totals (Sunil/Shirin)\n"
                "• Top categories and cities\n"
                "• Document counts and date ranges\n"
                "• Database creation and update times"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💾 `/export-data` - Backup Everything",
            value=(
                "**No parameters needed**\n"
                "**Features:**\n"
                "• Downloads complete data as JSON file\n"
                "• Includes all expenses and documents\n"
                "• Timestamped backup filename\n"
                "• Full restore capability"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🗑️ `/clear-database` - Reset Everything",
            value=(
                "**Required:** confirm (type 'CLEAR ALL DATA')\n"
                "**⚠️ DANGER:** Permanently deletes ALL data!\n"
                "• Removes all expenses\n"
                "• Deletes all documents\n"
                "• Resets to fresh database\n"
                "• Cannot be undone!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛡️ Safety Features",
            value=(
                "• Strong confirmation required for destructive actions\n"
                "• Regular data backups recommended\n"
                "• Live exchange rate fallbacks\n"
                "• Comprehensive error handling"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Export data regularly for backup safety!")
        
        return embed
    
    def create_examples_help_embed(self) -> discord.Embed:
        """Create usage examples help embed"""
        embed = discord.Embed(
            title="🎯 Usage Examples & Workflows",
            description="Real-world examples and best practices",
            color=0x2c3e50,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📅 Complete Daily Workflow",
            value=(
                "**Morning Planning:**\n"
                "• `/exchange-rates` - Check today's conversion rates\n"
                "• `/trip-itinerary specific_date:2025-07-28` - See today's plans\n\n"
                "**Adding Expenses Throughout Day:**\n"
                "• `/add-expense amount:200 currency:RMB activity:Train to Shanghai category:Transportation city:Shanghai payer:Bubba`\n"
                "• `/add-expense amount:80 currency:RMB activity:Hotel check-in category:Accommodation city:Shanghai payer:Couple`\n"
                "• `/upload-document expense_id:1 document:[train_ticket.pdf]` (attach receipt)\n\n"
                "**Evening Review:**\n"
                "• `/activity-stats view:by-date` - See today's activity summary"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Weekend Trip Analysis",
            value=(
                "**Check Your Spending Patterns:**\n"
                "• `/spending-summary currency:GBP grouping:person start_date:2025-07-21 end_date:2025-07-27` - See Shir vs Bubba totals\n"
                "• `/category-breakdown start_date:2025-07-21 end_date:2025-07-27` - What you spent most on\n"
                "• `/activity-stats view:by-category` - Activity breakdown by type\n\n"
                "**Compare Cities:**\n"
                "• `/activity-stats view:by-city` - Which cities you were most active in\n"
                "• `/spending-summary currency:AED grouping:category city:Abu Dhabi` - Dubai spending in dirhams\n\n"
                "**Backup Your Data:**\n"
                "• `/export-data` - Download complete trip backup"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🗺️ Trip Planning & Budget Check",
            value=(
                "**Before You Travel:**\n"
                "• `/exchange-rates` - Check current RMB, GBP, AED rates\n"
                "• `/database-stats` - See your overall trip progress\n\n"
                "**City-Specific Planning:**\n"
                "• `/trip-itinerary city:Beijing` - Review all Beijing activities\n"
                "• `/spending-summary currency:RMB grouping:category city:Shanghai` - Shanghai budget check\n"
                "• `/activity-stats view:by-city` - Compare all cities\n\n"
                "**Budget Monitoring:**\n"
                "• `/spending-summary currency:GBP grouping:person` - See Shir vs Bubba spending in pounds\n"
                "• `/category-breakdown` - Track spending by Food, Transport, etc."
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 Expense Management Examples",
            value=(
                "**Find & Edit:**\n"
                "• `/list-expenses category:Food` → Find food expenses\n"
                "• `/edit-expense expense_id:5 amount:75` → Fix amount\n\n"
                "**Document Management:**\n"
                "• `/list-documents` → Find document names\n"
                "• `/delete-document expense_id:3 filename:old_receipt.pdf`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Pro Tips",
            value=(
                "• Use consistent activity descriptions for better tracking\n"
                "• Add notes to expenses for important details\n"
                "• Upload receipts immediately after adding expenses\n"
                "• Check `/exchange-rates` before adding foreign currency expenses\n"
                "• Use date filters for focused analysis\n"
                "• Export data regularly for backup safety"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎬 Real Travel Scenarios",
            value=(
                "**Shared Hotel Room:**\n"
                "`/add-expense amount:300 currency:RMB activity:Hotel night category:Accommodation city:Chengdu payer:Couple`\n\n"
                "**Shir Buys Train Tickets:**\n"
                "`/add-expense amount:150 currency:RMB activity:High-speed rail Beijing-Shanghai category:Transportation city:Beijing payer:Shir`\n\n"
                "**Bubba Pays for Dinner:**\n"
                "`/add-expense amount:45 currency:GBP activity:Chinese hotpot dinner category:Food city:London payer:Bubba notes:Amazing Sichuan place`\n\n"
                "**Buying Souvenirs:**\n"
                "`/add-expense amount:25 currency:AED activity:Traditional crafts category:Shopping city:Abu Dhabi payer:Shir`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Important Tips for Shir & Bubba",
            value=(
                "• **Use `payer:Couple`** when you split costs 50/50\n"
                "• **Date format:** Always YYYY-MM-DD (like 2025-07-28)\n"
                "• **Currencies:** RMB, GBP (pounds), AED (dirhams), USD, EUR\n"
                "• **Cities:** Use full names (Abu Dhabi, not just Dubai)\n"
                "• **Activities:** Be specific ('Dim sum lunch' vs just 'Food')\n"
                "• **Documents:** Upload receipts right after adding expenses"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Start with /add-expense and /summary to get familiar with the bot!")
        
        return embed
    
    @app_commands.command(name="activity-stats", description="Detailed activity statistics for your trip")
    @app_commands.describe(
        view="Choose view type",
        city="Filter by specific city (optional)",
        start_date="Start date (YYYY-MM-DD format, optional)",
        end_date="End date (YYYY-MM-DD format, optional)"
    )
    async def activity_stats(
        self,
        interaction: discord.Interaction,
        view: Literal["overview", "by-date", "by-category", "by-city"] = "overview",
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Show detailed activity statistics"""
        try:
            # Validate dates if provided
            if start_date:
                try:
                    datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid start_date format. Use YYYY-MM-DD (e.g., 2025-02-15)",
                        ephemeral=True
                    )
                    return
            
            if end_date:
                try:
                    datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid end_date format. Use YYYY-MM-DD (e.g., 2025-02-15)",
                        ephemeral=True
                    )
                    return
            
            # Get filtered expenses
            expenses = database.get_expenses(
                city=city,
                start_date=start_date,
                end_date=end_date
            )
            
            if not expenses:
                filter_text = []
                if city:
                    filter_text.append(f"city: {city}")
                if start_date:
                    filter_text.append(f"from: {start_date}")
                if end_date:
                    filter_text.append(f"to: {end_date}")
                
                filter_str = f" ({', '.join(filter_text)})" if filter_text else ""
                await interaction.response.send_message(
                    f"📊 No activities found{filter_str}",
                    ephemeral=True
                )
                return
            
            # Create appropriate embed based on view type
            if view == "overview":
                embed = self.create_activity_overview_embed(expenses, city, start_date, end_date)
            elif view == "by-date":
                embed = self.create_activity_by_date_embed(expenses, city, start_date, end_date)
            elif view == "by-category":
                embed = self.create_activity_by_category_embed(expenses, city, start_date, end_date)
            elif view == "by-city":
                embed = self.create_activity_by_city_embed(expenses, city, start_date, end_date)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating activity stats: {str(e)}",
                ephemeral=True
            )
    
    def create_activity_overview_embed(self, expenses: List[Dict], city: str, start_date: str, end_date: str) -> discord.Embed:
        """Create activity overview statistics embed"""
        total_activities = len(expenses)
        
        # Count by categories
        category_counts = {}
        city_counts = {}
        date_counts = {}
        
        for expense in expenses:
            # Category counts
            category = expense['category']
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # City counts
            exp_city = expense['city']
            city_counts[exp_city] = city_counts.get(exp_city, 0) + 1
            
            # Date counts
            date = expense['date']
            date_counts[date] = date_counts.get(date, 0) + 1
        
        # Create filter description
        filter_parts = []
        if city:
            filter_parts.append(f"City: {city}")
        if start_date:
            filter_parts.append(f"From: {start_date}")
        if end_date:
            filter_parts.append(f"To: {end_date}")
        
        filter_desc = f" ({', '.join(filter_parts)})" if filter_parts else " (All activities)"
        
        embed = discord.Embed(
            title=f"📊 Activity Statistics Overview{filter_desc}",
            description=f"**Total Activities:** {total_activities}",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        # Top categories
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        category_text = "\n".join([f"• **{cat}**: {count} activities" for cat, count in top_categories])
        embed.add_field(
            name="🏷️ Top Categories",
            value=category_text or "No activities",
            inline=True
        )
        
        # Top cities
        top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        city_text = "\n".join([f"• **{cty}**: {count} activities" for cty, count in top_cities])
        embed.add_field(
            name="🌍 Cities Visited",
            value=city_text or "No activities",
            inline=True
        )
        
        # Date range info
        if date_counts:
            dates = sorted(date_counts.keys())
            first_date = dates[0]
            last_date = dates[-1]
            unique_days = len(date_counts)
            avg_per_day = round(total_activities / unique_days, 1)
            
            date_info = (
                f"• **First Activity:** {first_date}\n"
                f"• **Last Activity:** {last_date}\n"
                f"• **Active Days:** {unique_days}\n"
                f"• **Avg per Day:** {avg_per_day}"
            )
        else:
            date_info = "No date information"
        
        embed.add_field(
            name="📅 Date Summary",
            value=date_info,
            inline=False
        )
        
        embed.add_field(
            name="📈 Quick Analysis",
            value=(
                f"• **Categories Used:** {len(category_counts)}/8 total\n"
                f"• **Cities Visited:** {len(city_counts)}\n"
                f"• **Most Active Category:** {top_categories[0][0] if top_categories else 'None'}\n"
                f"• **Most Visited City:** {top_cities[0][0] if top_cities else 'None'}"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Use different view types: by-date, by-category, by-city for detailed breakdowns")
        
        return embed
    
    def create_activity_by_date_embed(self, expenses: List[Dict], city: str, start_date: str, end_date: str) -> discord.Embed:
        """Create activity by date statistics embed"""
        # Group by date
        date_activities = {}
        for expense in expenses:
            date = expense['date']
            if date not in date_activities:
                date_activities[date] = []
            date_activities[date].append(expense)
        
        # Create filter description
        filter_parts = []
        if city:
            filter_parts.append(f"City: {city}")
        if start_date:
            filter_parts.append(f"From: {start_date}")
        if end_date:
            filter_parts.append(f"To: {end_date}")
        
        filter_desc = f" ({', '.join(filter_parts)})" if filter_parts else ""
        
        embed = discord.Embed(
            title=f"📅 Activity Statistics by Date{filter_desc}",
            description=f"**Total Activities:** {len(expenses)} across {len(date_activities)} days",
            color=0xe74c3c,
            timestamp=datetime.now()
        )
        
        # Sort dates and show daily breakdown
        sorted_dates = sorted(date_activities.keys())
        
        # Show up to 10 most recent days to avoid Discord limits
        recent_dates = sorted_dates[-10:] if len(sorted_dates) > 10 else sorted_dates
        
        for date in recent_dates:
            day_expenses = date_activities[date]
            day_count = len(day_expenses)
            
            # Count categories for this day
            day_categories = {}
            day_cities = set()
            for exp in day_expenses:
                cat = exp['category']
                day_categories[cat] = day_categories.get(cat, 0) + 1
                day_cities.add(exp['city'])
            
            # Format day info
            category_info = ", ".join([f"{cat}({count})" for cat, count in sorted(day_categories.items())])
            city_info = ", ".join(sorted(day_cities))
            
            day_value = (
                f"**{day_count} activities**\n"
                f"🏷️ {category_info}\n"
                f"🌍 {city_info}"
            )
            
            embed.add_field(
                name=f"📅 {date}",
                value=day_value,
                inline=True
            )
        
        # Add summary if showing truncated data
        if len(sorted_dates) > 10:
            embed.add_field(
                name="📊 Note",
                value=f"Showing most recent 10 days. Total trip spans {len(sorted_dates)} days from {sorted_dates[0]} to {sorted_dates[-1]}",
                inline=False
            )
        
        # Most/least active days
        activity_counts = [(date, len(activities)) for date, activities in date_activities.items()]
        most_active = max(activity_counts, key=lambda x: x[1])
        least_active = min(activity_counts, key=lambda x: x[1])
        avg_per_day = round(len(expenses) / len(date_activities), 1)
        
        embed.add_field(
            name="📈 Daily Analysis",
            value=(
                f"• **Most Active Day:** {most_active[0]} ({most_active[1]} activities)\n"
                f"• **Least Active Day:** {least_active[0]} ({least_active[1]} activities)\n"
                f"• **Average per Day:** {avg_per_day} activities"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Use specific date ranges to focus on particular periods")
        
        return embed
    
    def create_activity_by_category_embed(self, expenses: List[Dict], city: str, start_date: str, end_date: str) -> discord.Embed:
        """Create activity by category statistics embed"""
        # Group by category
        category_activities = {}
        for expense in expenses:
            category = expense['category']
            if category not in category_activities:
                category_activities[category] = []
            category_activities[category].append(expense)
        
        # Create filter description
        filter_parts = []
        if city:
            filter_parts.append(f"City: {city}")
        if start_date:
            filter_parts.append(f"From: {start_date}")
        if end_date:
            filter_parts.append(f"To: {end_date}")
        
        filter_desc = f" ({', '.join(filter_parts)})" if filter_parts else ""
        
        embed = discord.Embed(
            title=f"🏷️ Activity Statistics by Category{filter_desc}",
            description=f"**Total Activities:** {len(expenses)} across {len(category_activities)} categories",
            color=0x27ae60,
            timestamp=datetime.now()
        )
        
        # Sort categories by activity count
        sorted_categories = sorted(category_activities.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, cat_expenses in sorted_categories:
            count = len(cat_expenses)
            percentage = round((count / len(expenses)) * 100, 1)
            
            # Find unique cities and dates for this category
            cities = set(exp['city'] for exp in cat_expenses)
            dates = set(exp['date'] for exp in cat_expenses)
            
            # Calculate total spending in RMB for this category
            total_rmb = sum(exp['amount_rmb'] for exp in cat_expenses)
            
            category_value = (
                f"**{count} activities** ({percentage}% of trip)\n"
                f"💰 {format_currency(total_rmb, 'RMB')}\n"
                f"🌍 {len(cities)} cities: {', '.join(sorted(cities))}\n"
                f"📅 {len(dates)} days active"
            )
            
            # Category emojis
            category_emojis = {
                'Transportation': '🚗',
                'Accommodation': '🏨', 
                'Food': '🍽️',
                'Activities': '🎯',
                'Shopping': '🛍️',
                'Official Stuff': '📋',
                'Connectivity': '📶',
                'Miscellaneous': '📦'
            }
            
            emoji = category_emojis.get(category, '📂')
            
            embed.add_field(
                name=f"{emoji} {category}",
                value=category_value,
                inline=True
            )
        
        # Category efficiency analysis
        if len(sorted_categories) > 1:
            most_used = sorted_categories[0]
            least_used = sorted_categories[-1]
            avg_per_category = round(len(expenses) / len(category_activities), 1)
            
            embed.add_field(
                name="📊 Category Analysis",
                value=(
                    f"• **Most Used:** {most_used[0]} ({len(most_used[1])} activities)\n"
                    f"• **Least Used:** {least_used[0]} ({len(least_used[1])} activities)\n"
                    f"• **Average per Category:** {avg_per_category} activities\n"
                    f"• **Categories Active:** {len(category_activities)}/8 total"
                ),
                inline=False
            )
        
        embed.set_footer(text="💡 Category breakdown shows your trip's activity patterns")
        
        return embed
    
    def create_activity_by_city_embed(self, expenses: List[Dict], city: str, start_date: str, end_date: str) -> discord.Embed:
        """Create activity by city statistics embed"""
        # Group by city
        city_activities = {}
        for expense in expenses:
            exp_city = expense['city']
            if exp_city not in city_activities:
                city_activities[exp_city] = []
            city_activities[exp_city].append(expense)
        
        # Create filter description
        filter_parts = []
        if city:
            filter_parts.append(f"City: {city}")
        if start_date:
            filter_parts.append(f"From: {start_date}")
        if end_date:
            filter_parts.append(f"To: {end_date}")
        
        filter_desc = f" ({', '.join(filter_parts)})" if filter_parts else ""
        
        embed = discord.Embed(
            title=f"🌍 Activity Statistics by City{filter_desc}",
            description=f"**Total Activities:** {len(expenses)} across {len(city_activities)} cities",
            color=0x9b59b6,
            timestamp=datetime.now()
        )
        
        # Sort cities by activity count
        sorted_cities = sorted(city_activities.items(), key=lambda x: len(x[1]), reverse=True)
        
        for city_name, city_expenses in sorted_cities:
            count = len(city_expenses)
            percentage = round((count / len(expenses)) * 100, 1)
            
            # Find unique categories and dates for this city
            categories = {}
            dates = set(exp['date'] for exp in city_expenses)
            
            for exp in city_expenses:
                cat = exp['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            # Calculate total spending in RMB for this city
            total_rmb = sum(exp['amount_rmb'] for exp in city_expenses)
            
            # Top categories for this city
            top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            cat_text = ", ".join([f"{cat}({cnt})" for cat, cnt in top_cats])
            
            city_value = (
                f"**{count} activities** ({percentage}% of trip)\n"
                f"💰 {format_currency(total_rmb, 'RMB')}\n"
                f"🏷️ {cat_text}\n"
                f"📅 {len(dates)} days visited"
            )
            
            # City flag emojis
            city_flags = {
                'Beijing': '🇨🇳',
                'Shanghai': '🇨🇳',
                'Guilin': '🇨🇳',
                'Chengdu': '🇨🇳',
                'Chongqing': '🇨🇳',
                'Yangshuo': '🇨🇳',
                'London': '🇬🇧',
                'Abu Dhabi': '🇦🇪'
            }
            
            flag = city_flags.get(city_name, '🏙️')
            
            embed.add_field(
                name=f"{flag} {city_name}",
                value=city_value,
                inline=True
            )
        
        # City analysis
        if len(sorted_cities) > 1:
            most_visited = sorted_cities[0]
            least_visited = sorted_cities[-1]
            avg_per_city = round(len(expenses) / len(city_activities), 1)
            
            embed.add_field(
                name="📊 City Analysis",
                value=(
                    f"• **Most Active:** {most_visited[0]} ({len(most_visited[1])} activities)\n"
                    f"• **Least Active:** {least_visited[0]} ({len(least_visited[1])} activities)\n"
                    f"• **Average per City:** {avg_per_city} activities\n"
                    f"• **Cities Visited:** {len(city_activities)}/8 available"
                ),
                inline=False
            )
        
        embed.set_footer(text="💡 City breakdown shows your travel activity distribution")
        
        return embed
    
    @app_commands.command(name="chart-spending", description="Beautiful rainbow pie chart of spending breakdown")
    @app_commands.describe(
        chart_type="Type of spending chart to generate",
        currency="Currency to display amounts in",
        city="Filter by specific city (optional)",
        start_date="Start date (YYYY-MM-DD format, optional)",
        end_date="End date (YYYY-MM-DD format, optional)"
    )
    async def chart_spending(
        self,
        interaction: discord.Interaction,
        chart_type: Literal["by-category", "by-city", "by-person"] = "by-category",
        currency: Literal["RMB", "GBP", "AED"] = "RMB",
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Generate rainbow pie charts for spending analysis"""
        try:
            # Validate dates if provided
            if start_date:
                try:
                    datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid start_date format. Use YYYY-MM-DD (e.g., 2025-07-28)",
                        ephemeral=True
                    )
                    return
            
            if end_date:
                try:
                    datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid end_date format. Use YYYY-MM-DD (e.g., 2025-07-28)",
                        ephemeral=True
                    )
                    return
            
            await interaction.response.defer()  # Charts take time to generate
            
            # Get filtered expenses
            expenses = self.db.get_expenses(
                city=city,
                start_date=start_date,
                end_date=end_date
            )
            
            if not expenses:
                filter_text = []
                if city:
                    filter_text.append(f"city: {city}")
                if start_date:
                    filter_text.append(f"from: {start_date}")
                if end_date:
                    filter_text.append(f"to: {end_date}")
                
                filter_str = f" ({', '.join(filter_text)})" if filter_text else ""
                await interaction.followup.send(f"📊 No expenses found{filter_str}")
                return
            
            # Create filter suffix for title
            filter_parts = []
            if city:
                filter_parts.append(f" in {city}")
            if start_date and end_date:
                filter_parts.append(f" ({start_date} to {end_date})")
            elif start_date:
                filter_parts.append(f" (from {start_date})")
            elif end_date:
                filter_parts.append(f" (to {end_date})")
            
            title_suffix = "".join(filter_parts)
            
            # Generate appropriate chart
            if chart_type == "by-category":
                chart_buffer = self.charts.create_spending_by_category_chart(expenses, currency, title_suffix)
            elif chart_type == "by-city":
                chart_buffer = self.charts.create_spending_by_city_chart(expenses, currency, title_suffix)
            elif chart_type == "by-person":
                chart_buffer = self.charts.create_spending_by_person_chart(expenses, currency, title_suffix)
            
            if chart_buffer is None:
                await interaction.followup.send("❌ Unable to generate chart - no data available")
                return
            
            # Create Discord file
            file = discord.File(chart_buffer, filename=f"spending_chart_{chart_type}_{currency.lower()}.png")
            
            # Create embed with chart info
            embed = discord.Embed(
                title="🌈 Rainbow Spending Chart Generated!",
                description=f"**Chart Type:** {chart_type.replace('-', ' ').title()}\n**Currency:** {currency}\n**Total Expenses:** {len(expenses)}",
                color=0xFF69B4,
                timestamp=datetime.now()
            )
            
            if filter_parts:
                embed.add_field(name="Filters Applied", value=title_suffix.strip(), inline=False)
            
            embed.set_image(url=f"attachment://spending_chart_{chart_type}_{currency.lower()}.png")
            embed.set_footer(text="💡 Use different chart types and currencies to explore your data!")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating chart: {str(e)}")
    
    @app_commands.command(name="chart-activities", description="Rainbow pie chart of activity counts")
    @app_commands.describe(
        chart_type="Type of activity chart to generate",
        city="Filter by specific city (optional)",
        start_date="Start date (YYYY-MM-DD format, optional)",
        end_date="End date (YYYY-MM-DD format, optional)"
    )
    async def chart_activities(
        self,
        interaction: discord.Interaction,
        chart_type: Literal["by-category", "by-city"] = "by-category",
        city: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Generate rainbow pie charts for activity analysis"""
        try:
            # Validate dates if provided
            if start_date:
                try:
                    datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid start_date format. Use YYYY-MM-DD (e.g., 2025-07-28)",
                        ephemeral=True
                    )
                    return
            
            if end_date:
                try:
                    datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid end_date format. Use YYYY-MM-DD (e.g., 2025-07-28)",
                        ephemeral=True
                    )
                    return
            
            await interaction.response.defer()  # Charts take time to generate
            
            # Get filtered expenses
            expenses = self.db.get_expenses(
                city=city,
                start_date=start_date,
                end_date=end_date
            )
            
            if not expenses:
                filter_text = []
                if city:
                    filter_text.append(f"city: {city}")
                if start_date:
                    filter_text.append(f"from: {start_date}")
                if end_date:
                    filter_text.append(f"to: {end_date}")
                
                filter_str = f" ({', '.join(filter_text)})" if filter_text else ""
                await interaction.followup.send(f"📊 No activities found{filter_str}")
                return
            
            # Create filter suffix for title
            filter_parts = []
            if city:
                filter_parts.append(f" in {city}")
            if start_date and end_date:
                filter_parts.append(f" ({start_date} to {end_date})")
            elif start_date:
                filter_parts.append(f" (from {start_date})")
            elif end_date:
                filter_parts.append(f" (to {end_date})")
            
            title_suffix = "".join(filter_parts)
            
            # Generate appropriate chart
            if chart_type == "by-category":
                chart_buffer = self.charts.create_activities_by_category_chart(expenses, title_suffix)
            elif chart_type == "by-city":
                chart_buffer = self.charts.create_activities_by_city_chart(expenses, title_suffix)
            
            if chart_buffer is None:
                await interaction.followup.send("❌ Unable to generate chart - no data available")
                return
            
            # Create Discord file
            file = discord.File(chart_buffer, filename=f"activity_chart_{chart_type}.png")
            
            # Create embed with chart info
            embed = discord.Embed(
                title="🌈 Rainbow Activity Chart Generated!",
                description=f"**Chart Type:** {chart_type.replace('-', ' ').title()}\n**Total Activities:** {len(expenses)}",
                color=0x9B59B6,
                timestamp=datetime.now()
            )
            
            if filter_parts:
                embed.add_field(name="Filters Applied", value=title_suffix.strip(), inline=False)
            
            embed.set_image(url=f"attachment://activity_chart_{chart_type}.png")
            embed.set_footer(text="💡 Visual breakdown of your travel activities!")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating chart: {str(e)}")
