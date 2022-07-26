import random

from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.core import mail
from django.conf import settings
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as d_logout, authenticate, login as d_login
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from faker import Faker

from .models import User, Meeting, Poster, Luck, Role, Grade
from .utils import random_string


def index(request):
    """
    将 / 请求跳转到用户列表页面处理函数，
    request参数为请求对象
    """
    url, index_html = '', ''
    user = request.user
    if user.is_anonymous or user.role == 'visitors':
        index_html = 'index/visitors.html'
    elif user.role == 'lucky_draw':
        index_html = 'index/lucky_drawa.html'
    elif user.role == 'judges':
        url = '/users/poster_manager/'
    elif user.role == 'senior_judges':
        url = '/users/poster_manager/'
    elif user.role == 'poster_manager':
        url = '/users/poster_manager/'
    else:
        url = '/users/admin-users/'
    if url:
        return HttpResponseRedirect(url)
    else:
        return render(request, index_html)


def login(request):
    """
    登录函数请求处理函数，
    request参数为请求对象
    """
    data = {
        'title': 'login',
        'hide_nav': True,
        'nav_title': '登录'
    }
    if request.method.lower() == 'get':
        # 当请求方式为get请求时，直接渲染登录页面
        return render(request, 'login_register.html', context=data)
    else:
        # 当请求方式为非get时，获取前端传入的用户名和密码
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not all([username, password]):
            data.update({
                'msg': 'The user name and password cannot be empty'
            })
            return JsonResponse(data)
        # user模型是继承django自有的user模型，所以可以使用django的认证方法
        user = authenticate(username=username, password=password)
        if user:
            # 如果用户认证通过，我们使用django内置的登录函数保存登录状态(session)
            d_login(request, user)
        else:
            data.update({
                'msg': 'The user name or password is incorrect'
            })
        return JsonResponse(data)


def register(request):
    """
    注册函数请求处理函数，
    request参数为请求对象
    """
    data = {
        'title': 'register',
        'hide_nav': True,
    }
    if request.method.lower() == 'get':
        # 当请求方式为get请求时，直接渲染注册页面
        return render(request, 'login_register.html', context=data)
    else:
        # 当请求方式为非get时，获取前端传入的用户名和密码
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not all([username, password]):
            data.update({
                'msg': 'The user name and password cannot be empty'
            })
            return JsonResponse(data)
        user_exist = User.objects.filter(username=username).first()
        if user_exist:
            data.update({
                'msg': 'This user name already exists'
            })
        else:
            User.objects.create(username=username, password=make_password(password))
        return JsonResponse(data)


def logout(request):
    """
    退出登录函数请求处理函数，
    request参数为请求对象
    """
    if request.method.lower() == 'get':
        d_logout(request)
    return HttpResponseRedirect('/users/login/')


@login_required
def admin_users(request):
    """
    获取所有用户处理函数,
    request参数为请求对象
    """
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    # 根据url获取传递过来的用户名称  例子：url--> http://127.0.0.1:9000/users/admin-users/?nickname=王明
    # search_username的值就是王明，如果未传递参数，则nickname为空字符串''
    search_username = request.GET.get('nickname', '')
    if search_username:
        # 如果获取到参数呢城，我们就从数据库中查找 昵称中【包含】参数nickname的用户，模糊匹配
        # 搜索 王 --> 结果是 名字中包含王字的用户都会搜索出来
        query = User.objects.filter(nickname__contains=search_username).order_by('id')
        # 将用户信息数据更新到data字典中，传到前端
    else:
        query = User.objects.all().order_by('id')

    # 人员数据分页，默认每页5个
    paginator = Paginator(query, 5)
    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        page = paginator.page(1)

    data = {'users': [user.to_json() for user in page]}

    # 页面前端搜索框中搜索的关键字
    data.update({
        'search_username': search_username,
        'page': page, 'paginator': paginator
    })
    return render(request, 'index/admin.html', context=data)


