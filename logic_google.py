# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import requests
from datetime import datetime, timedelta

# third-party
from flask import request, render_template, jsonify
from lxml import etree as ET
import lxml.builder as builder
from lxml.builder import E
from lxml import html

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery, SystemModelSetting
from framework.util import Util
from framework.common.plugin import LogicModuleBase
from framework.common.share import RcloneTool2
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
#########################################################

class LogicGoogle(LogicModuleBase):
    db_default = {}

    def __init__(self, P):
        super(LogicGoogle, self).__init__(P, 'setting')
        self.name = 'google'

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        if sub == 'setting':
            arg['sample'] = SystemModelSetting.get('ddns')
            arg['apikey'] = SystemModelSetting.get('auth_apikey') if SystemModelSetting.get_bool('auth_use_apikey') else ''
            return render_template('{package_name}_{module_name}_{sub}.html'.format(package_name=P.package_name, module_name=self.name, sub=sub), arg=arg)
        return render_template('sample.html', title='%s - %s' % (package_name, sub))
    

    def process_api(self, sub, req):
        try:
            remote = req.args.get('remote')
            title = req.args.get('title')
            image = req.args.get('image') if req.args.get('image') is not None else ''
            desc = req.args.get('desc') if req.args.get('desc') is not None else ''
            genre = req.args.get('genre') if req.args.get('genre') is not None else ''
            return self.make_xml(remote, title, image, desc, genre)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    def make_xml(self, remote, title, image, desc, genre):
        try:
            logger.debug('%s %s %s %s %s', remote, title, image, desc, genre)
            tmp = builder.ElementMaker(nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            root = tmp.rss(version="2.0")
            EE = builder.ElementMaker(namespace="http://www.itunes.com/dtds/podcast-1.0.dtd", nsmap={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
            channel_tag = (
                E.channel(
                    E.title(title),
                    E.link(),
                    E.description(desc),
                    E.language('ko-kr'),
                    E.copyright(''),
                    EE.subtitle(),
                    EE.author(),
                    EE.summary(desc),
                    EE.category(genre),
                    EE.image(image),
                    EE.explicit('no'),
                )
            )
            root.append(channel_tag)
            import rclone 
            lsjson = RcloneTool2.lsjson(rclone.Logic.path_rclone, rclone.Logic.path_config, remote, option=['--files-only'])
            startdate= datetime.now() + timedelta(days=len(lsjson)*-1)
            for item in lsjson:
                logger.debug(item)
                if not item['MimeType'].startswith('audio'):
                    continue
                channel_tag.append(E.item (
                    E.title(item['Name']),
                    #EE.subtitle(item['Name']),
                    EE.summary(item['Name']),
                    E.guid(item['Name']),
                    E.pubDate(startdate.strftime('%a, %d %b %Y %H:%M:%S') + ' +0900'),
                    EE.duration(),
                    E.enclosure(url='https://drive.google.com/uc?export=download&id={}'.format(item['ID']), length=str(item['Size']), type=item['MimeType']),
                    #E.description(item['Name'])
                ))
                startdate = startdate + timedelta(days=1)
            return app.response_class(ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8"), mimetype='application/xml')
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    
    