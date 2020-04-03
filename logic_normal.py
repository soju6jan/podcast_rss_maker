# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import requests
from datetime import datetime

# third-party
from lxml import etree as ET
import lxml.builder as builder
from lxml.builder import E
from lxml import html

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery, SystemModelSetting
from framework.util import Util

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting
#########################################################

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer' : ''
} 


pb_headers = {
    'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.2; Nexus 6 Build/KOT49H)',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Podbbang' : 'os=iOS&osver=4.4.2&ver=4.35.271&device=MQAG2KH/A&device_id=359090030208175&id=4349893&auth_code=cdc986a2d1184895178e8129231a39cc6c7c31ab&nick=&is_login=N&is_adult=N'
}

class LogicNormal(object):
    @staticmethod
    def make_podbbang(channel_id):
        try:
            url = 'http://www.podbbang.com/ch/%s' % channel_id
            logger.debug(url)
            tree = html.fromstring(requests.get(url).content)
            tmp = builder.ElementMaker(nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            root = tmp.rss(version="2.0")
            EE = builder.ElementMaker(namespace="http://www.itunes.com/dtds/podcast-1.0.dtd", nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            channel_tag = (
                E.channel(
                    E.title(tree.xpath('//*[@id="podcastDetails"]/div[3]/h3/text()')[0].strip()),
                    E.link(url),
                    E.description(tree.xpath('//*[@id="podcastDetails"]/div[3]/div[1]/text()')[0].strip()),
                    E.language('ko-kr'),
                    E.copyright(''),
                    EE.subtitle(),
                    EE.author(),
                    EE.summary(tree.xpath('//*[@id="podcastDetails"]/div[3]/div[1]/text()')[0].strip()),
                    EE.category(text=tree.xpath('//*[@id="podcastDetails"]/div[3]/span/a/text()')[0].strip()),
                    EE.image(href=tree.xpath('//*[@id="podcastDetails"]/div[3]/img')[0].attrib['src']),
                    EE.explicit('no'),
                    #EE.keywords(tree.xpath('//*[@id="header_wrap"]/div/div[1]/div[2]/span/a/text()')[0].strip()),
                )
            )
            root.append(channel_tag)
            data = requests.get('http://app-api4.podbbang.com/channel?channel=%s&order=desc&count=%s&page=1' % (channel_id, ModelSetting.get('pb_feed_count')), headers=pb_headers).json()
            for item in data['list']:
                channel_tag.append(E.item (
                    E.title(item['title']),
                    EE.subtitle(item['summary']),
                    EE.summary(item['summary']),
                    E.guid(item['episode']),
                    E.pubDate(datetime.strptime(item['date'], "%Y-%m-%d %H:%M:%S").strftime('%a, %d %b %Y %H:%M:%S') + ' +0900'),
                    EE.duration(item['duration']),
                    E.enclosure(url=item['file_url'], length=item['file_size'], type='audio/mp3'),
                    E.description(item['summary'])
                ))
            return app.response_class(ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8"), mimetype='application/xml')
        except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())

    @staticmethod
    def make_klive(sub):
        try:
            from klive.logic_klive import LogicKlive
            from klive.model import  ModelSetting as KliveModelSetting
            if LogicKlive.source_list is None:
                tmp = LogicKlive.channel_load_from_site()
            instance = LogicKlive.source_list['pooq'] 
            #logger.debug(instance.get_channel_list())
            #instance = SourcePooq('pooq', arg['pooq_id'], arg['pooq_pw'], None)

            token = None
            if KliveModelSetting.get_bool('use_token'):
                token = SystemModelSetting.get('unique')

            

            tmp = builder.ElementMaker(nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            root = tmp.rss(version="2.0")
            EE = builder.ElementMaker(namespace="http://www.itunes.com/dtds/podcast-1.0.dtd", nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            channel_tag = (
                E.channel(
                    E.title('KLive Radio'),
                    E.link(),
                    E.description('KLive Radio'),
                    E.language('ko-kr'),
                    E.copyright(''),
                    EE.subtitle(),
                    EE.author(),
                    EE.summary('KLive Radio'),
                    EE.category('Radio'),
                    EE.image(),
                    EE.explicit('no'),
                    EE.keywords('Radio'),
                )
            )
            root.append(channel_tag)
            for idx, c in enumerate(instance.get_channel_list()):
                if not c.is_tv:
                    logger.debug(c.title)
                    logger.debug(c.current)
                    logger.debug(c.source_id)
                    logger.debug(c.source)
                    url = '%s/klive/api/url.m3u8?m=url&s=%s&i=%s' % (SystemModelSetting.get('ddns'), c.source, c.source_id)
                    if token is not None:
                        url += '&token=%s' % token

                    channel_tag.append(E.item (
                        E.title(c.title),
                        EE.subtitle(c.current),
                        EE.summary(c.current),
                        E.guid(str(idx+1)),
                        E.pubDate(datetime.now().strftime('%a, %d %b %Y %H:%M:%S') + ' +0900'),
                        #EE.duration(),
                        E.enclosure(url=url), #, length=item['file_size'], type='audio/mp3'),
                        E.description(c.current)
                    ))
            return app.response_class(ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8"), mimetype='application/xml')
        except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())