import scrapy
from scrapy.selector import Selector
#from items import PauzaItem
import re


class PauzaSpider(scrapy.Spider):

    name = "pauza"
    start_urls = ['http://www.pauza.hr/sitemap.xml']

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
        restoran_urls = Selector(response=response).xpath('//div[@class="index-items"]//strong/a/@href').extract()
        area = re.search('.*/(.*)', response.url).group(1)

        self.area_restorant_mapper[area] = set(restoran_urls)

        item = {}
        for restoran_url in restoran_urls:
            restoran_name = re.search('.*/(.*)?.*', restoran_url).group(1)
            item['restoran_name'] = restoran_name
            item['area'] = area

            for city, area_urls in self.city_area_mapper.items():
                if area_url in area_urls:
                    item['city'] = city

            print item
