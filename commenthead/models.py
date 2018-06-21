# -*- coding: utf-8 -*-

from django.db import models

class DailyMailHomepage(models.Model):

    crawl_time  = models.DateTimeField(auto_now_add=True)
    html = models.TextField()
