"""
PubMEDapi
~~~~~~~~~~~~~~~~

This API defines the interface to PubMED.

Author: Lorenz Hexemer
"""
from typing import List, Generator, Optional
from bs4 import BeautifulSoup as html
import requests as http

from .PubMedArticle import PubMedArticle


class PubMedSearch:
    def __init__(self, search_str: Optional[str] = None,
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
        if search_str is not None:
            query = self.buildQuery(
                search_str, not_older_than, abstract_available
            )
            self.startFromQuery(query)

    def startFromQuery(self, query: str) -> None:
        """
        Starts a search defined by query from the first page of results ()

        Args:
            query (str): Full pubmed http query
        """
        self.results_page = 1
        doc = self.sendQuery(query)

        results = doc.find('div', class_="results-amount")
        self.n_results = int(results.h3.span.text.replace(',', ''))
        print(f"found {self.n_results} articles.")

        self.articles = self.extractResults(doc)

    def buildQuery(self,
                   search_str: str,
                   not_older_than: Optional[str],
                   abstract_available: bool
                   ) -> str:
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
        self.query = (
            f'https://pubmed.ncbi.nlm.nih.gov/'
            f'?term={self.search_str}'
        )
        if not_older_than:
            if not_older_than == "1_year":
                self.query += "&filter=datesearch.y_1"
            elif not_older_than == "5_years":
                self.query += "&filter=datesearch.y_5"
            elif not_older_than == "10_years":
                self.query += "&filter=datesearch.y_10"
            else:
                raise Exception(f'Invalid search flag "{not_older_than}"')

        if abstract_available:
            self.query += "&filter=simsearch1.fha"

        return self.query

    def grepMoreResults(self) -> None:
        """
        Fetches more results from the PubMed website.
        """
        self.results_page += 1
        doc = self.sendQuery(self.query)
        self.articles += self.extractResults(doc)

    def sendQuery(self, query: str) -> None:
        """
        Sends the initial query for the current page (from self.results_page)

        Args:
            query: full http query to pubmed

        Returns
            Parsed BeatutiflSoup document.
        """
        query += f'&page={self.results_page}'
        response = http.get(query)
        doc = html(response.text, "html.parser")
        return doc

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
        authors_long = [s.text for s in docsum_autorhs[::2]]
        authors_short = [s.text for s in docsum_autorhs[1::2]]
        citations = [
            c.text
            for c in doc.find_all('span', class_="docsum-journal-citation")
        ]

        results = [
            PubMedArticle(*args)
            for args in zip(
                pubmed_ids,
                titles,
                authors_long,
                authors_short,
                citations
            )
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
