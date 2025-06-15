a simple maubot module that responds with financial data about stock price or cryptocurrency exchange rate.

To install, please see the [standard maubot plugin installation instructions](https://github.com/maubot/maubot/wiki/Usage#adding-a-plugin)

note: this module depends on having an api key for [Alpha Vantage](https://www.alphavantage.co/support/#api-key)

## Setup
plug in your Alpha Vantage API key in the config file (either before packaging in the base-config, or directly in the maubot interface after loading).

update the commands you want to use, by default stock data is returned with the `!stonks` command, and crypto data is returned with `!hodl` command. for example:

`!stonks ibm`

would return something like this:

```markdown
**Current data for International Business Machines (https://finance.yahoo.com/quote/IBM) (IBM):**

**Price:** $277.22, ▼-1.3557% from previous close @ $281.03
**Open:** $278.20
**52 Week High:** $283.06
**52 Week Low:** $162.58
**Sector:** TECHNOLOGY
**Market Cap:** $261.19B
**P/E Ratio:** 47.39
```

and

`!hodl btc usd`

would return something like this:

```markdown
**BTC/USD** - 2025-06-15

Current: 105467.27 USD
24h Change: +1.85 (+0.00%) ↑
24h Volume: 34.77 BTC
24h High: 105553.75 USD
24h Low: 105396.90 USD
30d Change: +1967.24 (+1.90%) ↑
6m Change: -669.72 (-0.63%) ↓
```