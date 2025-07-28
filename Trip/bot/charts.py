import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from typing import Dict, List, Tuple, Optional
import io
import discord
from datetime import datetime

class ChartGenerator:
    """Generate beautiful rainbow-colored pie charts for expense data"""
    
    def __init__(self):
        # Beautiful rainbow color palette
        self.rainbow_colors = [
            '#FF6B6B',  # Red
            '#FF8E53',  # Orange
            '#FF8F00',  # Amber
            '#FFD93D',  # Yellow
            '#6BCF7F',  # Green
            '#4ECDC4',  # Teal
            '#45B7D1',  # Blue
            '#9B59B6',  # Purple
            '#F39C12',  # Golden
            '#E74C3C',  # Crimson
            '#3498DB',  # Sky Blue
            '#2ECC71',  # Emerald
            '#F1C40F',  # Sunflower
            '#E67E22',  # Carrot
            '#9C88FF',  # Lavender
            '#FF69B4'   # Hot Pink
        ]
        
        # Set matplotlib to use a nice style
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def create_spending_by_category_chart(self, expenses: List[Dict], currency: str = 'RMB', title_suffix: str = '') -> Optional[io.BytesIO]:
        """Create pie chart for spending by category"""
        category_totals = {}
        
        for expense in expenses:
            category = expense['category']
            if currency == 'RMB':
                amount = expense['amount_rmb']
            elif currency == 'GBP':
                amount = expense['amount_gbp']
            elif currency == 'AED':
                amount = expense['amount_aed']
            else:
                amount = expense['amount_rmb']  # fallback
            
            category_totals[category] = category_totals.get(category, 0) + amount
        
        if not category_totals:
            return None
        
        # Sort by amount (descending)
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        labels = [cat for cat, _ in sorted_categories]
        sizes = [amount for _, amount in sorted_categories]
        colors = self.rainbow_colors[:len(labels)]
        
        title = f"💰 Spending by Category{title_suffix}"
        if currency == 'GBP':
            title += " (British Pounds)"
        elif currency == 'AED':
            title += " (UAE Dirhams)"
        else:
            title += " (Chinese RMB)"
        
        return self._create_pie_chart(labels, sizes, colors, title, currency)
    
    def create_spending_by_city_chart(self, expenses: List[Dict], currency: str = 'RMB', title_suffix: str = '') -> Optional[io.BytesIO]:
        """Create pie chart for spending by city"""
        city_totals = {}
        
        for expense in expenses:
            city = expense['city']
            if currency == 'RMB':
                amount = expense['amount_rmb']
            elif currency == 'GBP':
                amount = expense['amount_gbp']
            elif currency == 'AED':
                amount = expense['amount_aed']
            else:
                amount = expense['amount_rmb']
            
            city_totals[city] = city_totals.get(city, 0) + amount
        
        if not city_totals:
            return None
        
        # Sort by amount (descending)
        sorted_cities = sorted(city_totals.items(), key=lambda x: x[1], reverse=True)
        
        labels = [city for city, _ in sorted_cities]
        sizes = [amount for _, amount in sorted_cities]
        colors = self.rainbow_colors[:len(labels)]
        
        title = f"🌍 Spending by City{title_suffix}"
        if currency == 'GBP':
            title += " (British Pounds)"
        elif currency == 'AED':
            title += " (UAE Dirhams)"
        else:
            title += " (Chinese RMB)"
        
        return self._create_pie_chart(labels, sizes, colors, title, currency)
    
    def create_spending_by_person_chart(self, expenses: List[Dict], currency: str = 'RMB', title_suffix: str = '') -> Optional[io.BytesIO]:
        """Create pie chart for spending by person (Shir vs Bubba vs Couple)"""
        person_totals = {}
        
        for expense in expenses:
            payer = expense['payer']
            if currency == 'RMB':
                amount = expense['amount_rmb']
            elif currency == 'GBP':
                amount = expense['amount_gbp']
            elif currency == 'AED':
                amount = expense['amount_aed']
            else:
                amount = expense['amount_rmb']
            
            if payer == 'Couple':
                # Split couple expenses 50/50
                person_totals['Shir'] = person_totals.get('Shir', 0) + (amount / 2)
                person_totals['Bubba'] = person_totals.get('Bubba', 0) + (amount / 2)
            else:
                # Map Sunil to Bubba for display
                display_name = 'Bubba' if payer == 'Sunil' else payer
                person_totals[display_name] = person_totals.get(display_name, 0) + amount
        
        if not person_totals:
            return None
        
        # Sort by amount (descending)
        sorted_persons = sorted(person_totals.items(), key=lambda x: x[1], reverse=True)
        
        labels = [person for person, _ in sorted_persons]
        sizes = [amount for _, amount in sorted_persons]
        
        # Special colors for Shir and Bubba
        person_colors = {
            'Shir': '#FF69B4',     # Hot Pink
            'Bubba': '#45B7D1',    # Blue
            'Sunil': '#45B7D1'     # Blue (same as Bubba)
        }
        colors = [person_colors.get(person, self.rainbow_colors[i]) for i, person in enumerate(labels)]
        
        title = f"👫 Shir vs Bubba Spending{title_suffix}"
        if currency == 'GBP':
            title += " (British Pounds)"
        elif currency == 'AED':
            title += " (UAE Dirhams)"
        else:
            title += " (Chinese RMB)"
        
        return self._create_pie_chart(labels, sizes, colors, title, currency)
    
    def create_activities_by_category_chart(self, expenses: List[Dict], title_suffix: str = '') -> Optional[io.BytesIO]:
        """Create pie chart for activity counts by category"""
        category_counts = {}
        
        for expense in expenses:
            category = expense['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        if not category_counts:
            return None
        
        # Sort by count (descending)
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        labels = [f"{cat}\n({count} activities)" for cat, count in sorted_categories]
        sizes = [count for _, count in sorted_categories]
        colors = self.rainbow_colors[:len(labels)]
        
        title = f"📊 Activities by Category{title_suffix}"
        
        return self._create_pie_chart(labels, sizes, colors, title, "activities")
    
    def create_activities_by_city_chart(self, expenses: List[Dict], title_suffix: str = '') -> Optional[io.BytesIO]:
        """Create pie chart for activity counts by city"""
        city_counts = {}
        
        for expense in expenses:
            city = expense['city']
            city_counts[city] = city_counts.get(city, 0) + 1
        
        if not city_counts:
            return None
        
        # Sort by count (descending)
        sorted_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)
        
        labels = [f"{city}\n({count} activities)" for city, count in sorted_cities]
        sizes = [count for _, count in sorted_cities]
        colors = self.rainbow_colors[:len(labels)]
        
        title = f"🗺️ Activities by City{title_suffix}"
        
        return self._create_pie_chart(labels, sizes, colors, title, "activities")
    
    def _create_pie_chart(self, labels: List[str], sizes: List[float], colors: List[str], title: str, currency: str) -> io.BytesIO:
        """Create a beautiful pie chart with rainbow colors"""
        # Create figure with high DPI for crisp image
        fig, ax = plt.subplots(figsize=(12, 10), dpi=100)
        fig.patch.set_facecolor('#2C2F33')  # Discord dark theme background
        
        # Create pie chart
        pie_result = ax.pie(
            sizes, 
            labels=labels, 
            colors=colors,
            autopct=lambda pct: f'{pct:.1f}%\n({self._format_value(pct * sum(sizes) / 100, currency)})',
            startangle=90,
            explode=[0.05] * len(sizes),  # Slightly separate all slices
            shadow=True,
            wedgeprops=dict(linewidth=3, edgecolor='white')
        )
        
        # Extract the results
        if len(pie_result) == 3:
            wedges, texts, autotexts = pie_result
        else:
            wedges, texts = pie_result
            autotexts = []
        
        # Style the text
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
            text.set_color('white')
        
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
            autotext.set_color('white')
        
        # Style the title
        ax.set_title(title, fontsize=16, fontweight='bold', color='white', pad=20)
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        fig.text(0.02, 0.02, f'Generated: {timestamp}', fontsize=8, color='#99AAB5')
        
        # Save to bytes
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', facecolor='#2C2F33', dpi=100)
        buffer.seek(0)
        plt.close(fig)  # Free memory
        
        return buffer
    
    def _format_value(self, value: float, currency: str) -> str:
        """Format value based on currency or type"""
        if currency == "activities":
            return f"{int(value)}"
        elif currency == 'RMB':
            return f"¥{value:.0f}"
        elif currency == 'GBP':
            return f"£{value:.0f}"
        elif currency == 'AED':
            return f"د.إ{value:.0f}"
        else:
            return f"{value:.0f}"

def format_currency(amount: float, currency: str) -> str:
    """Format currency for display"""
    if currency == 'RMB':
        return f"¥{amount:.2f}"
    elif currency == 'GBP':
        return f"£{amount:.2f}"
    elif currency == 'AED':
        return f"د.إ{amount:.2f}"
    elif currency == 'USD':
        return f"${amount:.2f}"
    elif currency == 'EUR':
        return f"€{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"
