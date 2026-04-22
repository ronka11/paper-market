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


### todo
- [x] database setup
- [x] market
- [x] portfolio
- [x] sentiment
- [x] langchain agents
- [x] loggings 
- [x] react frontend
- [ ] backtesting methods
- [ ] rpi deployement


### improvements
- [ ] dynamic charts, adjusting y axis scale according to time window
- [ ] candlestick charts along with existing charts
- [ ] project intro popup - aim, learnings
- [ ] compare two stocks
- [ ] better scraping of posts according to ticker and name
- [ ] better search of stocks according to name
