from django.contrib import admin
from django import forms

from app.models import Vocabulary
from app.user.models import SentenceRelative, SentenceKeyword, ImportRecord, UserVocabulary


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


class SentenceRelativeInline(admin.StackedInline):
    model = SentenceRelative
    extra = 0


class SentenceKeywordInline(admin.StackedInline):
    model = SentenceKeyword
    extra = 0


class QueryTranslateRecordAdmin(admin.ModelAdmin):
    list_display = ["source", "target"]

    # readonly_fields = ["ct"]
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
                kwargs['exclude'] = ['source_from', "user"]
                self.inlines = (SentenceRelativeInline, SentenceKeywordInline)
            else:
                self.inlines = ()
                kwargs['exclude'] = ['source_from', 'target', "uk_phonetic", "us_phonetic", "translate", "user"]
        return super(QueryTranslateRecordAdmin, self).get_form(request, obj, **kwargs)


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
