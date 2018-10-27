import hashlib
import json
import os
import re
import datetime

from django.core.files import File
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.views import View

from app.admin import admin_site
from app.dict.models import UserQueryDict, QueryDictFile
from app.dict.query.mdict_query import IndexBuilder
from app.session.models import ImportSession, ImportSessionFile
from app.user.models import QueryWordTag, QueryTranslateRecord
from app.views import remote_tmp
from vocabulary.settings import MEDIA_ROOT, MEDIA_URL


class QueryWordView(View):
    """查询单词界面"""

    resource_pattern = re.compile(
        r"(?:href|src)=\"(?P<link>(?:sound://)?(?P<file>[^\"\.]+\.(?:wav|gif|png|jpg|mp3|css|js)))\"")
    entry_pattern = re.compile(r"href=\"(?P<link>entry://(?P<word>[^\"]+))\"")

    def process_link_file(self, index_build, word, doc_str):
        """process all html source file link"""
        start = 0
        output = ""
        find_iter = self.resource_pattern.finditer(doc_str)
        for find_item in find_iter:
            file_link = find_item.group("file")
            file_span = find_item.span("link")
            dict_title = index_build._title.replace(" ", "_")
            dict_path = os.path.join(MEDIA_ROOT, "dict", "resource", dict_title)
            if not os.path.exists(dict_path):
                os.makedirs(dict_path)
            file_path = os.path.join(dict_path, file_link)
            if not os.path.exists(file_path):
                resource_files = index_build.mdd_lookup("\\" + file_link.replace("/", "\\"))
                if 0 == len(resource_files):
                    print("\t%s:%s查询失败!" % (word, file_link))
                else:
                    # 因为部分资源为img/xx.jpg 所有需要取具体名称
                    (file_base_dic, file_name) = os.path.split(file_path)
                    if not os.path.exists(file_base_dic):
                        os.makedirs(file_base_dic)
                    if resource_files:
                        with open(file_path, 'wb') as f:
                            f.write(resource_files[0])
            # 添加文件前信息
            output += doc_str[start:file_span[0]]
            output += os.path.join(os.path.join(MEDIA_URL, "dict", "resource", dict_title), file_link) + "\""
            start = file_span[1] + 1
        output += doc_str[start:]
        return output

    def process_link_entry(self, doc_str):
        """process all html source entry link"""
        start = 0
        output = str()
        entry_iter = self.entry_pattern.finditer(doc_str)
        for entry_item in entry_iter:
            entry_path = entry_item.group("word")
            entry_span = entry_item.span("link")
            # 添加文件前信息
            output += doc_str[start:entry_span[0]]
            output += "?word=" + entry_path + "\""
            start = entry_span[1] + 1
        output += doc_str[start:]
        return output

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/admin/login/?next=%s' % request.path)
        elif request.method == 'GET':
            # 清理临时目录
            remote_tmp()
            doc_items = {}
            word_record = None
            session_files = []
            session_file = None
            today = datetime.date.today()
            word = request.GET.get("word")
            # 用户session
            try:
                import_session = ImportSession.objects.get(user=request.user, used=True)
                session_files = list(import_session.session_files.all())
                session_file = import_session.session_files.get(used=True)
            except (ImportSession.DoesNotExist, ImportSessionFile.DoesNotExist):
                pass
            if word and word.strip():
                word = word.strip().lower()
                user_dict_items = UserQueryDict.objects.filter(user=request.user).order_by("position")
                for dict_item in user_dict_items:
                    index_build = IndexBuilder(dict_item.dict_file.mdx_file.path)
                    items = index_build.mdx_lookup(word)
                    doc_items.setdefault(dict_item.dict_name, [])
                    for item in items:
                        output = self.process_link_file(index_build, word, item)
                        output = self.process_link_entry(output)
                        doc_items[dict_item.dict_name].append(output)
                # 保存查询记录
                try:
                    word_record = QueryTranslateRecord.objects.get(user=request.user, source=word, ct__year=today.year,
                                                                   ct__month=today.month, ct__day=today.day)
                    word_record.frequency += 1
                    word_record.ct = datetime.datetime.now(tz=datetime.timezone.utc)
                    word_record.save()
                except QueryTranslateRecord.DoesNotExist:
                    QueryTranslateRecord.objects.create(source=word,
                                                        frequency=1,
                                                        session_file=session_file,
                                                        user=request.user)
            query_word_set = QueryTranslateRecord.objects.filter(user=request.user, source_from="inner",
                                                                 ct__year=today.year, ct__month=today.month,
                                                                 ct__day=today.day)
            user_dict_items = list(UserQueryDict.objects.filter(user=request.user).order_by("id"))
            for index, user_dict in enumerate(user_dict_items):
                user_dict.id = index
            user_dict_items.sort(key=lambda i: i.position)
            context = {
                "doc_items": doc_items,
                "word_record": word_record,
                "session_files": session_files,
                "dict_items": user_dict_items,
                "query_count": query_word_set.count(),
                "tag_group": QueryWordTag.objects.filter(user=request.user),
                "query_items": query_word_set.order_by('-ct'),
            }
            return render(request, 'dict/query_word.html', context)

    def post(self, request):
        pass


