import os
from datetime import datetime

from django.contrib import admin
from django import forms
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse

from app.models import Vocabulary
from app.user.models import SentenceRelative, SentenceKeyword, ImportRecord, UserVocabulary, QueryWordTag
from vocabulary.settings import MEDIA_ROOT
from app.user.models import SentenceRelative, SentenceKeyword, ImportRecord, UserVocabulary, QueryWordTag


class UserVocabularyAdmin(admin.ModelAdmin):
    list_display = ('word', "query_count")
    fields = ["word"]
    readonly_fields = ["word"]

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(UserVocabularyAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.user == request.user


class ExportRecordForm(forms.ModelForm):
    class Meta:
        fields = [
            "export_file",
            "unknown_file",
            "finished",
        ]
        model = ImportRecord


class ImportRecordAdmin(admin.ModelAdmin):
    list_display = ('export_file', "finished")
    readonly_fields = ["finished"]
    form = ExportRecordForm

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(ImportRecordAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.user == request.user


class SentenceRelativeInlineForm(forms.ModelForm):
    readonly_fields = ["source", "target"]
    exclude = ["source", "target"]


class SentenceRelativeInline(admin.StackedInline):
    model = SentenceRelative
    form = SentenceRelativeInlineForm
    extra = 0

    # def get_formset(self, request, obj=None, **kwargs):
    #     formset= super().get_formset(request, obj, **kwargs)
    #     formset.form.bash_fields[""]


class SentenceKeywordInlineForm(forms.ModelForm):
    readonly_fields = ["key", "info"]
    exclude = ["key", "info"]


class SentenceKeywordInline(admin.StackedInline):
    model = SentenceKeyword
    form = SentenceKeywordInlineForm
    extra = 0


class RecordTagFilter(admin.SimpleListFilter):
    """为订单增加月份过滤器"""
    title = u'Tag Filter'
    parameter_name = 'tag_filter'

    def lookups(self, request, model_admin):
        word_tags = QueryWordTag.objects.filter(user=request.user)
        return ((tag.tag, tag) for tag in word_tags)

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        else:
            today = datetime.now().date()
            word_tag = QueryWordTag.objects.get(user=request.user, tag=self.value())
            return queryset.filter(Q(tag=word_tag) & Q(ct__date=today))


class RecordDateFilter(admin.SimpleListFilter):
    title = u'Date Filter'
    parameter_name = 'date_filter'

    def lookups(self, request, model_admin):
        today = datetime.now().date()
        return (today.strftime("%Y-%m-%d"), today),

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        else:
            today = datetime.now().date()
            return queryset.filter(ct__date=today)


class QueryTranslateRecordAdmin(admin.ModelAdmin):
    list_display = ["source", "target"]
    actions = ['export_sentence']
    # 列表过滤器
    list_filter = (RecordTagFilter, RecordDateFilter)

    readonly_fields = ["target", "uk_phonetic", "us_phonetic", "translate", "session_file", "tag", "ct", "frequency"]

    # inlines = (SentenceRelativeInline, SentenceKeywordInline)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(QueryTranslateRecordAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.user == request.user

    def get_form(self, request, obj=None, **kwargs):
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj:
            if "inner" != obj.source_from:
                kwargs['exclude'] = ["target", "uk_phonetic", "us_phonetic", "translate", 'source_from', "user",
                                     "session_file", "frequency", "tag", "ct"]
                self.inlines = (SentenceRelativeInline, SentenceKeywordInline)
            else:
                self.inlines = ()
                kwargs['exclude'] = ["target", "uk_phonetic", "us_phonetic", "translate", 'source_from', 'target',
                                     "uk_phonetic", "us_phonetic", "translate", "user",
                                     "session_file", "frequency", "tag", "ct"]
        form = super(QueryTranslateRecordAdmin, self).get_form(request, obj, **kwargs)
        # form.base_fields["tag"].queryset = QueryWordTag.objects.filter(user=request.user)
        return form

    def export_sentence(self, request, queryset):
        if 0 == len(queryset):
            messages.error(request, 'nothing need to do!.')
        else:
            content = os.linesep.join([item.source for item in queryset])
            response = HttpResponse(content)
            response['Content-Disposition'] = 'attachment; filename="%s.txt"' % datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            response['Content-Type'] = 'application/txt'
            return response

    export_sentence.short_description = 'Export Selected Record'
    export_sentence.short_description = "Export Record"


class SentenceRelativeAdmin(admin.ModelAdmin):
    list_display = ('source', "target")

    def has_module_permission(self, request, obj=None):
        return None


class SentenceKeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', "info")

    def has_module_permission(self, request, obj=None):
        return None


class QueryWordTagAdmin(admin.ModelAdmin):
    list_display = ('tag', "style")

    # def has_module_permission(self, request, obj=None):
    #     return None
    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(QueryWordTagAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.user == request.user
