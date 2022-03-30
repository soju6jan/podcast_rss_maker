import os, sys, traceback, re, json, threading, time, shutil, platform, requests
from datetime import datetime
from flask import request, render_template, jsonify, redirect, send_file

from .plugin import P, logger, package_name, ModelSetting, LogicModuleBase, app
from tool_base import ToolUtil
from support.base import d, default_headers

from lxml import etree as ET
import lxml.builder as builder
from lxml.builder import E

name = 'podbbang'

class LogicPodbbang(LogicModuleBase):
    db_default = { 
        'db_version' : '1',
        'pb_feed_count' : '30',
    }

    def __init__(self, P):
        super(LogicPodbbang, self).__init__(P, 'setting')
        self.name = name


    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        try:
            arg['tmp_pb_api'] = ToolUtil.make_apikey_url(f"/{package_name}/api/podbbang/12548")
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")
    

    def process_api(self, sub, req):
        return self.make_xml(sub)


    def make_xml(self, channel_id):
        try:
            data = requests.get(f"https://app-api6.podbbang.com/channels/{channel_id}", headers=default_headers).json()
            tmp = builder.ElementMaker(nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            root = tmp.rss(version="2.0")
            EE = builder.ElementMaker(namespace="http://www.itunes.com/dtds/podcast-1.0.dtd", nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            channel_tag = (
                E.channel(
                    E.title(data['title']),
                    E.link(f"https://podbbang.com/channels/{channel_id}"),
                    E.description(),
                    E.language('ko-kr'),
                    E.copyright(''),
                    EE.subtitle(),
                    EE.author(),
                    EE.summary(data['description']),
                    EE.category(text=data['category']['name']),
                    EE.image(href=data['image']),
                    EE.explicit('no'),
                )
            )
            root.append(channel_tag)
            url = f"https://app-api6.podbbang.com/channels/{channel_id}/episodes?offset=0&limit={ModelSetting.get('pb_feed_count')}&sort=desc&episode_id=0&focus_center=0"
            data = requests.get(url, headers=default_headers).json()
            for item in data['data']:
                channel_tag.append(E.item (
                    E.title(item['title']),
                    EE.subtitle(),
                    EE.summary(item['description']),
                    E.guid(str(item['id'])),
                    E.pubDate(datetime.strptime(item['publishedAt'], "%Y-%m-%d %H:%M:%S").strftime('%a, %d %b %Y %H:%M:%S') + ' +0900'),
                    EE.duration(item['media']['duration']),
                    E.enclosure(url=item['media']['url'], length=str(item['media']['length']), type='audio/mp3'),
                    E.description()
                ))
            return app.response_class(ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8"), mimetype='application/xml')
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    