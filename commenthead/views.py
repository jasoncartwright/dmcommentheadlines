# -*- coding: utf-8 -*-
import logging, re, json
from django.http import HttpResponse
from google.appengine.api import urlfetch
from libs.beautifulsoup import BeautifulSoup
from django.views.decorators.cache import cache_page

from models import DailyMailHomepage

@cache_page(600)
def home(request):
    last_hp = DailyMailHomepage.objects.all().latest("crawl_time")
    return HttpResponse(last_hp.html)


def crawl(request):

    dm_hp_url = "http://www.dailymail.co.uk/home/index.html"
    dm_comment_url = "https://secured.dailymail.co.uk/reader-comments/p/asset/readcomments/%s?max=1&sort=voteRating&order=desc&rcCache=shout"
    article_id_regex = r"article-(\d*)"

    dm_hp_url_result = urlfetch.fetch(dm_hp_url, deadline=30)

    dm_hp_content = u""

    if dm_hp_url_result.status_code == 200:

        logging.info("Got DM homepage %s bytes" % len(dm_hp_url_result.content))
        dm_hp_content = str(dm_hp_url_result.content)
        dm_hp_content_soup = BeautifulSoup(dm_hp_content)
        headlines = dm_hp_content_soup.findAll("a", {"itemprop" : "url"})
        logging.info("Found %s headlines" % len(headlines))
        for headline in headlines:
            headline_url = headline["href"]
            article_re = re.compile(article_id_regex)
            headline_id = article_re.findall(headline_url)[0]
            headline_comment_url = dm_comment_url % headline_id
            logging.info(headline_comment_url)
            headline_comment_url_result = urlfetch.fetch(headline_comment_url, deadline=30, headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "X-Requested-With": "XMLHttpRequest"})
            # logging.info(headline_comment_url_result.content)
            try:
                comment = json.loads(headline_comment_url_result.content)["payload"]["page"][0]["message"]
                logging.info(comment)
                headline.string = comment
            except IndexError:
                pass

        hp_str = str(dm_hp_content_soup)
        hp_str = hp_str.replace("http://scripts.dailymail.co.uk","https://scripts.dailymail.co.uk")
        hp_str = hp_str.replace("http://i.dailymail.co.uk","https://i.dailymail.co.uk")

        new_hp = DailyMailHomepage(
            html = hp_str
        )
        new_hp.save()

    return HttpResponse("OK")
