import datetime

from django.contrib import admin


class QueryDictFileAdmin(admin.ModelAdmin):
    list_display = ('mdx_file', "mdx_md5")

    def has_module_permission(self, request, obj=None):
        return None


class UserQueryDictAdmin(admin.ModelAdmin):
    list_display = ["dict_name", "dict_file", "position"]
    readonly_fields = ["up"]

    def save_model(self, request, obj, form, change):
        obj.up = datetime.datetime.now()
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(UserQueryDictAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.user == request.user
