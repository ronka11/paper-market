# paper-market
paper market simulator


## startup
1. activate venv
2. uvicorn main:app --reload
3. docker run -d -p 6379:6379 redis
4. celery -A app.celery_app.celery worker --pool=solo --loglevel=info
5. celery -A app.celery_app.celery beat --loglevel=info


### todo
- [x] database setup
- [x] market
- [x] portfolio
- [x] sentiment
- [x] langchain agents
- [ ] loggings 
- [ ] react frontend
- [ ] backtesting methods

