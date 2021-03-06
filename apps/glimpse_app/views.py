from django.shortcuts import render, HttpResponse, redirect
from django.db import models
from .models import User, Device
import bcrypt, sys, os, base64, datetime, hashlib, hmac 
from django.contrib import messages
import boto3, csv
import pandas as pd
# The below key is how we need to connect to the AWS without having our server hard coded with the keys
# conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# bucket = conn.get_bucket("<your-bucket-name>")
client = boto3.client('s3') #low-level functional API
resource = boto3.resource('s3') #high-level object-oriented API
test_bucket = resource.Bucket('pi-1') #subsitute this for your s3 bucket name. 

def index(request):
    return render(request, "homepage.html")
def registerLoginPage(request):
    return render(request, "registerPage.html")
def adminLogin(request):
    return render(request, "adminLogin.html")

def createUser(request):
    if request.method=="POST":
        errors = User.objects.basic_validator(request.POST)
        if len(errors):
            for key, value in errors.items():
                messages.error(request, value)
            return redirect('/registerLoginPage', errors)
        else:
            device_number = request.POST['deviceNumber']
            bucket_select = "user" + device_number
            bucket_images = bucket_select + "/images"
            bucket_videos = bucket_select + "/videos"
            this_users_images = test_bucket.objects.filter(Prefix=bucket_images)
            this_users_videos = test_bucket.objects.filter(Prefix=bucket_videos)
            imgCount = 0
            vidCount = 0
            User.objects.create(full_name=request.POST['usersName'], email_address=request.POST['usersEmail'], phone_number=request.POST['usersPhone'], number_pics = imgCount, number_vids = vidCount, device_key_name=request.POST['deviceNumber'])
            Device.objects.create(device_owner = User.objects.get(device_key_name = device_number), device_key_name = "SerialNumber", number_pics = imgCount, number_vids = vidCount)
            # The above line will be changed to S3 syntax to send the new user information to the database and will create a new user.
            last_user = User.objects.last()
            request.session['user_id'] = last_user.id
            return redirect('/userPage')
    return redirect('/')

def login(request):
    if request.method == "POST":
        errors = User.objects.login_validator(request.POST)
        if len(errors):
            for key, value in errors.items():
                messages.error(request, value)
            return redirect('/registerLoginPage', errors)
        if User.objects.filter(email_address=request.POST['emailsLogin']):
            user = User.objects.get(email_address=request.POST['emailsLogin'])
            if user.device_key_name == request.POST['deviceNumber']:
                request.session['user_id'] = user.id
                return redirect('/userPage')
    return redirect('/')

def userPage(request):
    user_id = User.objects.get(id=request.session['user_id'])
    device_id = Device.objects.get(device_owner = user_id.id)
    device_number = user_id.device_key_name
    bucket_select = "user" + device_number
    bucket_images = bucket_select + "/images"
    throw_images = bucket_images + "/"
    bucket_videos = bucket_select + "/videos"
    throw_videos = bucket_videos + "/"
    file_name = bucket_select + "/"
    this_users_files = test_bucket.objects.filter(Prefix=bucket_select)
    this_users_images = test_bucket.objects.filter(Prefix=bucket_images)
    this_users_videos = test_bucket.objects.filter(Prefix=bucket_videos)
    imgCount = 0
    for image in this_users_images:
        imgCount += 1
    vidCount = 0
    for vid in this_users_videos:
        vidCount += 1
    user_id.number_pics = imgCount
    user_id.number_vids = vidCount
    device_id.number_pics = imgCount
    device_id.number_vids = vidCount
    user_id.save()
    device_id.save()
    context = {
        'name':user_id.full_name,
        'this_user': this_users_files,
        'this_user_images': this_users_images,
        'this_user_videos': this_users_videos,
        'file_name': file_name,
        'not_bucket_select_img': throw_images,
        'not_bucket_select_vid': throw_videos,
    }
    return render(request, "eventPage.html", context)

def godModeCheck(request):
    if request.method == "POST":
        if request.POST['godModeLogin'] == "Dylan Rose" and request.POST['godModePassword'] == "isourboss":
            request.session['user_id'] = 0
            return redirect('/godMode')
        else:
            return redirect('/adminLogin')

def godMode(request):
    if request.session['user_id'] != 0:
        print("get out of here")
        return redirect('/adminLogin')
    else:
        context = {
            'users': User.objects.all(),
            'devices': Device.objects.all()
        }
        context['objects'] = test_bucket.objects.filter(Prefix='user')
        context['battery'] = test_bucket.objects.filter(Prefix='user2/battery.csv')
        return render(request, "godMode.html", context)

def viewUserInfoGodMode(request, user_num):
    user_id = User.objects.get(device_key_name=user_num)
    bucket_select = "user" + user_num
    bucket_images = bucket_select + "/images"
    throw_images = bucket_images + "/"
    bucket_videos = bucket_select + "/videos"
    throw_videos = bucket_videos + "/"
    file_name = bucket_select + "/"
    # key_name = throw_images + "battery.csv"
    # obj = client.get_object(Bucket='test_bucket', Key=key_name)
    # grid_sizes = pd.read_csv(obj['Body'])
    this_users_files = test_bucket.objects.filter(Prefix=bucket_select)
    this_users_images = test_bucket.objects.filter(Prefix=bucket_images)
    this_users_videos = test_bucket.objects.filter(Prefix=bucket_videos)
    battery_select = bucket_select + "/battery.csv"
    battery_info = test_bucket.objects.filter(Prefix=battery_select)
    context = {
        'name':user_num,
        'file_name': file_name,
        'this_user_images': this_users_images,
        'this_user_videos': this_users_videos,
        'not_bucket_select_img': throw_images,
        'not_bucket_select_vid': throw_videos,
    }
    return render(request, "viewUserInfoGodMode.html", context)

def logout(request):
    request.session.clear()
    return redirect('/')

def deleteUser(request, user_id):
    User.objects.get(id=user_id).delete()
    return redirect('/godMode')

def viewImage(request, match):
    cont = {
        'image': match
    }
    return render(request, "viewImage.html", cont)
    