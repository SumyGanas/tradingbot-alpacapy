- A visualization/showcasing comparing the performance of an automated trading strategy to the S&P500 using paper trading APIs
- The Alpaca Paper Trading and Market Data APIs were used to execute orders on an exchange and fetch stock data respectively 
[Alpaca Docs](https://docs.alpaca.markets/docs/paper-trading)

# Technologies Used (GCP)
 
- Cloud Firestore (Main database)
- 	Stores all portfolio DBs
- 	Has a brief snapshot of each portfolio:
	- 	Name, Total $, day's change
- 	Stores all buy/sell orders executed to date

- Cloud Storage
- 	Stores the functions and hosting code

- Cloud Functions
- 	Executes the trading strategy daily via Cloud Pub/Sub events automated via Cloud Scheduler
- 	Pushes the API results to the database