def poster_manager(request):
    """
    根据角色的不同，展示不同功能的海报列表页面
    """
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    user = request.user
    data = {'role': 'visitors'}
    query = Poster.objects.all().order_by('id')
    if user.is_authenticated:
        # 用户角色是评委
        if user.role == User.ROLE_CHOICE[2][0]:
            data['role'] = user.role
            query = Poster.objects.filter(grade=user.grade).order_by('id')
        # 用户角色是高级评委
        elif user.role == User.ROLE_CHOICE[3][0]:
            data['role'] = user.role
            # 过滤出同学院的作品
            if user.grade:
                grade = Grade.objects.filter(id=user.grade).first()
                grades = [str(i.id) for i in Grade.objects.filter(college=grade.college)]
                query_set = []
                # 每个专业只显示相应数量的获胜海报
                for g in grades:
                    query_set1 = Poster.objects.exclude(one_score_number=0)
                    son_poster = query_set1.filter(grade=g).order_by('one_score_avg')
                    for s in son_poster:
                        query_set.append(s)
                # 这里过滤出优秀作品
                query = query_set
            else:
                query = []
        # 用户角色是海报管理者
        elif user.role == User.ROLE_CHOICE[4][0]:
            data['role'] = user.role
            query = Poster.objects.filter(user=user).order_by('id')
    # 这种情况是用户未登录
    token = request.GET.get('token')
    if token and cache.get(token):
        user = User.objects.filter(email=cache.get(token)).first()
        action = request.GET.get('action')
        d_login(request, user)
        query = Poster.objects.all().order_by('id')
        if action == 'vote':
            message = 'Vote success，click<a href="/users/luck_draw/">here</a>to draw'
            messages.add_message(request, messages.SUCCESS, message)
        elif action == 'luck':
            message = '[%s] Draw a successful' % user.username
            messages.add_message(request, messages.SUCCESS, message)
        elif action == 'already_luck':
            message = '[%s] Have already been drawn' % user.username
            messages.add_message(request, messages.ERROR, message)
        else:
            message = 'The default user name is the email address, and the default password is 123456'
            messages.add_message(request, messages.SUCCESS, message)

    # 海报数据分页，默认8个
    paginator = Paginator(query, 8)
    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        page = paginator.page(1)

    data.update({
        'page': page, 'paginator': paginator
    })
    return render(request, 'index/poster_manager.html', context=data)


def add_poster(request):
    """
    在线添加海报
    """
    if request.method == 'POST':
        user = request.user
        if user and user.grade:
            title = request.POST.get('title')
            summary = request.POST.get('summary')
            image = request.FILES.get('image')
            if not image:
                messages.add_message(request, messages.ERROR, 'Images cannot be empty')
                return render(request, 'add_poster.html')
            # 创建海报数据到数据库，save之后才能入库
            p = Poster(
                title=title, summary=summary, image_path=image, user=request.user,
                grade=user.grade
            )
            p.save()
            return HttpResponseRedirect('/')
        else:
            messages.add_message(request, messages.ERROR, 'Please ask the administrator to set the department and major for this user before uploading the poster')
            return HttpResponseRedirect('/')
    else:
        return render(request, 'add_poster.html')


def random_poster(request):
    """
    创建海报界面的随机内容填充函数
    """
    fake = Faker("zh_CN")
    data = {
        'title': fake.company(),
        'summary': fake.text(max_nb_chars=50, ext_word_list=None)
    }
    return JsonResponse(data)


def edit_poster(request, poster_id):
    """
    编辑海报
    """
    # 海报不存在，直接返回到首页
    p = Poster.objects.filter(id=poster_id).first()
    if p is None:
        return HttpResponseRedirect('/')

    if request.method == 'GET':
        data = {'poster': p}
        return render(request, 'add_poster.html', context=data)
    else:
        title = request.POST.get('title')
        summary = request.POST.get('summary')
        image = request.FILES.get('image')
        p.title = title
        p.summary = summary
        if image:
            p.image_path = image
        p.save()
        return HttpResponseRedirect('/')


def delete_poster(request, poster_id):
    """
    删除海报
    """
    p = Poster.objects.filter(id=poster_id).first()
    if p:
        p.delete()
    return HttpResponseRedirect('/')


def vote(request, poster_id):
    """
    海报投票
    """
    # 从请求原始参数中获取上次请求的地址，准备跳转回去
    last_url = request.META.get('HTTP_REFERER')
    last_url = last_url.rsplit('&', 1)[0]
    post = Poster.objects.filter(id=poster_id).first()
    if post:
        if post.if_vote == 1:
            messages.add_message(request, messages.SUCCESS, 'You have voted')
        else:
            post.vote_number += 1
            post.if_vote = 1
            post.save()
            last_url += '&action=vote'
    return HttpResponseRedirect(last_url)


@login_required
def score(request, poster_id):
    """
    给海报打分
    """
    user = request.user
    post = Poster.objects.filter(id=poster_id).first()
    score = int(request.POST.get('score'))
    # 确保参数都不为空
    if all([post, score]):
        # 高级评委打分
        if user.role == 'senior_judges':
            post.two_score_total += score
            post.two_score_number += 1
        # 普通评委打分
        else:
            post.one_score_total += score
            post.one_score_number += 1
        post.save()
    return JsonResponse({'status': 'ok'})


