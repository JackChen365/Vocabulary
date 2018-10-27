import datetime
import html
import json
import os
import re
import time

import django
from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.files import File
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, render_to_response
# Create your views here.
from django.template import loader
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from app.admin import admin_site
from app.analysis.analyzer import Analyzer
from app.models import HighFrequencyWord, Vocabulary
from app.session.models import ImportSession, ImportSessionFile
from app.tasks import upload_task
from app.user.forms import RegisterForm
from app.user.models import QueryWordTag, ImportRecord, UserVocabulary, QueryTranslateRecord, SentenceKeyword, \
    SentenceRelative
from app.views import remote_tmp, get_analyzer
from vocabulary.settings import MEDIA_ROOT


class RegisterView(View):
    """注册用户信息"""

    def get(self, request):
        form = RegisterForm()
        context = {
            "site_title": admin_site.site_title,
            "site_header": admin_site.site_register_header,
            "title": "Sign up for vocabulary",
            'form': form,
        }
        return render(request, 'user/user_register.html', context)

    def post(self, request):
        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime());
        username = request.POST.get('username', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        email = request.POST.get('email', '')
        errors = []
        register_form = RegisterForm(request.POST)  # b********
        if not register_form.is_valid():
            errors.extend(register_form.errors.values())
            return render_to_response("user/user_register.html",
                                      {'cur_time': cur_time,
                                       'username': username,
                                       'email': email,
                                       'errors': errors})
        if password1 != password2:
            errors.append("两次输入的密码不一致!")
            return render_to_response("user/user_register.html",
                                      {'cur_time': cur_time,
                                       'username': username,
                                       'email': email,
                                       'errors': errors})
        filter_result = User.objects.filter(username=username).count()
        if 0 < filter_result:
            errors.append("用户名已存在")
            return render_to_response("user/user_register.html",
                                      {'cur_time': cur_time,
                                       'username': username,
                                       'email': email,
                                       'errors': errors})
        User.objects.create_user(username=username, password=password1, is_superuser=True, is_staff=True,
                                 email=email)
        # 登录前需要先验证
        try:
            new_user = auth.authenticate(username=username, password=password1)
            if new_user is not None:
                auth.login(request, new_user)
                return HttpResponseRedirect("/admin/login/")
        except Exception as e:
            errors.append(str(e))
            return render_to_response("user/user_register.html",
                                      {'cur_time': cur_time,
                                       'username': username,
                                       'email': email, 'errors': errors})


class UploadFile(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/admin/login/?next=%s' % request.path)
        else:
            context = {
                "title": "Select file Form",
                "sub_title": "Only support .srt or pdf file",
                "has_permission": True,
                "site_url": admin_site.site_url,
                "site_title": admin_site.site_title,
                "site_header": admin_site.site_header,
            }
            return HttpResponse(loader.get_template('user/upload_file.html').render(context, request))

    def post(self, request):
        if request.method == 'POST':  # 获取对象
            if 0 == len(request.FILES):
                return HttpResponse("没有上传任务文件！")
            else:
                export_file = request.FILES.get("export_file")
                if export_file is None:
                    return HttpResponse("上传失败！")
                else:
                    record = ImportRecord(user=request.user)
                    record.save()
                    record.export_file.save(export_file.name, File(export_file))
                    unknown_file = request.FILES.get("unknown_file")
                    if unknown_file is not None:
                        record.unknown_file.save(unknown_file.name, File(unknown_file))
                    # 执行异步任务
                    # upload_task(request.user.id, record.id)
                    upload_task.delay(request.user.id, record.id)
                    data = {'is_valid': True, "data": "数据提交成功！"}
                    return JsonResponse(data=data)


class QueryFile(View):

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/admin/login/?next=%s' % request.path)
        else:
            context = {
                "title": "Select file Form",
                "sub_title": "Only support .srt or pdf file",
                "has_permission": True,
                "site_url": admin_site.site_url,
                "site_title": admin_site.site_title,
                "site_header": admin_site.site_header,
            }
            return HttpResponse(loader.get_template('user/query_file.html').render(context, request))

    def post(self, request):
        if 0 == len(request.FILES):
            return HttpResponse("没有上传任务文件！")
        else:
            export_file = request.FILES.get("export_file")
            if not export_file:
                return HttpResponse("上传失败！")
            else:
                # 清理tmp目录
                remote_tmp()
                # 分析文件
                tmp_path = os.path.join(MEDIA_ROOT, "tmp")
                if not os.path.exists(tmp_path):
                    os.makedirs(tmp_path)
                target_path = os.path.join(tmp_path, export_file.name)
                target_file = open(target_path, 'wb+')  # 打开特定的文件进行二进制的写操作
                for chunk in export_file.chunks():  # 分块写入文件
                    target_file.write(chunk)
                target_file.close()
                analyzer = get_analyzer(target_path)
                data = analyzer.get_data()
                # 查询出数据库己存在数据
                query_set = UserVocabulary.objects.filter()
                # 过滤出所有不存在单词
                query_items = []
                for item in data:
                    if 0 == query_set.filter(Q(word=item.name)).count():
                        query_items.append(item)
                need_query_items = [item.name for item in query_items]
                result_items = list(Vocabulary.objects.filter(word__in=need_query_items).all())
                template = loader.get_template('user/query_result.html')
                # 将搜索词高亮,例句最大只取5条
                for result_item in result_items:
                    find_item = [item for item in data if item.name == result_item.word]
                    if find_item:
                        result_item.frequency = find_item[0].count
                        result_item.sentence = find_item[0].sentence[:5]
                        word_pattern = re.compile(r'(%s)' % result_item.word, re.IGNORECASE)
                        for sentence_item in result_item.sentence:
                            sentence_item.sentence = word_pattern.sub(r'<font color="red"><strong>\1</strong></font>',
                                                                      sentence_item.sentence)
                result_items.sort(key=lambda ob: ob.frequency, reverse=True)
                context = {
                    "title": "File:%s" % export_file.name,
                    "sub_title": "Word(%d) Unknown(%d)" % (len(need_query_items), len(result_items)),
                    "word_items": result_items,
                    "has_permission": True,
                    "site_url": admin_site.site_url,
                    "site_title": admin_site.site_title,
                    "site_header": admin_site.site_header,
                }
                html_text = template.render(context, request)
                return HttpResponse(html.unescape(html_text))


def query_word_box(request):
    """查询单词信息"""
    if request.method == 'GET':
        word = request.GET.get("word")
        if not word:
            return HttpResponse("<h1>%s:Search not result!</h1>" % word)
        else:
            query_item = Analyzer.lemmatize(word)
            if not query_item:
                return HttpResponse("<h1>%s:Search not result!</h1>" % word)
            else:
                try:
                    word_item = Vocabulary.objects.get(word=word)
                except Vocabulary.DoesNotExist:
                    return HttpResponse("<h1>%s:Search not result!</h1>" % word)
                else:
                    # 查词是否为用户词库
                    try:
                        word_item.is_user_word = UserVocabulary.objects.filter(word=word_item.word).exists()
                    except HighFrequencyWord.DoesNotExist:
                        print("word:%s can't found!" % word)
                    context = {
                        "item": word_item,
                    }
                    return render(request, 'query_word_box.html', context)


@csrf_exempt
def record_user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            expiry = 60 * 60 * 24 * 14
            request.session.set_expiry(expiry)  # three days
            cookies = {"csrftoken": django.middleware.csrf.get_token(request)}
            if not request.session.exists(request.session.session_key):
                cookies["sessionid"] = request.session.create()
            else:
                cookies["sessionid"] = request.session.session_key
            data = {'is_valid': True, "cookies": cookies,
                    "expiry": expiry, "info": "username or password is error!"}
        else:
            data = {'is_valid': False, "info": "username or password is error!"}
        return JsonResponse(data=data)


@csrf_exempt
def record_user_query(request):
    if not request.user.is_authenticated:
        data = {'is_valid': False, "info": "user need login!"}
        return JsonResponse(data=data)
    elif request.method == "POST":
        body = request.body.decode('utf-8')
        body_dict = json.loads(body)
        word = body_dict.get("word")
        desc_items = body_dict.get("desc_items")
        desc_item = None
        if desc_items:
            desc_item = "<br>".join({"<p>%s %s</p>" % (k, v) for k, v in desc_items.items()})
        session_id = body_dict.get("session_id")
        session_file = None
        if session_id:
            try:
                session_item = ImportSession.objects.get(user=request.user, used=True)
                session_file = session_item.session_files.get(id=session_id)
            except (ImportSession.DoesNotExist, ImportSessionFile.DoesNotExist):
                pass
        if not word or not word.strip():
            return JsonResponse(data={'is_valid': False, "info": "invalid"})
        else:
            try:
                translate_record = QueryTranslateRecord.objects.get(source=word.strip(), user=request.user)
                translate_record.frequency += 1
                translate_record.save()
            except QueryTranslateRecord.MultipleObjectsReturned:
                print("%s too many get!" % word.strip())
            except QueryTranslateRecord.DoesNotExist:
                translate_record = QueryTranslateRecord.objects.create(source=word.strip(),
                                                                       target=body_dict.get("info"),
                                                                       uk_phonetic=body_dict.get("uk"),
                                                                       us_phonetic=body_dict.get("us"),
                                                                       translate=desc_item,
                                                                       source_from="https://fanyi.baidu.com/",
                                                                       frequency=1,
                                                                       user=request.user,
                                                                       session_file=session_file)
                # 重点词汇
                key_words = body_dict.get("key_items")
                if key_words:
                    for key_word in key_words:
                        SentenceKeyword.objects.create(
                            query_translate=translate_record,
                            keyword=key_word["key"],
                            info=key_word["info"])
                # 双语例句
                double_samples = body_dict.get("double_samples")
                if double_samples:
                    for double_sample in double_samples:
                        SentenceRelative.objects.create(
                            query_translate=translate_record,
                            source=double_sample["source"],
                            target=double_sample["target"],
                            resource=double_sample["resource"])
            return JsonResponse(data={'is_valid': True, "info": "success"})


def delete_query_history(request):
    if request.method == "POST":
        today = datetime.date.today()
        try:
            word = request.POST.get("word")
            word_record = QueryTranslateRecord.objects.get(user=request.user, source=word, ct__year=today.year,
                                                           ct__month=today.month, ct__day=today.day)
        except QueryTranslateRecord.DoesNotExist:
            return JsonResponse(data={'is_valid': False})
        else:
            word_record.delete()
        return JsonResponse(data={'is_valid': True})


def get_translate_tag(request):
    """获取单词tag"""
    if request.method == "GET":
        word = request.GET.get("word")
        select_tag = None
        try:
            word_record = QueryTranslateRecord.objects.get(user=request.user, source=word)
            if word_record.tag:
                select_tag = word_record.tag.tag
        except (QueryTranslateRecord.DoesNotExist, QueryTranslateRecord.MultipleObjectsReturned):
            pass
        try:
            word_tags = list(QueryWordTag.objects.filter(user=request.user).all())
        except QueryWordTag.DoesNotExist:
            return JsonResponse(data={'is_valid': False, "message": "get tag failed!"})
        else:
            json_items = json.dumps(word_tags,
                                    default=lambda obj: model_to_dict(obj, fields=["tag", "color"]))
            return JsonResponse(data={'is_valid': True, "select_tag": select_tag,
                                      "data": json_items, "message": "get success!"})


@csrf_exempt
def query_translate_tag(request):
    """设置查询翻译信息tag"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=%s' % request.path)
    elif request.method == "POST":
        tag = request.POST.get("tag")
        word = request.POST.get("word")
        try:
            word_record = QueryTranslateRecord.objects.get(user=request.user, source=word)
            word_tag = QueryWordTag.objects.get(tag=tag, user=request.user)
            word_record.tag = word_tag
            word_record.save()
        except (QueryTranslateRecord.DoesNotExist, QueryWordTag.DoesNotExist):
            return JsonResponse(data={'is_valid': False, "message": "set:%s tag failed!" % word})
        else:
            return JsonResponse(data={'is_valid': True, "message": "set:%s tag success!" % word})


def transfer_translate_items(request):
    """设置查询翻译信息tag"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=%s' % request.path)
    elif request.method == "GET":
        try:
            session_item = ImportSession.objects.get(user=request.user, used=True)
            session_file = session_item.session_files.get(used=True)
        except (ImportSession.DoesNotExist, ImportSessionFile.DoesNotExist):
            return JsonResponse(data={'is_valid': False, "message": "can't found session file!"})
        else:
            word_records = QueryTranslateRecord.objects.filter(user=request.user, session_file=None)
            for word_record in word_records:
                word_record.session_file = session_file
                word_record.save()
            return JsonResponse(data={'is_valid': True, "message": "files:%d changed!" % len(word_records)})
