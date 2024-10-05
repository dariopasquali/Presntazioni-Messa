import requests

news_url = "https://corogiovani.pythonanywhere.com/get_news"


class NewsFetcher:
    @staticmethod
    def fetch_news():
        response = requests.get(news_url)
        return response.text
