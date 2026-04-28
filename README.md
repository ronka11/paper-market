# paper-market
paper market simulator
An AI-powered paper trading simulator. Feed it a stock/crypto ticker (Indian NSE/BSE or US), it pulls real market data + Reddit sentiment, runs algorithmic strategies (pending), lets you simulate trades with virtual cash, and an LLM agent helps you reason about positions


## startup
1. paper-market> activate venv
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
- [ ] backtesting methods
- [ ] rpi deployement


### improvements / todo
- [ ] fix dashboard
- [x] dynamic charts, adjusting y axis scale according to time window
- [x] candlestick charts along with existing charts
- [x] project intro popup - aim, learnings
- [x] compare two stocks
- [x] integrate tavily instead of reddit?
- [x] two seperate portfolios for US and IN stocks