def luck_draw(request):
    """
    抽奖函数
    """
    # 从请求原始参数中获取上次请求的地址，准备跳转回去
    last_url = request.META.get('HTTP_REFERER')
    last_url = last_url.rsplit('&', 1)[0]
    user = request.user
    luck = Luck.objects.filter(user=user).first()
    # 下方last_url中拼接的action参数，目前是跳转到首页时，提供不同的消息提醒
    if luck is None:
        Luck.objects.create(user=user)
        last_url += '&action=luck'
    else:
        last_url += '&action=already_luck'
    return HttpResponseRedirect(last_url)


def luck_member(request):
    """
    获取抽奖的人员
    """
    # 只获取luck表中外键关联的user的username字段
    lucks = Luck.objects.all().values_list('user__username')
    member = [i[0] for i in lucks]
    data = {
        'member': member,  # 所有抽奖的人员
        'luck_p': random.choice(member)  # 随机选择一个中奖者
    }
    return JsonResponse(data=data)


def role_number(request):
    """
    设置各个角色的数量
    """
    # get_or_create 如果没从数据库中获取到数据，即创建
    lucky_draw, created = Role.objects.get_or_create({'name': 'lucky_draw'}, name='lucky_draw')
    judges, created = Role.objects.get_or_create({'name': 'judges_number'}, name='judges_number')
    senior_judges, created = Role.objects.get_or_create({'name': 'senior_judges'}, name='senior_judges')
    # poster_manager, created = Role.objects.get_or_create({'name': 'poster_manager'}, name='poster_manager')

    if request.method == 'POST':
        lucky_draw_number = request.POST.get('lucky_draw_number')
        judges_number = request.POST.get('judges_number')
        senior_judges_number = request.POST.get('senior_judges_number')
        # poster_manager_number = request.POST.get('poster_manager_number')
        lucky_draw.amount = lucky_draw_number
        judges.amount = judges_number
        senior_judges.amount = senior_judges_number
        # poster_manager.amount = poster_manager_number

        lucky_draw.save()
        judges.save()
        senior_judges.save()
        # poster_manager.save()

        messages.add_message(request, messages.SUCCESS, 'modify successfully')
    data = {
        'lucky_draw_number': lucky_draw.amount,
        'judges_number': judges.amount,
        'senior_judges_number': senior_judges.amount,
        # 'poster_manager_number': poster_manager.amount,
    }
    return render(request, 'role_number.html', context=data)


def poster_set_bak(request):
    """
    旧版本的作品集函数： 展示优秀作品(6个)和最佳作品(3个)
    """
    base_query = Poster.objects.exclude(one_score_number=0).order_by('-one_score_avg')
    post_1 = base_query[:6]
    post_2 = base_query.order_by('-two_score_avg')[:3]
    data = {
        'post_1': post_1, 'post_2': post_2
    }
    return render(request, 'poster_set.html', context=data)


def poster_set(request):
    """
    新版本作品集，获取每个专业相对应的高分作品(高级评委评分过的)
    """
    # 获取所有学院和专业
    grades = Grade.objects.all()
    # 选出每个学院专业中高级评委分数给的最高的n个(n的数量是由管理员决定的)
    grades_list = []
    for g in grades:
        query_set = Poster.objects.filter(grade=g.id).exclude(one_score_number=0).order_by('-two_score_avg')
        grades_list.append({
            'college': g.college, 'posters': query_set[:g.poster_number], 'major': g.major
        })
    data = {
        'posters': grades_list, 'grades': [(i.college, i.major) for i in grades]
    }
    return render(request, 'new_poster_set.html', context=data)


def list_grade(request):
    grades = Grade.objects.all()
    data = {
        'grades': grades
    }
    return render(request, 'grades.html', context=data)


def add_grade(request):
    if request.method == 'POST':
        college = request.POST.get('college')
        major = request.POST.get('major')
        g = Grade.objects.filter(college=college, major=major).first()
        if g is not None:
            messages.add_message(request, messages.WARNING, 'data duplication')
        else:
            Grade.objects.create(college=college, major=major)
            return HttpResponseRedirect('/users/grades/')
    return render(request, 'add_grade.html')


def del_grade(request, grade_id):
    """
    删除学院专业
    """
    g = Grade.objects.filter(id=grade_id).first()
    if g:
        g.delete()
    return HttpResponseRedirect('/users/grades/')


def edit_grade(request, grade_id):
    """
    编辑海报
    """
    # 海报不存在，直接返回到首页
    g = Grade.objects.filter(id=grade_id).first()
    if g is None:
        return HttpResponseRedirect('/')

    if request.method == 'GET':
        data = {'grade': g}
        return render(request, 'add_grade.html', context=data)
    else:
        college = request.POST.get('college')
        major = request.POST.get('major')
        poster_number = request.POST.get('poster_number')
        g.college = college
        g.major = major
        g.poster_number = poster_number
        g.save()
        return HttpResponseRedirect('/users/grades/')


