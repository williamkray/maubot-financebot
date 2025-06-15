from typing import Optional, Type, List

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command

# not necessary, as it's imported by maubot already
#import asyncio
#import aiohttp
import json

class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("alphavantageKey")
        helper.copy("stocktrigger")
        helper.copy("cryptotrigger")

class FinanceBot(Plugin):
    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @command.new(name=lambda self: self.config["stocktrigger"],
            help="Look up information about a stock by its ticker symbol")
    @command.argument("ticker", pass_raw=True, required=True)
    async def stock_handler(self, evt: MessageEvent, ticker: str) -> None:
        await evt.mark_read()

        if ticker.lower() == "help":
            await evt.mark_read()

            await evt.respond("Look up information about a stock using its ticker symbol, for example: <br />\
                            <code>!" + self.config["stocktrigger"] + " tsla</code>", allow_html=True)
            return None

        tickerUpper = ticker.upper()
        
        # Get company overview
        overview_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={tickerUpper}&apikey={self.config["alphavantageKey"]}'
        quote_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={tickerUpper}&apikey={self.config["alphavantageKey"]}'
        
        try:
            # Get both company overview and quote data
            overview_response = await self.http.get(overview_url)
            overview_json = await overview_response.json()
            
            quote_response = await self.http.get(quote_url)
            quote_json = await quote_response.json()
        except Exception as e:
            await evt.respond(f"request failed: {e.message}")
            return None

        try:
            if "Error Message" in quote_json or "Error Message" in overview_json:
                await evt.respond("No results, double check that you've chosen a real ticker symbol")
                return None

            quote = quote_json['Global Quote']
            current_price = float(quote['05. price'])
            open_price = float(quote['02. open'])
            previous_close = float(quote['08. previous close'])
            change = float(quote['09. change'])
            change_percent = quote['10. change percent']
            
            # Get company name and additional data from overview
            company_name = overview_json.get('Name', tickerUpper)
            sector = overview_json.get('Sector', 'N/A')
            market_cap = float(overview_json.get('MarketCapitalization', 0))
            pe_ratio = overview_json.get('PERatio', 'N/A')
            high_52w = float(overview_json.get('52WeekHigh', 0))
            low_52w = float(overview_json.get('52WeekLow', 0))

        except Exception as e:
            await evt.respond("No results, double check that you've chosen a real ticker symbol")
            self.log.exception(e)
            return None
        
        if change < 0:
            color = "red"
            arrow = "\U000025BC"
        else:
            color = "green"
            arrow = "\U000025B2"

        # Format market cap to be more readable
        if market_cap >= 1e12:
            market_cap_str = f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            market_cap_str = f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            market_cap_str = f"${market_cap/1e6:.2f}M"
        else:
            market_cap_str = f"${market_cap:.2f}"

        prettyMessage = "<br />".join(
                [
                    f"<b>Current data for <a href=\"https://finance.yahoo.com/quote/{tickerUpper}\">\
                            {company_name}</a> ({tickerUpper}):</b>" ,
                    f"",
                    f"<b>Price:</b> <font color=\"{color}\">${current_price:.2f}, \
                            {arrow}{change_percent}</font> from previous close @ ${previous_close:.2f}",
                    f"<b>Open:</b> ${open_price:.2f}",
                    f"<b>52 Week High:</b> ${high_52w:.2f}",
                    f"<b>52 Week Low:</b> ${low_52w:.2f}",
                    f"<b>Sector:</b> {sector}",
                    f"<b>Market Cap:</b> {market_cap_str}",
                    f"<b>P/E Ratio:</b> {pe_ratio}"
                ]
            )
        
        await evt.respond(prettyMessage, allow_html=True)

    @command.new(name="hodl", help="Look up cryptocurrency price and changes.")
    @command.argument("symbol", pass_raw=True, required=True)
    async def crypto_handler(self, evt: MessageEvent, symbol: str) -> None:
        """Handle crypto price requests."""
        args = symbol.split()
        if not args:
            await evt.respond("Please provide a cryptocurrency symbol (e.g., !hodl BTC)")
            return

        symbol = args[0].upper()
        market = args[1].upper() if len(args) > 1 else "USD"

        try:
            # Get daily data for multiple timeframe analysis
            url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={symbol}&market={market}&apikey={self.config['alphavantageKey']}"
            async with self.http.get(url) as response:
                if response.status != 200:
                    await evt.respond(f"Error fetching data: HTTP {response.status}")
                    return
                
                data = await response.json()
                
                if "Error Message" in data:
                    await evt.respond(f"Error: {data['Error Message']}")
                    return
                
                if "Note" in data:
                    await evt.respond(f"API Note: {data['Note']}")
                    return

                time_series = data.get("Time Series (Digital Currency Daily)", {})
                if not time_series:
                    await evt.respond(f"No data found for {symbol}/{market}")
                    return

                # Get today's data
                today = list(time_series.items())[0]
                today_date = today[0]
                today_data = today[1]
                
                # Get historical data for different timeframes
                dates = list(time_series.keys())
                if len(dates) < 180:  # Need at least 180 days for 6-month analysis
                    await evt.respond(f"Insufficient historical data for {symbol}/{market}")
                    return

                # Calculate changes for different timeframes
                current_price = float(today_data["4. close"])
                open_price = float(today_data["1. open"])
                day_30_ago_price = float(time_series[dates[30]]["4. close"])
                month_6_ago_price = float(time_series[dates[180]]["4. close"])

                # Calculate price changes and percentages
                day_change = current_price - open_price
                day_change_pct = (day_change / open_price) * 100
                
                month_change = current_price - day_30_ago_price
                month_change_pct = (month_change / day_30_ago_price) * 100
                
                year_half_change = current_price - month_6_ago_price
                year_half_change_pct = (year_half_change / month_6_ago_price) * 100

                # Format the changes with appropriate colors and arrows
                def format_change(change, pct):
                    if change > 0:
                        return f"<font color='green'>+{change:.2f} ({pct:+.2f}%) ↑</font>"
                    elif change < 0:
                        return f"<font color='red'>{change:.2f} ({pct:+.2f}%) ↓</font>"
                    return f"{change:.2f} ({pct:+.2f}%)"

                day_change_str = format_change(day_change, day_change_pct)
                month_change_str = format_change(month_change, month_change_pct)
                year_half_change_str = format_change(year_half_change, year_half_change_pct)

                # Format volume
                volume = float(today_data["5. volume"])
                if volume >= 1_000_000:
                    volume_str = f"{volume/1_000_000:.2f}M"
                elif volume >= 1_000:
                    volume_str = f"{volume/1_000:.2f}K"
                else:
                    volume_str = f"{volume:.2f}"

                # Create the response message
                response = "<br />".join([
                    f"<b>{symbol}/{market}</b> - {today_date}",
                    f"",
                    f"Current: {current_price:.2f} {market}",
                    f"24h Change: {day_change_str}",
                    f"24h Volume: {volume_str} {symbol}",
                    f"24h High: {float(today_data['2. high']):.2f} {market}",
                    f"24h Low: {float(today_data['3. low']):.2f} {market}",
                    f"30d Change: {month_change_str}",
                    f"6m Change: {year_half_change_str}"
                ])

                await evt.respond(response, allow_html=True)

        except Exception as e:
            await evt.respond(f"Error fetching {symbol} data: {str(e)}")
