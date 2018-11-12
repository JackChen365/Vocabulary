import hashlib
import hashlib
import json
import re

from django.core.files import File
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import render, redirect
# Create your views here.
from django.template import loader
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from app.admin import admin_site, TableList
from app.analysis.analyzer import Analyzer, QueryItem
from app.models import HighFrequencyWord, Vocabulary
from app.session.forms import ExportSessionForm
from app.session.models import ImportSession, ImportSessionFile, SessionSentence, SessionWord
from app.tasks import session_task
from app.user.models import UserVocabulary
from app.views import remote_tmp


class UploadSession(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/admin/login/?next=%s' % request.path)
        else:
            sessions = ImportSession.objects.filter(user=request.user).order_by("-ct")
            session_table = TableList(title=None, headers=["Title", "Finished", "Time", "Other"], data=sessions)
            template = loader.get_template('session/upload_file.html')
            context = {
                "has_permission": True,
                "title": "Select session",
                "session_table": session_table,
                "site_url": admin_site.site_url,
                "site_title": admin_site.site_title,
                "site_header": admin_site.site_header,
            }
            return HttpResponse(template.render(context, request))

    def post(self, request):
        form = ExportSessionForm(request.POST, request.FILES)
        if form.is_valid():
            title = request.POST["title"]
            files = request.POST["files"]
            timestamp = request.POST["timestamp"]
            hash_lib = hashlib.md5()
            hash_lib.update(files.encode("utf-8") + timestamp.encode("utf-8"))
            export_id = hash_lib.hexdigest()
            print("export_id:%s" % export_id)
            session, _ = ImportSession.objects.get_or_create(user=request.user,
                                                             title=title, export_id=export_id)
            if not ImportSession.objects.filter(used=True).exists():
                session.used = True
                session.save()
            upload_file = form.cleaned_data["file"]
            # 保存文件
            session_file = ImportSessionFile.objects.create(name=upload_file.name, session=session)
            session_file.file.save(upload_file.name, File(upload_file))

            # 判断文件是否上传完成
            file_length = int(request.POST["file-length"])
            data = {'is_valid': True}
            if file_length == session.session_files.count():
                print("%s系列 文件上传:%s 成功 总个数:%s 个数：%d" %
                      (title, upload_file.name, file_length, session.session_files.count()))
                # 加入异步执行队列
                session_task.delay(export_id)
                # session_task(export_id)
                data["is_finished"] = True
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


class SessionDetailView(View):
    """展示Session详情界面"""

    class FileItem(object):
        def __init__(self, session_id, session_file):
            self.id = session_file.id
            self.name = session_file.name
            self.url = "/session/query/detail/%s/%s/" % (session_id, session_file.id)

    def get(self, request, session_id, file_id):
        if request.method == 'GET':
            # 清理临时目录
            remote_tmp()
            session = ImportSession.objects.get(id=session_id)
            session_files = session.session_files.all()
            file_id = file_id if '0' != file_id else session_files[0].id
            session_file = session_files.get(id=file_id)
            session_sentences = session_file.session_file_sentences.all()
            file_items = []
            for session_file in session_files:
                file_items.append(SessionDetailView.FileItem(session_id, session_file))
            # 首字母大写格式替换
            pattern = re.compile(r'^(\w+)')
            for sentence_item in session_sentences:
                sentence_item.sentence = pattern.sub(r'<em><strong>\1</strong></em>', sentence_item.sentence)
            context = {
                "session_id": session_id,
                "file_id": file_id,
                "session_files": file_items,
                "session_sentences": session_sentences,
                "has_permission": True,
                "title": "Session Detail",
                "site_title": admin_site.site_title,
                "site_header": admin_site.site_header,
                "request_path": "/session/query/detail/%s/%s/" % (session_id, file_id),
            }
            return render(request, 'session/query_file_detail.html', context)

    def post(self, request):
        pass


class SearchSentence(View):
    """搜索Session句子"""

    def get(self, request):
        session_id = request.GET.get("id")
        context = {
            "has_permission": True,
            "session_id": session_id,
            "title": "Search Sentence",
            "site_title": admin_site.site_title,
            "site_header": admin_site.site_header,
        }
        return render(request, 'session/query_sentence.html', context)

    def post(self, request):
        if "POST" == request.method:
            # 清理临时资源目录
            remote_tmp()
            session_id = request.POST.get("id")
            word = request.POST.get("word")
            try:
                session_item = ImportSession.objects.get(id=session_id)
            except ImportSession.DoesNotExist:
                return HttpResponse("<h3>No Result!</h3>")
            sentence_items = session_item.session_sentences.filter(
                Q(sentence__icontains=word) | Q(sentence_prototype__icontains=word))
            first_pattern = re.compile(r'^(\w+)')
            word_pattern = re.compile(r'(%s)' % word, re.IGNORECASE)
            for sentence_item in sentence_items:
                # 首字母高亮
                sentence_item.sentence = first_pattern.sub(r'<em><strong>\1</strong></em>', sentence_item.sentence)
                # 将搜索词高亮
                sentence_item.sentence = word_pattern.sub(r'<font color="red"><strong>\1</strong></font>',
                                                          sentence_item.sentence)
            context = {
                "has_permission": True,
                "title": "Search Sentence",
                "session_sentences": sentence_items,
                "site_title": admin_site.site_title,
                "site_header": admin_site.site_header,
            }
            return render(request, 'session/query_sentence_list.html', context)


def query_session_sentence(request):
    """查询句子的单词信息"""
    if request.method == 'GET':
        session_id = request.GET.get("id")
        file_id = request.GET.get("file_id")
        index = request.GET.get("index")
        if not session_id or not index:
            return HttpResponse("<h3>%s:Search not result!</h3>" % session_id)
        else:
            # 查词是否为用户词库
            try:
                session_item = ImportSession.objects.get(id=session_id)
                session_file = session_item.session_files.get(id=file_id)
                sentence_item = session_file.session_file_sentences.get(index=index)
                session_word_items = session_item.session_words.all()
            except (ImportSession.DoesNotExist, ImportSessionFile.DoesNotExist, SessionSentence.DoesNotExist):
                return HttpResponse("<h3>Session Sentence:%s can't found!</h3>" % session_id)
            sentence_words = sentence_item.sentence_prototype.split(" ")
            result_items = []
            for word_item in sentence_words:
                try:
                    vocabulary = Vocabulary.objects.get(word=word_item)
                    session_word_item = session_word_items.get(word=word_item)
                except (Vocabulary.DoesNotExist, SessionWord.DoesNotExist):
                    pass
                else:
                    vocabulary.is_user_word = UserVocabulary.objects.filter(word=word_item).exists()
                    vocabulary.frequency = session_word_item.frequency
                    result_items.append(vocabulary)
            # 使用百词斩在线查询中文释义
            context = {
                "sentence_note": sentence_item.note,
                "sentence_words": result_items,
            }
            return render(request, 'session/query_sentence_detail.html', context)


def query_session_word(request):
    """查询序列内单词信息"""
    if request.method == 'GET':
        session_id = request.GET.get("id")
        word = request.GET.get("word")
        if not session_id or not word:
            return HttpResponse("<h1>%s:Search not result!</h1>" % word)
        else:
            word = Analyzer.lemmatize(word)
            if not word:
                return HttpResponse("<h1>%s:Search not result!</h1>" % word)
            else:
                try:
                    word_item = Vocabulary.objects.get(word=word.name)
                except Vocabulary.DoesNotExist:
                    return HttpResponse("<h1>%s:Search not result!</h1>" % word)
                else:
                    try:
                        session_item = ImportSession.objects.get(id=session_id)
                        session_word = session_item.session_words.get(word=word_item.word)
                    except (ImportSession.DoesNotExist, SessionWord.DoesNotExist):
                        print("session:%s can't found!" % session_id)
                    else:
                        # 记录词频
                        word_item.frequency = session_word.frequency
                        word_item.sentence = session_item.session_sentences.filter(
                            sentence__icontains=word_item.word).all()[:3]
                    # 查词是否为用户词库
                    try:
                        word_item.is_user_word = UserVocabulary.objects.filter(word=word_item.word).exists()
                    except HighFrequencyWord.DoesNotExist:
                        print("high_frequency:%s can't found!" % session_id)
                    # 使用百词斩在线查询中文释义
                    context = {
                        "item": word_item,
                    }
                    return render(request, 'query_word_box.html', context)


def query_session_list(request):
    """查询系列"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=%s' % request.path)
    elif request.method == "GET":
        try:
            session_item = ImportSession.objects.get(user=request.user, used=True)
        except ImportSession.DoesNotExist:
            return JsonResponse(data={'is_valid': False, "message": "user has no study session!"})
        else:
            session_file_items = list(session_item.session_files.all())
            json_items = json.dumps(session_file_items,
                                    default=lambda obj: model_to_dict(obj, fields=["id", "name", "used"]))
            return JsonResponse(data={'is_valid': True, "session_files": json_items})


@csrf_exempt
def study_session_file(request):
    """查询系列"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=%s' % request.path)
    elif request.method == "POST":
        file_id = request.POST.get("file_id")
        try:
            session_item = ImportSession.objects.get(user=request.user, used=True)
        except ImportSession.DoesNotExist:
            return JsonResponse(data={'is_valid': False, "message": "Session not existed!"})
        else:
            for session_file in session_item.session_files.filter(used=True):
                session_file.used = False
                session_file.save()
            try:
                session_file_item = session_item.session_files.get(id=file_id)
                session_file_item.used = True
                session_file_item.save()
            except ImportSessionFile.DoesNotExist:
                return JsonResponse(data={'is_valid': False, "message": "SessionFile not existed!"})
            else:
                return JsonResponse(data={'is_valid': True, "data": session_file_item.id})


def remove_all_session(request):
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=%s' % request.path)
    elif request.method == "GET":
        ImportSession.objects.filter(user=request.user).all().delete()
        return HttpResponse("ok!")


def study_session_item(request):
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=%s' % request.path)
    elif request.method == "POST":
        session_id = request.POST.get("id")
        try:
            session_item = ImportSession.objects.get(user=request.user, used=True)
            session_item.used=False
            session_item.save()
            new_session_item = ImportSession.objects.get(user=request.user, id=session_id)
            new_session_item.used = True
            new_session_item.save()
        except ImportSession.DoesNotExist:
            return JsonResponse(data={'is_valid': False, "message": "Session not existed!"})
        else:
            return JsonResponse(data={'is_valid': True})
