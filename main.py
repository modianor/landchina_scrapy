from scrapy import cmdline

cmdline.execute("scrapy crawl landchina -a start=2005-06-1 -a end=2005-06-30".split())