class UploadDictView(View):
    """上传字典信息"""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/admin/login/?next=%s' % request.path)
        elif request.method == 'GET':
            template = loader.get_template('dict/upload_dict_file.html')
            context = {
                "title": "Select dict file Form",
                "sub_title": "First file is mdx and second is mdd",
                "has_permission": True,
                "site_url": admin_site.site_url,
                "site_title": admin_site.site_title,
                "site_header": admin_site.site_header,
            }
            return HttpResponse(template.render(context, request))

    def post(self, request):
        if request.method == 'POST':  # 获取对象
            if 0 == len(request.FILES):
                return HttpResponse("没有上传任务文件！")
            else:
                mdx_file = request.FILES.get("mdx_file")
                if mdx_file is None:
                    return HttpResponse("上传失败！")
                else:
                    tmp_path = os.path.join(MEDIA_ROOT, "tmp")
                    if not os.path.exists(tmp_path):
                        os.makedirs(tmp_path)
                    target_path = os.path.join(tmp_path, mdx_file.name)
                    target_file = open(target_path, 'wb+')  # 打开特定的文件进行二进制的写操作
                    md5 = hashlib.md5()
                    for chunk in mdx_file.chunks():  # 分块写入文件
                        target_file.write(chunk)
                        md5.update(chunk)
                    target_file.close()
                    mdx_digest = md5.digest()
                    try:
                        query_dict_file = QueryDictFile.objects.get(mdx_md5=mdx_digest)
                    except QueryDictFile.DoesNotExist:
                        query_dict_file = QueryDictFile.objects.create(mdx_md5=mdx_digest)
                        query_dict_file.mdx_file.save(mdx_file.name, File(open(target_path, 'rb')))
                        # set up the dict file
                        IndexBuilder(query_dict_file.mdx_file.path, force_rebuild=True)
                        mdd_file = request.FILES.get("mdd_file")
                        if mdd_file is not None:
                            query_dict_file.mdd_file.save(mdd_file.name, File(mdd_file))
                    # 保存用户词典信息
                    UserQueryDict.objects.create(user=request.user,
                                                 dict_name=mdx_file.name,
                                                 dict_file=query_dict_file,
                                                 position=UserQueryDict.objects.filter(user=request.user).count(),
                                                 up=datetime.datetime.now(tz=datetime.timezone.utc), )
                    data = {'is_valid': True, "data": "数据提交成功！"}
                    return JsonResponse(data=data)


def dict_sort(request):
    """字典排序"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=%s' % request.path)
    elif request.method == "POST":
        position_str = request.POST.get("position")
        position_items = [int(item) for item in json.loads(position_str)]
        # 3,1,2
        user_dict_items = list(UserQueryDict.objects.filter(user=request.user).order_by("id"))
        for index, position in enumerate(position_items):
            dict_item = user_dict_items[position]
            dict_item.position = index
            dict_item.save()
        print(["%d %d" % (item.id, item.position) for item in
               UserQueryDict.objects.filter(user=request.user).order_by("position")])
        return HttpResponse("ok!")
