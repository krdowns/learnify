from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('courses', views.courses, name='courses'),
    path('courses/<int:pk>', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/add_video', views.add_video, name='add_video'),
    path('courses/<int:pk>/edit_course', views.edit_course, name='edit_course'),
    path('courses/create', views.course_create, name='course_create'),
    path('profile/<slug:username>', views.profile, name='profile'),
    path('user_login', views.user_login, name='user_login'),
    path('logout', views.user_logout, name='logout'),
    path('special', views.special, name='special'),
    path('charge/<int:pk>', views.checkout, name='charge')
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


