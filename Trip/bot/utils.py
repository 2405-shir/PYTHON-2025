import discord
from datetime import datetime
from typing import List, Dict, Optional
import re

def validate_date(date_string: str) -> bool:
    """Validate date string in YYYY-MM-DD format"""
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def format_currency(amount: float, currency: str) -> str:
    """Format currency with appropriate symbol"""
    symbols = {
        'RMB': '¥',
        'CNY': '¥',
        'GBP': '£',
        'AED': 'AED ',
        'USD': '$',
        'EUR': '€'
    }
    
    symbol = symbols.get(currency, '')
    if currency == 'AED':
        return f"{symbol}{amount:,.2f}"
    else:
        return f"{symbol}{amount:,.2f}"

def create_summary_embed(expenses: List[Dict], city: Optional[str] = None, 
                        start_date: Optional[str] = None, end_date: Optional[str] = None) -> discord.Embed:
    """Create summary embed for expenses"""
    
    # Calculate totals
    total_rmb = sum(exp['total_rmb'] for exp in expenses)
    sunil_rmb = sum(exp['sunil_rmb'] for exp in expenses)
    sunil_gbp = sum(exp['sunil_gbp'] for exp in expenses)
    shirin_rmb = sum(exp['shirin_rmb'] for exp in expenses)
    shirin_aed = sum(exp['shirin_aed'] for exp in expenses)
    
    # Create embed
    embed = discord.Embed(
        title="📊 Travel Expense Summary",
        color=0x3498db,
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
    
    # Total expenses
    embed.add_field(
        name="📈 Total Expenses", 
        value=f"**{len(expenses)}** transactions\n{format_currency(total_rmb, 'RMB')}", 
        inline=True
    )
    
    # Sunil's expenses
    embed.add_field(
        name="👨 Sunil's Share",
        value=f"{format_currency(sunil_rmb, 'RMB')}\n{format_currency(sunil_gbp, 'GBP')}",
        inline=True
    )
    
    # Shirin's expenses
    embed.add_field(
        name="👩 Shirin's Share",
        value=f"{format_currency(shirin_rmb, 'RMB')}\n{format_currency(shirin_aed, 'AED')}",
        inline=True
    )
    
    # City breakdown (if not filtered by city)
    if not city and expenses:
        cities = {}
        for exp in expenses:
            city_name = exp['city']
            if city_name not in cities:
                cities[city_name] = 0
            cities[city_name] += exp['total_rmb']
        
        city_breakdown = []
        for city_name, amount in sorted(cities.items(), key=lambda x: x[1], reverse=True):
            city_breakdown.append(f"{city_name}: {format_currency(amount, 'RMB')}")
        
        if city_breakdown:
            embed.add_field(
                name="🏙️ By City",
                value="\n".join(city_breakdown[:5]),  # Show top 5 cities
                inline=False
            )
    
    # Recent expenses
    if expenses:
        recent_expenses = expenses[:5]  # Get 5 most recent
        recent_list = []
        for exp in recent_expenses:
            recent_list.append(
                f"**{exp['date']}** - {exp['city']}\n"
                f"{exp['activity']} ({exp['category']})\n"
                f"{format_currency(exp['total_rmb'], 'RMB')}"
            )
        
        embed.add_field(
            name="🕒 Recent Expenses",
            value="\n\n".join(recent_list),
            inline=False
        )
    
    # Date range
    if expenses:
        dates = [exp['date'] for exp in expenses]
        embed.set_footer(text=f"Date range: {min(dates)} to {max(dates)}")
    
    return embed

def create_breakdown_embed(expenses: List[Dict], city: Optional[str] = None,
                          start_date: Optional[str] = None, end_date: Optional[str] = None) -> discord.Embed:
    """Create category breakdown embed"""
    
    # Calculate category breakdown
    categories = {}
    for exp in expenses:
        cat = exp['category']
        if cat not in categories:
            categories[cat] = {
                'count': 0,
                'total_rmb': 0,
                'sunil_rmb': 0,
                'sunil_gbp': 0,
                'shirin_rmb': 0,
                'shirin_aed': 0
            }
        
        categories[cat]['count'] += 1
        categories[cat]['total_rmb'] += exp['total_rmb']
        categories[cat]['sunil_rmb'] += exp['sunil_rmb']
        categories[cat]['sunil_gbp'] += exp['sunil_gbp']
        categories[cat]['shirin_rmb'] += exp['shirin_rmb']
        categories[cat]['shirin_aed'] += exp['shirin_aed']
    
    # Create embed
    embed = discord.Embed(
        title="📊 Category Breakdown",
        color=0xe74c3c,
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
    
    # Sort categories by total amount
    sorted_categories = sorted(categories.items(), key=lambda x: x[1]['total_rmb'], reverse=True)
    
    # Add category breakdown
    for category, data in sorted_categories:
        category_text = (
            f"**Total:** {format_currency(data['total_rmb'], 'RMB')} ({data['count']} transactions)\n"
            f"**Sunil:** {format_currency(data['sunil_rmb'], 'RMB')} ({format_currency(data['sunil_gbp'], 'GBP')})\n"
            f"**Shirin:** {format_currency(data['shirin_rmb'], 'RMB')} ({format_currency(data['shirin_aed'], 'AED')})"
        )
        
        # Use emoji for categories
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
        
        emoji = category_emojis.get(category, '📊')
        embed.add_field(
            name=f"{emoji} {category}",
            value=category_text,
            inline=True
        )
    
    # Total summary
    total_rmb = sum(cat['total_rmb'] for cat in categories.values())
    total_sunil_gbp = sum(cat['sunil_gbp'] for cat in categories.values())
    total_shirin_aed = sum(cat['shirin_aed'] for cat in categories.values())
    
    embed.add_field(
        name="💰 Grand Total",
        value=(
            f"**Combined:** {format_currency(total_rmb, 'RMB')}\n"
            f"**Sunil:** {format_currency(total_sunil_gbp, 'GBP')}\n"
            f"**Shirin:** {format_currency(total_shirin_aed, 'AED')}"
        ),
        inline=False
    )
    
    return embed

def format_expense_list(expenses: List[Dict], limit: int = 10) -> str:
    """Format expense list for display"""
    if not expenses:
        return "No expenses found."
    
    formatted = []
    for i, exp in enumerate(expenses[:limit]):
        formatted.append(
            f"**{i+1}.** {exp['date']} - {exp['city']}\n"
            f"   {exp['activity']} ({exp['category']})\n"
            f"   {format_currency(exp['total_rmb'], 'RMB')} - {exp['payer']}"
        )
    
    if len(expenses) > limit:
        formatted.append(f"\n... and {len(expenses) - limit} more expenses")
    
    return "\n\n".join(formatted)

def get_expense_emoji(category: str) -> str:
    """Get emoji for expense category"""
    emojis = {
        'Transportation': '🚗',
        'Accommodation': '🏨',
        'Food': '🍽️',
        'Activities': '🎯',
        'Shopping': '🛍️',
        'Official Stuff': '📋',
        'Connectivity': '📶',
        'Miscellaneous': '📦'
    }
    return emojis.get(category, '📊')

def create_itinerary_embed(expenses: List[Dict], city: Optional[str] = None,
                          start_date: Optional[str] = None, end_date: Optional[str] = None) -> discord.Embed:
    """Create comprehensive trip itinerary embed organized by date"""
    
    # Group expenses by date
    daily_expenses = {}
    for exp in expenses:
        date = exp['date']
        if date not in daily_expenses:
            daily_expenses[date] = []
        daily_expenses[date].append(exp)
    
    # Sort dates
    sorted_dates = sorted(daily_expenses.keys())
    
    # Calculate trip totals
    trip_total_rmb = sum(exp['total_rmb'] for exp in expenses)
    trip_sunil_gbp = sum(exp['sunil_gbp'] for exp in expenses)
    trip_shirin_aed = sum(exp['shirin_aed'] for exp in expenses)
    
    # Create embed - customize title for single date vs date range
    is_single_date = (start_date and end_date and start_date == end_date)
    
    if is_single_date:
        embed = discord.Embed(
            title=f"📅 Daily Itinerary - {start_date}",
            description="Complete day-by-day breakdown of activities and expenses",
            color=0x9b59b6,
            timestamp=datetime.now()
        )
    else:
        embed = discord.Embed(
            title="🗓️ Complete Trip Itinerary",
            color=0x9b59b6,
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
        embed.add_field(name="🔍 Trip Details", value="\n".join(filter_info), inline=False)
    
    # Trip overview
    trip_overview = (
        f"**Duration:** {len(sorted_dates)} days\n"
        f"**Total Expenses:** {len(expenses)} transactions\n"
        f"**Cities Visited:** {len(set(exp['city'] for exp in expenses))}\n"
        f"**Total Cost:** {format_currency(trip_total_rmb, 'RMB')}"
    )
    embed.add_field(name="📊 Trip Overview", value=trip_overview, inline=False)
    
    # Daily breakdown (show more detail for single date, limit for multiple days)
    days_shown = 0
    max_days = 7 if not is_single_date else 1
    
    for date in sorted_dates:
        if days_shown >= max_days:
            remaining_days = len(sorted_dates) - days_shown
            embed.add_field(
                name="📝 Note", 
                value=f"... and {remaining_days} more days. Use date filters to see specific periods.",
                inline=False
            )
            break
            
        day_expenses = daily_expenses[date]
        day_total = sum(exp['total_rmb'] for exp in day_expenses)
        
        # Format day activities
        activities = []
        cities_visited = set()
        
        for exp in day_expenses:
            emoji = get_expense_emoji(exp['category'])
            cities_visited.add(exp['city'])
            
            activity_line = f"{emoji} **{exp['activity']}** ({exp['category']})"
            cost_line = f"   💰 {format_currency(exp['total_rmb'], 'RMB')} - {exp['payer']}"
            
            if exp['notes']:
                note_line = f"   📝 {exp['notes'][:50]}{'...' if len(exp['notes']) > 50 else ''}"
                activities.append(f"{activity_line}\n{cost_line}\n{note_line}")
            else:
                activities.append(f"{activity_line}\n{cost_line}")
        
        # Day header with cities
        cities_text = ", ".join(sorted(cities_visited))
        day_header = f"📍 **{cities_text}**\n💵 Daily Total: {format_currency(day_total, 'RMB')}"
        
        # Combine day info
        day_content = f"{day_header}\n\n" + "\n\n".join(activities)
        
        # Truncate if too long for Discord (more space for single date view)
        max_length = 1800 if is_single_date else 1000
        if len(day_content) > max_length:
            truncate_length = max_length - 50
            day_content = day_content[:truncate_length] + "...\n*(More activities on this day)*"
        
        embed.add_field(
            name=f"📅 {date}",
            value=day_content,
            inline=False
        )
        
        days_shown += 1
    
    # Trip totals
    totals_text = (
        f"**Combined:** {format_currency(trip_total_rmb, 'RMB')}\n"
        f"**Sunil:** {format_currency(trip_sunil_gbp, 'GBP')}\n"
        f"**Shirin:** {format_currency(trip_shirin_aed, 'AED')}"
    )
    embed.add_field(name="💰 Trip Total Costs", value=totals_text, inline=True)
    
    # Transportation summary
    transport_expenses = [exp for exp in expenses if exp['category'] == 'Transportation']
    if transport_expenses:
        transport_total = sum(exp['total_rmb'] for exp in transport_expenses)
        transport_count = len(transport_expenses)
        embed.add_field(
            name="🚗 Transportation", 
            value=f"{transport_count} trips\n{format_currency(transport_total, 'RMB')}",
            inline=True
        )
    
    # Accommodation summary
    accommodation_expenses = [exp for exp in expenses if exp['category'] == 'Accommodation']
    if accommodation_expenses:
        accommodation_total = sum(exp['total_rmb'] for exp in accommodation_expenses)
        accommodation_count = len(accommodation_expenses)
        embed.add_field(
            name="🏨 Accommodation", 
            value=f"{accommodation_count} bookings\n{format_currency(accommodation_total, 'RMB')}",
            inline=True
        )
    
    # Footer with date range
    if sorted_dates:
        embed.set_footer(text=f"Trip Period: {sorted_dates[0]} to {sorted_dates[-1]}")
    
    return embed
