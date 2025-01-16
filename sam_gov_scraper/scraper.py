import argparse
import concurrent.futures
from datetime import datetime, timedelta
import json
import logging
import requests
from typing import List, Dict
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SAM.gov API endpoint
BASE_URL = "https://sam.gov/api/prod/sgs/v1/search/?random=1736987964325&index=_all&page={page}&mode=search&sort=-modifiedDate&size={page_size}&mfe=true&q=&qMode=ALL&modified_date.to={end_date}&modified_date.from={start_date}"
PAGE_SIZE = 400

def fetch_opportunities(start_date: datetime, end_date: datetime, page: int, retry: int = 0) -> Dict:
    """Fetch opportunities from SAM.gov API"""
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        start_date_str = start_date.strftime("%Y-%m-%d") + "-07:00"
        end_date_str = end_date.strftime("%Y-%m-%d") + "-07:00"
        url = BASE_URL.format(page=page, page_size=PAGE_SIZE, start_date=start_date_str, end_date=end_date_str)
        # logger.info(f"Fetching opportunities for org {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        xhr_data = response.json()
        # print(f"XHR DATA: {json.dumps(xhr_data, indent=2)}")
        try:
            payload = xhr_data.get('_embedded', {}).get("results", [])
        except KeyError:
            logger.error(f"Error fetching opportunities: {xhr_data}")
            return None
        return payload
    except requests.RequestException as e:
        logger.error(f"Error fetching opportunities: {e}")
        if retry < 1:
            return fetch_opportunities(start_date=start_date, end_date=end_date, page=page, retry=retry+1)
        else:
            return None


def process_opportunity(opportunity: id) -> None:
    """Process a single opportunity"""
    
    # try:
    #     # Extract relevant data and store in database
    #     # This is where you'd implement your database storage logic
    #     notice_id = opportunity.get('noticeId')
    #     title = opportunity.get('title')
    #     logger.info(f"Processing opportunity: {notice_id} - {title}")
        
    # except Exception as e:
    #     logger.error(f"Error processing opportunity: {e}")

def main(max_workers: int):
    logger.info(f"Starting scraper with {max_workers} workers")
    # Process opportunities using thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        entries = 0
        entries_by_id = {}
        begin_date = datetime(2024, 1, 1)
        for day in range(365):
            start_date = begin_date + timedelta(days=day)
            end_date = start_date + timedelta(days=1)
            # logger.info(f"Processin g day {day} {start_date}")
            org_entries = 0
            page = 0
            while True:
                data = fetch_opportunities(start_date=start_date, end_date=end_date, page=page)
                if not data or len(data) == 0:
                    break
                # logger.info(f"Fetched {len(data)} opportunities for org {org_id}")
                for result in data:
                    id = result['_id']

                    if id in entries_by_id:
                        # print(f"Skipping {id} because it already exists")
                        continue
                    entries_by_id[id] = True
                    executor.submit(process_opportunity, id)
                    org_entries += 1
                page += 1
            logger.info(f"Processed {org_entries} entries for day {start_date}")
            # logger.info(f"Total entries: {entries_by_id}")
            entries += org_entries


        # # Fetch and process remaining pages
        # for page in range(2, total_pages + 1):
        #     data = fetch_opportunities(page=page)
        #     if data:
        #         opportunities = data.get('opportunities', [])
        #         futures.extend(
        #             executor.submit(process_opportunity, opp) 
        #             for opp in opportunities
        #         )
        
        # # Wait for all tasks to complete
        # concurrent.futures.wait(futures)
    
    logger.info("Scraping completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAM.gov Opportunity Scraper")
    parser.add_argument(
        "--max_workers",
        type=int,
        default=10,
        help="Maximum number of worker threads"
    )
    
    args = parser.parse_args()
    main(args.max_workers)