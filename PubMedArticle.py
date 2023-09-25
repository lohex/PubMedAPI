"""
PubMEDapi
~~~~~~~~~~~~~~~~

This API defines the interface to PubMED.

Author: Lorenz Hexemer
"""

import re
import requests as http
from bs4 import BeautifulSoup as html
from typing import Optional, Generator


class PubMedArticle:
    """
    Represents an article from PubMed.

    Attributes:
        id (str): The PubMed ID of the article.
        title (Optional[str]): The title of the article.
        authors (Optional[str]): The authors of the article.
        publication (Optional[str]): The publication where the article
            was published.
        doc (Optional[str]): The HTML content of the article page.
        abstract (Optional[str]): The abstract of the article.
        fulltext_link (Optional[str]): The link to the full text
            of the article.
    """
    def __init__(self, id: str,
                 title: Optional[str] = None,
                 authors: Optional[str] = None,
                 publication: Optional[str] = None
                 ) -> None:
        """
        Initializes a new instance of the PubMedArticle class.
        Args:
            id (str): The PubMed ID of the article.
            title (Optional[str], optional): The title of the article.
              Defaults to None.
            authors (Optional[str], optional): The authors of the article.
              Defaults to None.
            publication (Optional[str], optional): The publication where the
              article was published. Defaults to None.
        """
        self.id = id
        if title is not None:
            self.setMetaData(title, authors, publication)

    def setMetaData(self, title: str, authors: str, publication: str) -> None:
        """
        Sets the metadata for the article.

        Args:
            title (str): The title of the article.
            authors (str): The authors of the article.
            publication (str): The publication where the article was published.
        """
        self.title = title.strip()
        self.authors = authors.strip()
        self.publication = publication.strip()

    def __str__(self) -> str:
        """
        Returns a string representation of the article.

        Returns:
            str: A string representation of the article.
        """
        if hasattr(self, "title"):
            return (
                f"{self.authors} {self.title}"
                f"{self.publication} PMID {self.id}"
            )
        else:
            return f"PMID {self.id}"

    def load(self) -> None:
        """
        Loads the article details from PubMed using its ID.
        """
        response = http.get(f'https://pubmed.ncbi.nlm.nih.gov/{self.id}/')
        self.doc = html(response.text)
        self.abstract = self.doc.find('div', class_="abstract-content")
        if self.abstract is not None:
            self.abstract = re.sub("\n+", "\n", self.abstract.text.strip())
        if not hasattr(self, "title"):
            self.loadMetaData()
        pmc_link = self.doc.find("a", title="Free full text at PubMed Central")
        self.fulltext_link = None
        if pmc_link is not None:
            self.fulltext_link = pmc_link.attrs['href']

    def loadMetaData(self) -> None:
        """
        Loads metadata from the document.
        """
        title = self.doc.find('h1', class_="heading-title").text
        button_id = "full-view-journal-trigger"
        journal = self.doc.find('button', id=button_id).text.strip()
        issue = self.doc.find('span', class_="cit").text.strip()
        publication = f"{journal}. {issue}"

        authors = self.doc.find('div', class_="authors-list").text
        authors = re.sub(r"(\d\s)+", "", authors)
        authors = re.sub(r"\s+", " ", authors)
        authors = ', '.join(
            [re.sub("([A-Z])[^ ]+ ([^ ]) ([^ ]+)", "\\3 \\1\\2", a).strip()
             for a in authors.split(',')]) + "."

        self.setMetaData(title, authors, publication)

    def articles_citing(self, limit: int = 100) -> Generator:
        """
        Yields articles citing the current document up to the given limit.

        Args:
            limit: Maximum number of articles to yield.

        Yields:
            Article citations.
        """
        self.citing_page = 1
        self.grepMoreResults()
        for at in range(self.n_citations):
            if at == limit:
                break

            if at == len(self.citations):
                self.grepMoreResults()
            yield self.citations[at]

    def grepMoreResults(self) -> None:
        """
        Fetches more results from the PubMed website.
        """
        self.citing_page += 1
        link = (
            f'https://pubmed.ncbi.nlm.nih.gov/?linkname=pubmed_pubmed_citedin&'
            f'from_uid={self.id}&page={self.citing_page}'
        )
        response = http.get(link)
        doc = html(response.text)
        self.citing += self.extractRefferings(doc)

    def extractRefferings(self, doc) -> list:
        """
        Extracts references from the given document.

        Args:
            doc: Document to extract references from.

        Returns:
            List of extracted references.
        """
        page_links = doc.find_all('a', class_="docsum-title")
        pubmed_ids = [p.attrs['data-article-id'] for p in page_links]
        titles = [p.text for p in page_links]
        class_name = "docsum-authors"
        authors = [s.text for s in doc.find_all('span', class_=class_name)]
        class_name = "docsum-journal-citation"
        citations = [c.text for c in doc.find_all('span', class_=class_name)]

        results = [
            PubMedArticle(id, title, authors, pub)
            for id, title, authors, pub
            in zip(pubmed_ids, titles, authors, citations)
        ]
        return results
