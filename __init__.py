import datetime

from .PubMedArticle import PubMedArticle
from .PubMedSearch import PubMedSearch
from .PubMedCrawler import PubMedCrawler


def search(search_str: str, **kwargs) -> PubMedSearch:
    results = PubMedSearch(search_str, **kwargs)
    return results


def get_latest() -> PubMedSearch:
    today = datetime.datetime.now()
    today_str = today.strftime("%Y/%m/%d").replace('/', '%2F')
    tomorow = today + datetime.timedelta(days=1)
    tomorow_str = tomorow.strftime("%Y/%m/%d").replace('/', '%2F')
    query = (
        f"https://pubmed.ncbi.nlm.nih.gov/"
        f"?term={today_str}%5Bedat%5D"
        f"&filter=dates.{today_str}-{tomorow_str}"
        f"&sort=date&size=100"
    )
    results = PubMedSearch()
    results.startFromQuery(query)
    return results
