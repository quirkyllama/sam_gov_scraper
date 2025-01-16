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
