from django.urls import path

# 从当前路径的views下导入所有函数
from .views import *


# 用户模块下的请求处理url
urlpatterns = [
    path('', index),
    path('login/', login),
    path('logout/', logout),
    path('register/', register),
    path('admin-users/', admin_users),
    path('<uuid:user_id>/', edit_user),
    path('meetings/', meeting),
    path('send_email/', send_email),
    path('poster_manager/', poster_manager),
    path('add_poster/', add_poster),
    path('random_poster/', random_poster),
    path('delete_poster/<uuid:poster_id>/', delete_poster),
    path('edit_poster/<uuid:poster_id>/', edit_poster),
    path('poster/<uuid:poster_id>/vote/', vote),
    path('poster/<uuid:poster_id>/score/', score),
    path('luck_draw/', luck_draw),
    path('luck_member/', luck_member),
    path('role-number/', role_number),
    path('poster_set/', poster_set),
    path('grades/', list_grade),
    path('add-grade/', add_grade),
    path('del-grade/<uuid:grade_id>/', del_grade),
    path('edit-grade/<uuid:grade_id>/', edit_grade),
    path('majors/', get_majors),
]
