import os, sys, traceback, re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, redirect
from framework import app, path_data, path_app_root, db, scheduler, SystemModelSetting, socketio, celery, get_logger
from plugin import LogicModuleBase, get_model_setting, Logic, default_route, PluginUtil

class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

    menu = {
        'main' : [package_name, u'Podcast RSS Maker'],
        'sub' : [
            ['podbbang', u'팟빵'], ['google', u'구글 드라이브'], ['log', u'로그']
        ],
        'sub2' : {
            'podbbang' : [
                ['setting', u'설정'], 
            ],
            'google' : [
                ['setting', u'설정'],
            ],
        },
        'category' : 'service'
    }

    plugin_info = {
        'version' : '0.2.0.0',
        'name' : u'Podcast RSS Maker',
        'category_name' : 'service',
        'developer' : 'soju6jan',
        'description' : u'Podcast 지원',
        'home' : 'https://github.com/soju6jan/podcast_feed_maker',
        'more' : '',
    }

    ModelSetting = get_model_setting(package_name, logger)
    logic = None
    module_list = None
    home_module = 'podbbang'

from tool_base import d
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting

def initialize():
    try:
        app.config['SQLALCHEMY_BINDS'][P.package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '{package_name}.db'.format(package_name=P.package_name)))
        PluginUtil.make_info_json(P.plugin_info, __file__)
        from .logic_podbbang import LogicPodbbang
        from .logic_google import LogicGoogle

        P.module_list = [LogicPodbbang(P), LogicGoogle(P)]
        P.logic = Logic(P)
        default_route(P)
    except Exception as e: 
        P.logger.error('Exception:%s', e)
        P.logger.error(traceback.format_exc())

initialize()



