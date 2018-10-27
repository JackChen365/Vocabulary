from django.conf.urls import url

from app.session.views import UploadSession, SearchSentence, query_session_word, query_session_list, \
    query_session_sentence, SessionDetailView, study_session_file, remove_all_session

urlpatterns = [
    url('^upload/file/$', UploadSession.as_view(), name="session-upload-file"),
    url('^search/sentence/$', SearchSentence.as_view(), name="session-search-sentence"),
    url('^query/list$', query_session_list, name="session-query-list"),
    url('^query/word/$', query_session_word, name="session-query-word"),
    url('^query/sentence/word/list$', query_session_sentence, name="session-query-sentence"),
    url('^query/detail/(\d+)/(\d+)/$', SessionDetailView.as_view(), name="session-query-detail"),
    url('^study/file/$', study_session_file, name="study-session-file"),
    url('^remove/all/$', remove_all_session, name="remove-all_session"),
]
