"""Finance-adapted prompts for TimeCAP agents."""

FINANCE_CONTEXTUALIZE_SYSTEM = (
    "Your job is to act as a professional finance analyst. "
    "You will write a high-quality report that is informative and helps in "
    "understanding the current financial situation."
)

FINANCE_CONTEXTUALIZE_USER = """Your task is to analyze key financial indicators over the last {window_size} market days.
Review the time-series data provided for the last {window_size} market days.
Each time-series consists of daily values separated by a '|' token for the following indicators:
- S&P 500: {sp500}
- VIX (Volatility Index): {vix}
- Nikkei 225: {nikkei}
- FTSE 100: {ftse}
- Gold Futures: {gold}
- Crude Oil Futures: {crude_oil}
- Exchange rate for EUR/USD: {eur_usd}
- Exchange rate for USD/JPY: {usd_jpy}
- Exchange rate for USD/CNY: {usd_cny}
Based on this time-series data, write a concise report that provides insights crucial for understanding the current financial situation.
Your report should be limited to five sentences, yet comprehensive, highlighting key trends and considering their potential impact on the market.
Do not write numerical values while writing the report."""

FINANCE_PREDICT_SYSTEM = (
    "Your job is to act as a professional financial forecaster. "
    "You will be given contextual information from the past market days. "
    "Based on this information, your task is to predict whether the target price will "
    "decrease by more than 1%, increase by more than 1%, or change minimally in the next market day."
)

FINANCE_PREDICT_USER = """Your task is to predict whether the {indicator_name} price will:
(1) Decrease: decrease by more than 1%
(2) Increase: increase by more than 1%
(3) Neutral: change minimally, between -1% to 1%
in the next market day.

Contextual report:
{summary}

{examples}

Respond with exactly one of: 'decrease', 'increase', or 'neutral'. Do not provide any other details."""

MINUTE_CONTEXTUALIZE_SYSTEM = (
    "Your job is to act as an intraday equity market analyst. "
    "Write a concise report that captures microstructure and short-horizon momentum context."
)

MINUTE_CONTEXTUALIZE_USER = """Analyze the last {window_size} one-minute bars for {symbol}.
Each series is minute values separated by '|':
- Open: {open}
- High: {high}
- Low: {low}
- Close: {close}
- Volume: {volume}
Write at most five sentences describing short-horizon trend, volatility regime, and liquidity cues.
Do not write raw numerical values in the report."""

MINUTE_PREDICT_SYSTEM = (
    "Your job is to act as an intraday forecaster. "
    "Given a contextual summary of recent minute bars, estimate the near-term return direction."
)

MINUTE_PREDICT_USER = """Based on the following intraday context for {symbol}, predict the next {horizon}-minute return direction:
'up', 'down', or 'flat'.

Contextual report:
{summary}

{examples}

Respond with exactly one of: 'up', 'down', or 'flat'."""

LABEL_MAP_DAILY = {
    "decrease": 0,
    "neutral": 1,
    "increase": 2,
}

LABEL_MAP_MINUTE = {
    "down": 0,
    "flat": 1,
    "up": 2,
}

INDICATOR_DISPLAY = {
    "sp500": "S&P 500",
    "nikkei": "Nikkei 225",
}
