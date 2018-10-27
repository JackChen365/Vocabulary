from django.conf.urls import url

from app.user.views import RegisterView, QueryFile, UploadFile, get_translate_tag, query_word_box, query_translate_tag, \
    record_user_query, delete_query_history, record_user_login, transfer_translate_items

urlpatterns = [
    url('^register/$', RegisterView.as_view(), name="register"),
    url('^login/$', record_user_login, name="user-login"),
    url('^delete/query/$', delete_query_history, name="user-delete-query"),
    url('^word/record/$', record_user_query, name="user-word-record"),
    url('^query/word/box/$', query_word_box, name="user-query-word-box"),
    url('^query/file/$', QueryFile.as_view(), name="user-query-file"),
    url('^upload/file/$', UploadFile.as_view(), name="user-upload-file"),
    url('^get/translate/tag/$', get_translate_tag, name="get-translate-tag"),
    url('^query/translate/tag/$', query_translate_tag, name="query-translate-tag"),
    url('^transfer/translate/items/$', transfer_translate_items, name="transfer-translate-items"),
]