@login_required
def edit_user(request, user_id):
    """
    编辑用户处理函数,包括修改，删除
    request参数为请求对象
    """
    # 根据前端传入的user_id查询数据库中是否存在，不存在即为非法请求
    user = User.objects.filter(id=user_id).first()
    if user:
        # 当请求方式为get请求时，直接渲染注册页面
        if request.method.lower() == 'get':
            data = {
                'user': user.to_json()
            }
            grades_queryset = Grade.objects.all()
            grades = []
            college_set = []
            # 简单去个重
            for i in grades_queryset:
                if i.college not in college_set:
                    grades.append(i)
                    college_set.append(i.college)
            data.update({
                'grades': grades
            })
            return render(request, 'user-edit.html', context=data)
        # 当请求方式为get请求时，直接渲染注册页面
        elif request.method.lower() == 'post':
            # 当请求方式为post时，获取前端传入参数对数据库中的相应用户进行修改
            nickname = request.POST.get('nickname')
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            role = request.POST.get('role')
            college = request.POST.get('college')
            major = request.POST.get('major')
            grade = Grade.objects.filter(college=college, major=major).first()
            if role == 'poster_manager':
                # 这里判断每个专业的海报管理者数量
                number = 0
                major = major or user.grade_r.major
                grade = Grade.objects.filter(college=college, major=major).first()
                if grade is not None:
                    users = User.objects.filter(grade=grade.id)
                    for u in users:
                        if u.role == role:
                            number += 1
                if number > 0:
                    messages.add_message(request, messages.ERROR, 'The college already has a poster manager')
                    return HttpResponseRedirect('/')
            else:
                role_count = User.objects.filter(role=role).count()
                if user.role == role:
                    role_count -= 1
                upper_limit = Role.objects.filter(name=role).first()
                if upper_limit is not None:
                    upper_limit = upper_limit.amount
                else:
                    upper_limit = 0
                if upper_limit != 0 and role_count >= upper_limit:
                    messages.add_message(request, messages.ERROR, 'The number of roles reached the upper limit. ')
                    return render(request, 'user-edit.html')
            if password:
                user.set_password(password)
            user.username = username
            user.nickname = nickname
            user.email = email
            user.role = role
            if grade is not None:
                user.grade = str(grade.id)
            try:
                user.save()
            except Exception as e:
                messages.add_message(request, messages.ERROR, str(e))
                return HttpResponseRedirect('/')
        else:
            # 删除用户
            user.delete()
    # 修改完跳转到用户列表界面
    return HttpResponseRedirect('/users/admin-users/')


def meeting(request):
    """
    会议内容设置
    """
    m = Meeting.objects.all().first()
    data = {'meeting': m}
    if request.method == 'GET':
        return render(request, 'mettings.html', context=data)
    else:
        title = request.POST.get('title')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        people_num = request.POST.get('people_num')

        start_time_p = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        end_time_p = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
        if start_time_p > end_time_p:
            data.update({'message': ' The start time of a meeting cannot be later than the end time'})
            return render(request, 'mettings.html', context=data)

        if m is None:
            m = Meeting(
                title=title, start_time=start_time,
                end_time=end_time, number=people_num
            )
        else:
            m.title = title
            m.start_time = start_time
            m.end_time = end_time
            m.number = people_num
        m.save()
        data.update({'message': 'save successfully'})
        return render(request, 'mettings.html', context=data)


def send_email(request):
    """
    浏览者发送邮件，邮件内容有投票的链接
    """
    email = request.POST.get('email')
    user = User.objects.filter(email=email).first()
    if user is None:
        User.objects.create(username=email, email=email, password=make_password('123456'))
    token = random_string()
    cache.set(token, email)
    # 发送邮件, 如果修改了IP和Port，需要把这里也修改了
    poster_url = 'http://127.0.0.1:9000/users/poster_manager/?token=%s' % token
    print(poster_url)
    try:
        mail.send_mail(
            subject='Title', message='click: %s' % poster_url,
            recipient_list=[email], from_email=settings.EMAIL_HOST_USER
        )
    except Exception:
        messages.add_message(request, messages.WARNING, poster_url)
    messages.add_message(request, messages.SUCCESS, 'send successfully')
    return HttpResponseRedirect('/')


def get_majors(request):
    data = {}
    college = request.GET.get('college')
    if college:
        grades = Grade.objects.filter(college=college)
        data.update({
            'majors': [g.major for g in grades]
        })
    return JsonResponse(data)

