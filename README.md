# sam_gov_scraper

## Setup

1. Install dependencies

```bash
pip install -r requirements.txt
```
2. Create a `.env` file with the following variables:

```
DATABASE_URL=XXX
```
3. Initialize the database

```bash
python -m sam_gov_scraper.reset_db
```

4. Run the scraper

```bash
python -m sam_gov_scraper.scraper --max_workers=10
```

## Notes
The Scraper works by scanning sam.gov search results. We do *not* use the explicit API, rather this uses the Web interface XHRs.
This interface has a limit of 10000 results per query, regardless of page size. To work around this, we do an open query (no filters) and query by day.
The scraper queries the DB for the oldest recorded opportunity (by modified date) and uses that day as the starting date.
Opportunity IDs are read from the XHRs and added to a ThreadedExecutor.

A stack of workers (specified by `--max_workers`) are used to process the opportunities.
It makes 2 requests for each opportunity:
1. The XHR to get the opportunity details
2. The XHR to get the attachments/links

During #1 we discover that some opportunities are not accessible for permission reasons.
See: [example](https://sam.gov/api/prod/opps/v2/opportunities/74552?random=1737005582919)

We are currently not storing any info about the opportunities missing due to permissions.

I've run the scaper with 50 workers. From my laptop it gets about 40rps. At that rate will take about 1.5 days to scrape all opportunities.
I've seen the occasional 500 error from the server, so I don't want to run it any faster for fear that I will either break the server, or cause admins to do something to block my IP.

## Schema
The Schema is relatively simple. Links are normalized as are contractors.
We only store the primary point of contact.