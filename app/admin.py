# Register your models here.
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.views.decorators.cache import never_cache

# Create your models here.
from app.dict.admins import QueryDictFileAdmin, UserQueryDictAdmin
from app.dict.models import QueryDictFile, UserQueryDict
from app.models import HighFrequencyWord, Vocabulary
from app.session.admins import ImportSessionAdmin, ExportSessionFileAdmin, SessionSentenceAdmin, SessionWordAdmin
from app.session.models import ImportSession, ImportSessionFile, SessionSentence, SessionWord
from app.user.admins import ImportRecordAdmin, QueryWordTagAdmin, QueryTranslateRecordAdmin, SentenceRelativeAdmin, \
    SentenceKeywordAdmin, UserVocabularyAdmin
from app.user.models import ImportRecord, QueryWordTag, QueryTranslateRecord, SentenceRelative, SentenceKeyword, \
    UserVocabulary


class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('word', 'uk_sound', "us_sound", "star", "high_frequency")

    # def has_module_permission(self, request, obj=None):
    #     return None


class HighFrequencyWordAdmin(admin.ModelAdmin):
    list_display = ('word', )

    # def has_module_permission(self, request, obj=None):
    #     return None


class TableList(object):
    """表格对象"""

    def __init__(self, title, headers, data):
        self.title = title
        # 首页订单交易的标题头
        self.headers = headers
        # 首页交易的订单记录
        self.data = data


class OptionItem(object):
    """附加功能"""

    def __init__(self, title, url, desc):
        self.title = title
        self.url = url
        self.desc = desc


class VocabularySites(AdminSite):
    site_url = "https://github.com/momodae"
    site_header = 'Vocabulary Analysis System'
    site_register_header = 'Vocabulary Sign up'
    site_title = 'Vocabulary System'

    @never_cache
    def index(self, request, extra_context=None):
        # 异常订单信息提示
        options = [OptionItem("Upload Data", "upload/file/", "update file(pdf/srt) to analysis!"),
                   OptionItem("Query Data", "query/file/", "query file(pdf/srt) to study!"), ]
        extra_context = {
            "title": "Data",
            "session_list": ImportSession.objects.filter(user=request.user),
            "options": TableList("Extras", headers=["option", "description"], data=options)
        }
        # 如果用户登录
        # if request.user.is_authenticated:
        # # 解除所有其他用户注册
        # for model in word_models.values():
        #     if admin_site.is_registered(model):
        #         admin_site.unregister(model)
        # # 注册vocabulary类
        # word_model = get_cache_word_model(request.user)
        # admin_opts = {
        #     "search_fields": ('word', 'simple',),
        #     "list_display": ('word', 'us_phonetic', 'star', 'description', 'high_frequency',),
        # }
        # register_model(admin_opts, word_model)
        return super().index(request, extra_context=extra_context)


admin_site = VocabularySites(name='admin')

#
# def create_model(name, fields=None, app_label='', module='app', options=None):
#     """
#     Create specified model
#     """
#
#     class Meta:
#         # Using type('Meta', ...) gives a dictproxy error during model creation
#         pass
#
#     if app_label:
#         # app_label must be set using the Meta inner class
#         setattr(Meta, 'app_label', app_label)
#
#     # Update Meta with any options that were provided
#     if options is not None:
#         for key, value in options.items():
#             setattr(Meta, key, value)
#
#     # Set up a dictionary to simulate declarations within a class
#     attrs = {'__module__': module, 'Meta': Meta}
#
#     # Add in any fields that were provided
#     if fields:
#         attrs.update(fields)
#
#     # Create the class, which automatically triggers ModelBase processing
#     return type(name, (models.Model,), attrs)
#
#
# def register_model(admin_opts, model):
#     """注册model admin对象"""
#     if not admin_site.is_registered(model):
#         class Admin(admin.ModelAdmin):
#             pass
#
#         if admin_opts is not None:
#             for key, value in admin_opts.items():
#                 setattr(Admin, key, value)
#         admin_site.register(model, Admin)
#         reload(import_module(settings.ROOT_URLCONF))
#         clear_url_caches()
#
#
# def db_table_exists(table_name):
#     return table_name in connection.introspection.table_names()
#
#
# def install(model):
#     if not db_table_exists(model._meta.db_table):
#         from django.db import connection
#         with connection.schema_editor() as schema_editor:
#             schema_editor.create_model(model)
#
#
# # 用户单词model缓存对象
# word_models = {}
#
#
# def get_cache_word_model(user):
#     model = word_models.get(user.username)
#     if not model:
#         model = _get_user_word_model(user)
#         word_models[user.username] = model
#     return model
#
#
# def _get_user_word_model(user):
#     """动态根据用户名称，建立用户单独的词库表"""
#     options = {
#         'ordering': ['ct', ],
#         'verbose_name': '%s-Vocabulary' % user.username,
#         "verbose_name_plural": '%s-Vocabulary' % user.username,
#     }
#     # Use the create_model function defined above
#     fields = get_vocabulary_fields(user)
#     fields['__str__'] = lambda self: self.word
#     model = create_model(name="%s_vocabulary" % user.username,
#                          fields=fields,
#                          app_label=AppConfig.name,
#                          options=options, )
#     install(model)
#     return model
#
#
# def get_vocabulary_fields(user):
#     fields = {
#         "word": models.CharField("单词名称", unique=True, max_length=128),
#         "uk_sound": models.FileField(verbose_name="音式发音", upload_to="resources/%s/" % user.username, null=True,
#                                      blank=True),
#         "us_sound": models.FileField(verbose_name="美式发音", upload_to="resources/%s/" % user.username, null=True,
#                                      blank=True),
#         "uk_phonetic": models.CharField("英式音标", max_length=32, null=True, blank=True),
#         "us_phonetic": models.CharField("美式音标", max_length=32, null=True, blank=True),
#         "picture": models.ImageField("联想图片", upload_to="picture/%s/" % user.username, null=True, blank=True),
#         "star": models.CharField("单词星级", max_length=12),
#         "description": models.CharField("英文解释", max_length=256),
#         "description_html": models.TextField("所有解释"),
#         "own": models.BooleanField("是否学会", default=True),
#         "high_frequency": models.BooleanField("高频词", default=False),
#         "ct": models.DateTimeField("记录时间", auto_now_add=True),
#     }
#     return fields

# dict
admin_site.register(QueryDictFile, QueryDictFileAdmin)
admin_site.register(UserQueryDict, UserQueryDictAdmin)
# session
admin_site.register(ImportSession, ImportSessionAdmin)
admin_site.register(ImportSessionFile, ExportSessionFileAdmin)
admin_site.register(SessionSentence, SessionSentenceAdmin)
admin_site.register(SessionWord, SessionWordAdmin)
# user
admin_site.register(UserVocabulary, UserVocabularyAdmin)
admin_site.register(ImportRecord, ImportRecordAdmin)
admin_site.register(QueryWordTag, QueryWordTagAdmin)
admin_site.register(QueryTranslateRecord, QueryTranslateRecordAdmin)
admin_site.register(SentenceRelative, SentenceRelativeAdmin)
admin_site.register(SentenceKeyword, SentenceKeywordAdmin)
# main
admin_site.register(HighFrequencyWord, HighFrequencyWordAdmin)
admin_site.register(Vocabulary, VocabularyAdmin)
