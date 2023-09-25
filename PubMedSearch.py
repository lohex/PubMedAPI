"""
PubMEDapi
~~~~~~~~~~~~~~~~

This API defines the interface to PubMED.

Author: Lorenz Hexemer
"""
from typing import List, Generator, Optional
from bs4 import BeautifulSoup as html
import requests as http

from PubMedArticle import PubMedArticle


class PubMedSearch:
    def __init__(self, search_str: str,
                 not_older_than: Optional[str] = None,
                 abstract_available: bool = True
                 ) -> None:
        """
        Initializes a PubMedSearch object.

        Args:
            search_str: The search query string.
            not_older_than: Filters articles not older than specified time.
            abstract_available: Whether to filter for articles with abstracts.
        """
        self.results_page = 1
        query = self.buildQuery(search_str, not_older_than, abstract_available)
        response = http.get(query)
        doc = html(response.text)

        results = doc.find('div', class_="results-amount")
        self.n_results = int(results.h3.span.text.replace(',', ''))
        print(f"found {self.n_results} articles.")

        self.articles = self.extractResults(doc)

    def buildQuery(self, search_str: str, not_older_than: Optional[str],
                   abstract_available: bool) -> str:
        """
        Builds the search query URL.

        Args:
            search_str: The search query string.
            not_older_than: Filters articles not older than specified time.
            abstract_available: Whether to filter for articles with abstracts.

        Returns:
            The search query URL.
        """
        self.search_str = search_str
        query = (
            f'https://pubmed.ncbi.nlm.nih.gov/'
            f'?term={self.search_str}&page={self.results_page}'
        )
        if not_older_than:
            if not_older_than == "1_year":
                query += "&filter=datesearch.y_1"
            elif not_older_than == "5_years":
                query += "&filter=datesearch.y_5"
            elif not_older_than == "10_years":
                query += "&filter=datesearch.y_10"
            else:
                raise Exception(f'Invalid search flag "{not_older_than}"')

        if abstract_available:
            query += "&filter=simsearch1.fha"

        return query

    def grepMoreResults(self) -> None:
        """
        Fetches more results from the PubMed website.
        """
        self.results_page += 1
        query = (
            f'https://pubmed.ncbi.nlm.nih.gov/?'
            f'term={self.search_str}&page={self.results_page}'
        )
        response = http.get(query)
        doc = html(response.text)

        self.articles += self.extractResults(doc)

    def extractResults(self, doc) -> List:
        """
        Extracts search results from the given document.

        Args:
            doc: Document to extract results from.

        Returns:
            List of extracted articles.
        """
        page_links = doc.find_all('a', class_="docsum-title")
        pubmed_ids = [p.attrs['data-article-id'] for p in page_links]
        titles = [p.text for p in page_links]
        docsum_autorhs = doc.find_all('span', class_="docsum-authors")
        authors = [s.text for s in docsum_autorhs]
        citations = [
            c.text
            for c in doc.find_all('span', class_="docsum-journal-citation")
        ]

        results = [PubMedArticle(id, title, authors, pub)
                   for id, title, authors, pub
                   in zip(pubmed_ids, titles, authors, citations)
                   ]
        return results

    def scan_results(self, limit: int = 100) -> Generator:
        """
        Yields search results up to the given limit.

        Args:
            limit: Maximum number of articles to yield.

        Yields:
            Articles from the search results.
        """
        for at in range(self.n_results):
            if at == limit:
                break

            if at == len(self.articles):
                self.grepMoreResults()
            yield self.articles[at]
