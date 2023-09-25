"""
PubMEDapi
~~~~~~~~~~~~~~~~

This API defines the interface to PubMED.

Author: Lorenz Hexemer
"""
import os
import dill
from types import Optional

from PubMedArticle import PubMedArticle
from PubMedSearch import PubMedSearch


class PubMedCrawler:
    def __init__(self, path: Optional[str] = None) -> None:
        """
        Initializes a PubMedCrawler object.

        Args:
            path (Optional[str]): The path to the archive directory.
        """
        self.results = {}
        if path is not None:
            self.setArchivePath(path)

    def setArchivePath(self, path: str) -> None:
        """
        Sets the archive path and creates the directory if it doesn't exist.

        Args:
            path (str): The path to the archive directory.
        """
        self.archivepath = path
        if not os.path.isdir(path):
            os.mkdir(path)

    def searchFor(self,
                  search_str: str,
                  limit: int = 1000,
                  not_older_than: bool = True,
                  abstract_available: bool = True,
                  **kwargs) -> None:
        """
        Searches for articles based on the given search string
        and other filters.

        Args:
            search_str (str): The search query string.
            limit (int): Maximum number of articles to search for.
            not_older_than (bool): Whether to filter articles based on age.
            abstract_available (bool): Whether to filter for articles
                with abstracts or not.
            **kwargs: Additional keyword arguments.
        """
        search_str = search_str.replace(' ', '+')
        search_results = PubMedSearch(search_str,
                                      not_older_than=not_older_than,
                                      abstract_available=abstract_available,
                                      **kwargs
                                      )
        for article in search_results.scan_results(limit):
            self.addArticle(article)
            self.addFoundBy(article, search_str)

    def addArticle(self, article: PubMedArticle) -> None:
        """
        Adds an article to the results dictionary.

        Args:
            article (PubMedArticle): The article to add.

        Returns:
            bool: True if the article was added, False otherwise.
        """
        if article.id in self.results.keys():
            return False

        article.load()
        if hasattr(self, 'archivepath') and article.abstract is not None:
            self.saveText(article.id, article.abstract)
        info = {
            'id': article.id,
            'title': article.title,
            'authors': article.authors,
            'citation': article.publication,
            'found_by': []
        }
        if hasattr(self, 'archivepath'):
            self.saveMeta(article.id, info)

        info['abstract'] = article.abstract
        self.results[article.id] = info

        return True

    def saveText(self, article_id: int, abstract: str) -> None:
        """
        Saves the abstract text of an article to a file.

        Args:
            article_id (int): The ID of the article.
            abstract (str): The abstract text.
        """
        with open(f"{self.archivepath}/{article_id}.txt", 'w') as fp:
            fp.write(abstract)

    def saveMeta(self, article_id: int, info: dict) -> None:
        """
        Saves the metadata of an article to a file.

        Args:
            article_id (int): The ID of the article.
            info (Dict): The metadata information.
        """
        with open(f"{self.archivepath}/{article_id}.meta", 'w') as fp:
            for label, value in info.items():
                value = '' if value == [] else value + "\n"
                fp.write(f"{label}: {value}")

    def addFoundBy(self, article: PubMedArticle, search_str: str) -> None:
        """
        Adds a search string to the 'found_by' list of an article.

        Args:
            article (PubMedArticle): The article to update.
            search_str (str): The search string.
        """
        self.results[article.id]['found_by'].append(search_str)
        if hasattr(self, 'archivepath'):
            self.saveFoundBy(article.id, search_str)

    def saveFoundBy(self, article_id: int, search_str: str) -> None:
        """
        Appends a search string to the metadata file of an article.

        Args:
            article_id (int): The ID of the article.
            search_str (str): The search string.
        """
        with open(f"{self.archivepath}/{article_id}.meta", 'a') as fp:
            fp.write(f"\n - {search_str}")

    def save(self, file_name: str) -> None:
        """
        Save the state of the crawler to a file.

        Args:
            file_name (str): The name of the file to save the state to.

        Returns:
            None
        """
        child_vars = []
        for var in dir(self):
            ref = getattr(self, var)
            if "__" in var or isinstance(ref, callable()):
                continue
            child_vars.append(var)

        with open(file_name, 'wb') as fp:
            dill.dump(child_vars, fp)
            for var in child_vars:
                dill.dump(getattr(self, var), fp)

    @staticmethod
    def load(file_name: str) -> 'PubMedCrawler':
        """
        Load the state of the crawler from a file.

        Args:
            file_name (str): The name of the file to load the state from.

        Returns:
            WikiCrawler: The loaded instance of the WikiCrawler.
        """
        empty = PubMedCrawler()
        with open(file_name, 'rb') as fp:
            child_vars = dill.load(fp)
            for var in child_vars:
                loaded = dill.load(fp)
                setattr(empty, var, loaded)
        return empty
