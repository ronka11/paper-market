# paper-market
paper market simulator
An AI-powered paper trading simulator. Feed it a stock/crypto ticker (Indian NSE/BSE or US), it pulls real market data + Reddit sentiment, runs algorithmic strategies (pending), lets you simulate trades with virtual cash, and an LLM agent helps you reason about positions


## startup
1. paper-market> .\venv-paper-market\Scripts\activate
2. paper-market> docker run -d -p 6379:6379 redis
3. paper-market\backend> uvicorn main:app --reload
4. paper-market\backend> celery -A app.celery_app.celery worker --pool=solo --loglevel=info
5. paper-market\backend> celery -A app.celery_app.celery beat --loglevel=info
6. paper-market\frontend> npm run dev


### plan
- [x] database setup
- [x] market
- [x] portfolio
- [x] sentiment
- [x] langchain agents
- [x] loggings 
- [x] react frontend
- [ ] backtesting methods (later)
- [ ] rpi deployement


### improvements / todo
- [ ] major UI improvement
- [x] buy/sell live prices
- [x] indian stocks redirection from dashboard
- [x] yfinance yfinance yfinance
- [X] ticker chart view for 6mo, 1y 
- [X] fix NASDAQ chart viewing
- [x] fix dashboard
- [x] improve prompting - strict json
- [x] dynamic charts, adjusting y axis scale according to time window
- [x] candlestick charts along with existing charts
- [x] project intro popup - aim, learnings
- [x] compare two stocks
- [x] integrate tavily instead of reddit?
- [x] two seperate portfolios for US and IN stocks
