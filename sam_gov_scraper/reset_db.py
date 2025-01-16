from dotenv import load_dotenv
from sam_gov_scraper.models import reset_db

def main():
    load_dotenv()
    reset_db()

if __name__ == "__main__":
    main()
