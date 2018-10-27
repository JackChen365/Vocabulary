from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from app.user.models import QueryWordTag


class ImportSessionAdmin(admin.ModelAdmin):
    list_display = ('export_id', 'title', "finished")

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(ImportSessionAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.user == request.user


class ExportSessionFileAdmin(admin.ModelAdmin):
    list_display = ('file',)

    def has_module_permission(self, request, obj=None):
        return None


class SessionSentenceAdmin(admin.ModelAdmin):
    list_display = ('sentence', "note",)
    search_fields = ("sentence", "sentence_prototype")
    readonly_fields = ("ct",)
    fieldsets = (
        ("Session", {'fields': ('session', 'session_file')}),
        ("Sentence", {'fields': (
            'sentence', 'sentence_prototype', 'note')}),
        ("Other", {'fields': ('time', "ct")}),
    )

    def has_module_permission(self, request, obj=None):
        return None


class SessionWordAdmin(admin.ModelAdmin):
    list_display = ('word', "frequency",)

    def has_module_permission(self, request, obj=None):
        return None


def initial_user_query_tag(user):
    # normal 正常
    QueryWordTag.objects.create(
        tag="Normal",
        user=user,
        style="<span style=\"font-weight:bold;padding:4px;\">%s</span>")
    # deprecated，不推荐学
    QueryWordTag.objects.create(
        tag="Deprecated",
        color="#8B4513",
        user=user,
        font_color="#FFFFFF",
        style="<span style=\"font-weight:bold;TEXT-DECORATION:line-through;color:black;padding:4px;\">%s</span>")
    # sound practice 发音
    QueryWordTag.objects.create(
        tag="SoundPractice",
        color="#1E90FF",
        user=user,
        font_color="#FFFFFF",
        style="<span style=\"font-weight:bold;color:green;padding:4px;\">%s</span>")
    # high frequency
    QueryWordTag.objects.create(
        tag="HighFrequency",
        color="#98FB98",
        user=user,
        font_color="#FFFFFF",
        style="<span style=\"font-weight:bold;color:red;padding:4px;\">%s</span>")


def create_user_profile(sender, instance, created, **kwargs):
    """创建用户时初始化操作"""
    if created:
        initial_user_query_tag(instance)


post_save.connect(create_user_profile, sender=User, dispatch_uid="create_user_profile")
