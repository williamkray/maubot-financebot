a simple maubot module that responds with financial data about stock price or cryptocurrency exchange rate.

To install, please see the [standard maubot plugin installation instructions](https://github.com/maubot/maubot/wiki/Usage#adding-a-plugin)

note: this module depends on having an api key for [Alpha Vantage](https://www.alphavantage.co/support/#api-key)

## Setup
plug in your Alpha Vantage API key in the config file (either before packaging in the base-config, or directly in the maubot interface after loading).

update the commands you want to use, by default stock data is returned with the `!stonks` command, and crypto data is returned with `!hodl` command. for example:

`!stonks ibm`

would return something like this:

![stonks response](images/stonks.png)

and

`!hodl btc/ada`

would return something like this:

![hodl response](images/hodl.png)
