# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback

# third-party
from flask import Blueprint, request, render_template, redirect, jsonify 
from flask_login import login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio, check_api
from system.model import ModelSetting as SystemModelSetting

# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
from .logic import Logic
from .model import ModelSetting
#########################################################

blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

menu = {
    'main' : [package_name, 'Podcast RSS Maker'],
    'sub' : [
        ['setting', '설정'], ['log', '로그']
    ],
    'category' : 'service'
}

plugin_info = {
    'version' : '0.1.0.0',
    'name' : 'Podcast RSS Maker',
    'category_name' : 'service',
    'developer' : 'soju6jan',
    'description' : 'Podcast 지원',
    'home' : 'https://github.com/soju6jan/podcast_feed_maker',
    'more' : '',
}

def plugin_load():
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()

#########################################################
# WEB Menu   
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/setting' % package_name)

@blueprint.route('/<sub>')
@login_required
def first_menu(sub): 
    if sub == 'setting':
        arg = ModelSetting.to_dict()
        arg['package_name']  = package_name
        arg['tmp_pb_api'] = '%s/%s/api/podbbang/%s' % (SystemModelSetting.get('ddns'), package_name, '12548')
        if SystemModelSetting.get_bool('auth_use_apikey'):
            arg['tmp_pb_api'] += '?apikey=%s' % SystemModelSetting.get('auth_apikey')
        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI                                                          
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    try:
        if sub == 'setting_save':
            ret = ModelSetting.setting_save(request)
            return jsonify(ret)
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())  

#########################################################
# API - 외부
#########################################################
@blueprint.route('/api/<sub>/<sub2>', methods=['GET', 'POST'])
@check_api
def api(sub, sub2):
    try:
        if sub == 'podbbang':
            from .logic_normal import LogicNormal
            return LogicNormal.make_podbbang(sub2)
        elif sub == 'klive':
            from .logic_normal import LogicNormal
            return LogicNormal.make_klive(sub2)
    except Exception as e:
        logger.debug('Exception:%s', e)
        logger.debug(traceback.format_exc())
