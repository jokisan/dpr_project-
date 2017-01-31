import scrapy
from scrapy.selector import Selector
import re
from time import sleep
from selenium import webdriver


class PauzaItem(scrapy.Item):
    city = scrapy.Field()
    area = scrapy.Field()
    restoran_name = scrapy.Field()
    phone_number = scrapy.Field()


class PauzaSpider(scrapy.Spider):

    name = "pauza"
    start_urls = ['http://www.pauza.hr/sitemap.xml']
    driver = webdriver.Chrome('/usr/bin/chromedriver')

    city_area_mapper = {
        'zagreb': set(),
        'rijeka': set(),
        'velika-gorica': set()
    }

    area_restorant_mapper = dict()

    def parse(self, response):
        urls = re.findall('<loc>(.*)<\/loc>', response.text)
        area_urls = [re.search('(.*)\/dostava', url).group(1) for url in urls if 'dostava' in url]

        for area_url in area_urls:
            for city_name in self.city_area_mapper.keys():
                if city_name in area_url:
                    self.city_area_mapper[city_name].add(area_url)
                    break

        for city_area_urls in self.city_area_mapper.values():
            for area_url in city_area_urls:
                yield scrapy.Request(area_url, callback=self.parse_restorants)

    def parse_restorants(self, response):
        area_url = response.url
        restoran_names = Selector(response=response).xpath('//div[@class="index-items"]//strong/a/text()').extract()

        area = re.search('.*/(.*)', response.url).group(1)
        area = area.split('-')[-1]
        self.area_restorant_mapper[area] = set(restoran_names)

        item = PauzaItem()
        cache = {}

        for restoran_name in restoran_names:
            item['restoran_name'] = restoran_name.encode('utf-8')
            item['area'] = area
            if restoran_name in cache:
                item['phone_number'] = cache.get(restoran_name)
            else:
                item['phone_number'] = self.get_phone_number(restoran_name)
                cache[restoran_name] = item.get('phone_number')

            for city, area_urls in self.city_area_mapper.items():
                if area_url in area_urls:
                    item['city'] = city

            yield item

    def get_phone_number(self, restoran_name):
        url = 'http://www.google.com/search?q=' + restoran_name
        self.driver.get(url)
        sleep(5)
        content = self.driver.page_source

        spans_text = Selector(text=content).xpath('//span/text()').extract()

        phone_numbers = [re.search('([0-9]+ [0-9]+ [0-9]+)', phone_numbers).group(1)
                        for phone_numbers in spans_text
                        if re.search('([0-9]+ [0-9]+ [0-9]+)', phone_numbers) is not None]

        phone_numbers = set(phone_numbers)

        return phone_numbers
