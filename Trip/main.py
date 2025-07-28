import discord
from discord.ext import commands
import asyncio
import os
from bot.commands import ExpenseCommands
from bot.database import ExpenseDatabase
from bot.currency import CurrencyConverter

# Bot setup with intents
intents = discord.Intents.default()
# Remove privileged intents to avoid Discord portal configuration
# intents.message_content = True

class TravelExpenseBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Initialize components
        self.db = ExpenseDatabase()
        self.currency = CurrencyConverter()
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        # Add cogs
        await self.add_cog(ExpenseCommands(self))
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        
        # Update currency rates on startup
        await self.currency.update_rates()

async def main():
    """Main function to run the bot"""
    bot = TravelExpenseBot()
    
    # Get token from environment variable
    token = os.getenv('DISCORD_BOT_TOKEN', 'your_discord_bot_token_here')
    
    if token == 'your_discord_bot_token_here':
        print("Warning: Using default token. Please set DISCORD_BOT_TOKEN environment variable.")
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print("Failed to login. Please check your bot token.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
