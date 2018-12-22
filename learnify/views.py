from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from learnify.forms import *
from learnify.models import *
from django.conf import settings
from django.views.generic.base import TemplateView
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

logged_in_user = None
stripe.api_key = settings.SECRET


def index(request):
    registered = False
    global logged_in_user
    if request.method == "POST":
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            if "profile_pic" in request.FILES:
                profile.profile_pic = request.FILES["profile_pic"]
            profile.save()
            registered = True
            return redirect("user_login")
        else:
            print(user_form.errors, profile_form.errors)
    else:
        # global logged_in_user
        user_form = UserForm()
        profile_form = UserProfileForm()
        # profile = logged_in_user
    return render(
        request,
        "learnify/index.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "registered": registered,
            "logged_in_user": logged_in_user,
        },
    )


def courses(request):
    global logged_in_user
    courses = Course.objects.all()
    stripe_key = settings.APIKEY
    purchases = Purchase.objects.filter(purchaser=logged_in_user)
    return render(request, 'learnify/courses.html', {
        'courses': courses,
        'stripe_key': stripe_key,
        "logged_in_user": logged_in_user,
        "purchases": purchases
    })


def course_detail(request, pk):
    global logged_in_user
    course = Course.objects.get(id=pk)
    stripe_key = settings.APIKEY
    reviews = Review.objects.filter(course=course)
    purchases = Purchase.objects.filter(purchaser=logged_in_user)
    purchased = False
    for purchase in purchases:
        if purchase.pk == course.pk:
            purchased = True
    videos = Video.objects.filter(course=course)
    print(purchased)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.author_id = logged_in_user.pk
            review.course_id = course.pk
            review.save()
    else:
        form = ReviewForm()
    return render(
        request,
        'learnify/course_detail.html',
        {
        'form': form,
        'course': course,
        "logged_in_user": logged_in_user,
        "stripe_key": stripe_key,
        "purchased": purchased,
        "course": course, 
        "videos": videos,
        "reviews": reviews
        })
    
def about(request):
    return render(request, "learnify/about.html", {"logged_in_user": logged_in_user})

def course_create(request):
    global logged_in_user
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.owner_id = logged_in_user.pk
            if "preview_video" in request.FILES:
                course.preview_video = request.FILES["preview_video"]
            course.save()
            return redirect("course_detail", pk=course.pk)
    else:
        form = CourseForm()
    return render(
        request,
        "learnify/create_course_form.html",
        {"form": form, "logged_in_user": logged_in_user},
    )

@login_required
def edit_course(request, pk):
    course = Course.objects.get(id=pk)
    global logged_in_user
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            courseform = form.save(commit=False)
            courseform.owner_id = logged_in_user.pk
            if "preview_video" in request.FILES:
                courseform.preview_video = request.FILES["preview_video"]
            courseform.save()
            return redirect("course_detail", pk=course.pk)
    else:
        form = CourseForm(instance=course)
        return render(
            request,
            "learnify/edit_course.html",
            {
            "form":form, 
            "logged_in_user":logged_in_user, 
            "course": course
            })


@login_required
def add_video(request, pk):
    global logged_in_user
    course = Course.objects.get(id=pk)
    if request.method == "POST":
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.course_id = course.pk
            if "video" in request.FILES:
                course.preview_video = request.FILES["video"]
            video.save()
            return redirect("course_detail", pk=course.pk)
    else:
        form = VideoForm()
    return render(
        request,
        "learnify/add_video.html",
        {"form": form,
        "logged_in_user": logged_in_user,
        "course":course},
    )

@login_required
def profile(request, username):
    user = User.objects.get(username=username)
    profile = UserProfile.objects.get(user=user)
    global logged_in_user
    logged_in_user = profile
    purchases = Purchase.objects.filter(purchaser=profile)
    return render(
        request,
        "learnify/profile.html",
        {"profile": profile, "logged_in_user": logged_in_user, "purchases": purchases},
    )


@login_required
def special(request):
    return HttpResponse("You are logged in")


@login_required
def user_logout(request):
    logout(request)
    global logged_in_user
    logged_in_user = None
    return redirect("index")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return redirect(f"profile/{username}")
            else:
                return HttpResponse("Your account was inactive.")
        else:
            print("Someone tried to login and failed.")
            print(f"They used username: {username} and password {password}")
            # return HttpResponse("Invalid login details given")
            messages.error(request,'Incorrect login details! Try again.')
            return redirect('user_login')
    else:
        return render(request, "learnify/login.html", {})

@login_required 
def checkout(request, pk):
    global logged_in_user
    new_purchase = Purchase(
        course = Course.objects.get(id=pk),
        purchaser = logged_in_user
    )
    print('HERE IS THE TYPE')
    print(type(new_purchase.course.price))
    print( round(new_purchase.course.price, 2))

    if request.method == "POST":
        token = request.POST.get("stripeToken")

    try:
        charge = stripe.Charge.create(
            amount= int(new_purchase.course.price * 100),
            currency='usd',
            description=Course.title,
            source=request.POST['stripeToken']
        )

        new_purchase.charge_id = charge.id
    
    except stripe.error.CardError as ce:
        return False, ce

    else:
        new_purchase.save()
        return render(request, 'learnify/charge.html')