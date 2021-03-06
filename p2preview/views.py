# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, render_to_response
from django.template import loader
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from p2preview.models import Person, Student, Instrutor, Course, RegisteredCourses, GroupDetail, Group, Activity, RegisteredGroupsForActivity, Criteria, GenericOption, Response, Rubric, Generic, UploadFile

import string
import random
import ast

@require_http_methods(["GET"])
@csrf_exempt
def fetch_self(request):
    person = validatePerson(request.META['HTTP_TOKEN'])
    if person != -1:
        if person[0].personType == 1:
            instrutor = Instrutor.objects.filter(iId=person[0])
            data = {
                'success': 1,
                'message': '',
                'self': {
                    'name': person[0].name,
                    'email': person[0].email,
                }
            }
        elif person[0].personType == 2:
            student = Student.objects.filter(sId=person[0])
            data = {
                'success': 1,
                'message': '',
                'self': {
                    'name': person[0].name,
                    'email': person[0].email,
                    'rollNo': student[0].rollNo,
                    'branch': student[0].branch,
                }
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
        }
    return JsonResponse(data, safe=True)


# Create your views here.
@csrf_exempt
def home(request):
    person = validatePerson(request.COOKIES.get('token'))
    if person != -1:
        template = loader.get_template('p2preview/home.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        return redirectToLogin()

@csrf_exempt
def activity_details(request, pk):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if instrutor != -1:
        activity = Activity.objects.filter(pk=pk, iId=instrutor[0])
        if (activity.count() == 1):
            """get criterias of the activity"""
            criterias = []
            criterias_data = Criteria.objects.filter(rubricId=activity[0].rubricId)
            for criteria in criterias_data:
                criterias.append(str(criteria.genericId.description))
            #registeredGroup = RegisteredGroupsForActivity.objects.filter(activityId=activity[0])

            #responses = Response.objects.filter()
            template = loader.get_template('p2preview/statistics.html')
            context = {
                'criterias': criterias
            }
            return HttpResponse(template.render(context, request))
        else:
            """redirect to /activity"""
            response = HttpResponseRedirect('/activity')
            response.delete_cookie('token')
            return response

    else:
        return redirectToLogin()

def activity(request):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if instrutor != -1:
        template = loader.get_template('p2preview/activity.html')
        activities_data = Activity.objects.filter(iId=instrutor[0]).order_by('-pk')
        activities = []
        for activity in activities_data:
            activities.append({
                'activity': activity,
                'groupsRegistered': RegisteredGroupsForActivity.objects.filter(activityId=activity).count()
            })

        context = {
            'rubrics': Rubric.objects.filter(iId=instrutor[0]),
            'courses': Course.objects.filter(instructorId=instrutor[0]),
            'activities': activities
        }
        return HttpResponse(template.render(context, request))
    else:
        return redirectToLogin()

@require_http_methods(["POST"])
@csrf_exempt
def toggle_activity_status(request):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if instrutor != -1:
        activity = Activity.objects.filter(pk=request.POST["activity_id"])
        if (activity.count() == 1):
            if (request.POST["value"] == 'True'):
                activity.update(isActive=True)
            else:
                activity.update(isActive=False)
            data = {
                'success': 1,
                'message': 'Successfully updated',
            }
        else:
            data = {
                'success': 0,
                'message': 'No activity found',
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
        }
    return JsonResponse(data, safe=True)

@csrf_exempt
def login_page(request):
    token = request.COOKIES.get('token')
    person = Person.objects.filter(token=token)
    if person.count() == 1:
        return HttpResponseRedirect('/')
    elif person.count() == 0:
        return render(request, 'p2preview/login.html')
    else:
        return redirectToLogin()

@require_http_methods(["POST"])
@csrf_exempt
def create_course(request):
    instrutor = validateInstructor(request.META['HTTP_TOKEN'])
    if (instrutor != -1):
        course = Course(name=request.POST['name'],
                        description=request.POST['description'],
                        instructorId=instrutor[0],
                        code=getRandomString(5))
        try:
            course.save()
            data = {
                'success': 1,
                'message': 'Course Successfully Created',
            }
        except:
            data = {
                'success': 0,
                'message': 'Please try again',
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
        }
    return JsonResponse(data, safe=True)


@csrf_exempt
def course(request):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if (instrutor != -1):
        template = loader.get_template('p2preview/course.html')
        courses = getInstructorCourses(instrutor).order_by('-pk')
        courseDetails = []
        for course in courses:
            courseDetails.append({
                'course': course,
                'students': getStudentsInCourse(course),
            })
        context = {
            'courses': courseDetails
        }
        return render_to_response('p2preview/course.html', context)
    else:
        return redirectToLogin();

@require_http_methods(["POST"])
@csrf_exempt
def submit_responses(request):
    student = validateStudent(request.META['HTTP_TOKEN'])
    if (student != -1):
        try:
            """get group"""
            group = Group.objects.filter(pk=request.POST["group_id"])
            if(group.count() == 1):
                """get activity"""
                activity = Activity.objects.filter(code=request.POST["activity_code"])
                if(activity.count() == 1):
                    """get registered group"""
                    registeredGroup = RegisteredGroupsForActivity.objects.filter(groupId=group[0], activityId=activity[0])
                    if(registeredGroup.count() == 1):
                        answers = request.POST['answers']
                        answers = ast.literal_eval(answers)
                        for answer in answers:
                            """get criteria"""
                            criteria = Criteria.objects.filter(pk=answer.get('criteria_id'))
                            if (criteria.count() == 1):
                                response = Response(registeredGroup=registeredGroup[0],
                                                    criteria=criteria[0],
                                                    response=answer.get('optionNumber'),
                                                    comment=answer.get('comment'))
                                response.save()
                        data = {
                            'success': 1,
                            'message': 'Successfully saved responses!!',
                            'data': get_activity_data_from_registered_group(registeredGroup[0])
                        }
                    else:
                        data = {
                            'success': 2,
                            'message': 'No registerted group found!!',
                            'data': []
                        }
                else:
                    data = {
                        'success': 2,
                        'message': 'No activity found!!',
                        'data': []
                    }
            else:
                data = {
                    'success': 2,
                    'message': 'No group found!!',
                    'data': []
                }
        except:
            data = {
                'success': 3,
                'message': 'Please try again!!',
                'data': []
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
            'data': []
        }
    return JsonResponse(data, safe=True)

@require_http_methods(["GET"])
@csrf_exempt
def get_student_courses(request):
    student = validateStudent(request.META['HTTP_TOKEN'])
    if (student != -1):
        registeredCourses = RegisteredCourses.objects.filter(sId=student).order_by('-pk')
        courses = []
        for reg in  registeredCourses:
            courses.append({
                'name': reg.courseId.name,
                'code': reg.courseId.code,
                'description': reg.courseId.description,
                'instructorName': reg.courseId.instructorId.iId.name
                })
        data = {
            'success': 1,
            'courses': courses
        }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
            'courses': []
        }
    return JsonResponse(data, safe=True)

def get_recommended_group_for_students(student, course, groupSize):
    groupDetails = GroupDetail.objects.filter(sId=student).order_by('-pk')
    groups = []
    for group in groupDetails:
        """Check if all group members are registered to that course or not"""
        membersGroupDetails = GroupDetail.objects.filter(groupId=group.groupId)
        memCount = membersGroupDetails.count()
        """check if group size is less than activity group size"""
        if (memCount <= groupSize):
            for gd in membersGroupDetails:
                if (RegisteredCourses.objects.filter(courseId=course, sId=gd.sId).count() == 1):
                    memCount = memCount - 1
            if (memCount == 0):
                groups.append({
                    'members': get_group_members(group.groupId),
                    'name': group.groupId.name,
                    'id': group.groupId.pk,
                    })
    return groups

def register_group_to_activity_data(group_id, activity_code):
    try:
        activity = Activity.objects.filter(code=activity_code)
        group = Group.objects.filter(pk=group_id)
        # TODO check all group members are registered to that course
        """Register group to activity"""
        registeredGroupsForActivity = RegisteredGroupsForActivity(activityId=activity[0], groupId=group[0])
        registeredGroupsForActivity.save()
        activity_details = Activity.objects.get(code=activity_code)
        criterias_data = []
        criterias = Criteria.objects.filter(rubricId=activity_details.rubricId)
        for criteria in criterias:
            options_data = []
            options = GenericOption.objects.filter(genericId=criteria.genericId).order_by('optionNo')
            for option in options:
                options_data.append({
                    'option': option.option,
                    'option_number': option.optionNo
                })
            criterias_data.append({
                'criteria_id': criteria.pk,
                'description': criteria.genericId.description,
                'options': options_data
            })
        data = {
            'success': 1,
            'message': 'Successfully registered',
            'data': {
                'activity': {
                    'name': activity_details.name,
                    'code': activity_details.code,
                    'fileURL': activity_details.fileURL,
                    'duration': activity_details.duration,
                },
                'criteria': criterias_data
            }
        }
        return data
    except:
        return {
            'success': 0,
            'message': 'Please try again',
            'data': {}
        }

@require_http_methods(["POST"])
@csrf_exempt
def register_group_to_activity(request):
    student = validateStudent(request.META['HTTP_TOKEN'])
    if (student != -1):
        activity_code = request.POST['activityCode']
        group_id = request.POST['groupCode']
        data = register_group_to_activity_data(group_id, activity_code)
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
            'data': {}
        }
    return JsonResponse(data, safe=True)

def get_student_groups_data(student):
    groupDetails = GroupDetail.objects.filter(sId=student).order_by('-pk')
    groups = []
    for group in groupDetails:
        groups.append({
            'members': get_group_members(group.groupId),
            'name': group.groupId.name,
            'id': group.groupId.pk,
            })
    return groups

@require_http_methods(["GET"])
@csrf_exempt
def get_student_groups(request):
    student = validateStudent(request.META['HTTP_TOKEN'])
    if (student != -1):
        groups = get_student_groups_data(student)
        data = {
            'success': 1,
            'data': {
                'groups': groups
            }
        }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
            'data': {}
        }
    return JsonResponse(data, safe=True)

@require_http_methods(["POST"])
@csrf_exempt
def get_activity_group_composition(request):
    student = validateStudent(request.META['HTTP_TOKEN'])
    if (student != -1):
        """Find course of activity"""
        activitys = Activity.objects.filter(code=request.POST["code"], isActive=True)
        if (activitys.count() == 1):
            """Check if student is registered to that course"""
            registeredCourses = RegisteredCourses.objects.filter(courseId=activitys[0].courseId, sId=student[0])
            if (registeredCourses.count() == 1):
                """Student is registered for the course to which is activity belongs"""
                """get recommended groups"""
                recommendedGroups = get_recommended_group_for_students(student[0], activitys[0].courseId, activitys[0].groupSize)
                data = {
                    'success': 1,
                    'message': 'Activity code is valid',
                    'data': {
                        'activity': {
                            'name': activitys[0].name,
                            'code': activitys[0].code,
                            'courseCode': activitys[0].courseId.code,
                            'groupSize': activitys[0].groupSize,
                        },
                        'recommendedGroups': recommendedGroups
                    }
                }
            else:
                data = {
                    'success': 0,
                    'message': 'This activity is not for you. You haven\'t registered to the corresponding course.',
                    'data': {}
                }
        else:
            data = {
                'success': 0,
                'message': 'Invalid activity code.',
                'data': {}
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
            'data': {}
        }
    return JsonResponse(data, safe=True)

@require_http_methods(["POST"])
@csrf_exempt
def add_student_course(request):
    student = validateStudent(request.META['HTTP_TOKEN'])
    if (student != -1):
        registeredCourse = addStudentInCourse(student[0], request.POST['code'])
        if (registeredCourse == -1):
            data = {
                'success': -1,
                'message': 'Please enter a valid code',
                'course': []
            }
        else:
            course = validateCourse(request.POST['code'])
            coursesResponse = []
            coursesResponse.append({
                'name': course[0].name,
                'code': course[0].code,
                'description': course[0].description,
                'instructorName': course[0].instructorId.iId.name
            })
            data = {
                'success': 1,
                'message': 'Course successfully added',
                'course': coursesResponse
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
            'course': []
        }
    return JsonResponse(data, safe=True)

def get_activity_data_from_registered_group(registeredGroupsForActivity):
    responses = []
    responsesData = Response.objects.filter(registeredGroup=registeredGroupsForActivity)
    lateSub = 0
    for response in responsesData:
        options = []
        optionsData = GenericOption.objects.filter(genericId=response.criteria.genericId).order_by('optionNo')
        for option in optionsData:
            options.append({
                'option': option.option,
                'points': option.points,
                'optionNo': option.optionNo
            })
        criteria = {
            'question': response.criteria.genericId.description,
            'answer': response.criteria.genericId.answer,
            'options': options,
            'id': response.criteria.pk
        }
        if (lateSub == 0 and (response.time - registeredGroupsForActivity.time).total_seconds() > registeredGroupsForActivity.activityId.duration):
            lateSub = 1
        responses.append({
            'criteria': criteria,
            'response': response.response,
            'comment': response.comment,
        })
    return {
        'activity': {
            'course': registeredGroupsForActivity.activityId.courseId.name,
            'name': registeredGroupsForActivity.activityId.name,
            'code': registeredGroupsForActivity.activityId.code,
            'duration': registeredGroupsForActivity.activityId.duration
        },
        'responses': responses,
        'groupId': registeredGroupsForActivity.groupId.pk,
        'lateSub': lateSub
    }

@require_http_methods(["GET"])
@csrf_exempt
def student_activities(request):
    student = validateStudent(request.META['HTTP_TOKEN'])
    if (student != -1):
        """get all groups of student"""
        groups = get_student_groups_data(student)
        activity = []
        for group in groups:
            groupObject = Group.objects.filter(pk=group.get("id"))
            if (groupObject.count() == 1):
                """check if this group is registered to activity or not"""
                registeredGroupsForActivity = RegisteredGroupsForActivity.objects.filter(groupId=groupObject[0]).order_by('time')
                if (registeredGroupsForActivity.count() == 1):
                    activity.append(get_activity_data_from_registered_group(registeredGroupsForActivity[0]))

        data = {
            'success': 1,
            'message': '',
            'activities': activity
        }
    else:
        data = {
            'success': -99,
            'message': 'Please login again',
            'course': []
        }
    return JsonResponse(data, safe=True)

@require_http_methods(["POST"])
@csrf_exempt
def register(request):
    person = Person(name=request.POST['name'],
                    email=request.POST['email'],
                    password=request.POST['password'],
                    personType=request.POST['personType'])
    try:
        person.save()
        if request.POST['personType'] == 1:
            instrutor = Instrutor(iId=person,
                                  department=request.POST['department'],
                                  office=request.POST['office'],
                                  visitingHours=request.POST['visitingHours'])
            instrutor.save()
        elif request.POST['personType'] == 2:
            student = Student(sId=person,
                              rollNo=request.POST['rollNo'],
                              branch=request.POST['branch'])
            student.save()
        data = {
            'success': 1,
            'message': 'Successfully registered',
        }
    except:
        """Check if email already registered"""
        persons = Person.objects.filter(email=request.POST['email'])
        if (persons.count() > 0):
            message = request.POST['email'] +  ' is already associated with another account.'
        else:
            message = 'Please try again'
        data = {
            'success': 0,
            'message': message,
        }
    return JsonResponse(data, safe=True)

@csrf_exempt
def new_course_page(request):
    return render(request, 'p2preview/course_new.html')

def statistics_page(request):
    return render(request, 'p2preview/statistics.html')

@require_http_methods(["POST"])
@csrf_exempt
def upload_file(request):
    try:
        new_file = UploadFile(file = request.FILES['file'])
        new_file.save()
        data = {
            'success': 1,
            'message': 'Successfully uploaded',
            'data': {
                'url': '/' + str(new_file.file)
            }
        }
    except:
        data = {
            'success': 0,
            'message': 'Please try again!!'
        }
    return JsonResponse(data, safe=True)

@require_http_methods(["POST"])
@csrf_exempt
def create_activity(request):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if instrutor != -1:
        try:
            course = Course.objects.filter(pk=request.POST["course_id"])
            if (course.count() == 1):
                rubric = Rubric.objects.filter(pk=request.POST["rubric_id"])
                if (rubric.count() == 1):
                    activity = Activity(iId=instrutor[0],
                                        courseId=course[0],
                                        rubricId=rubric[0],
                                        name=request.POST["activity_name"],
                                        code=getRandomString(5),
                                        fileURL=request.POST["file_path"],
                                        duration=request.POST["duration"],
                                        groupSize=request.POST["groupSize"])
                    activity.save()
                    data = {
                        'success': 1,
                        'message': 'Successfully added',
                        'data': {

                        }
                    }
                else:
                    data = {
                        'success': 0,
                        'message': 'Please select valid rubric'
                    }
            else:
                data = {
                    'success': 0,
                    'message': 'Please select valid course'
                }
        except:
            data = {
                'success': 0,
                'message': 'Please try again'
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again'
        }

    return JsonResponse(data, safe=True)

@require_http_methods(["POST"])
@csrf_exempt
def create_rubric(request):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if instrutor != -1:
        try:
            """create rubric"""
            rubric = Rubric(iId=instrutor[0],
                            name=request.POST["rubric_name"])
            rubric.save()

            """create criteria"""
            criterias = ast.literal_eval(request.POST["criterias"])
            for criteria in criterias:
                generic = Generic.objects.filter(pk=criteria)
                if (generic.count() == 1):
                    criteria_object = Criteria(rubricId=rubric,
                                               genericId=generic[0])
                    criteria_object.save()
            data = {
                'success': 1,
                'message': 'Successfully created'
            }

        except:
            data = {
                'success': 0,
                'message': 'Please try again'
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again'
        }

    return JsonResponse(data, safe=True)

@require_http_methods(["POST"])
@csrf_exempt
def create_generic(request):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if instrutor != -1:
        try:
            """create generic"""
            generic = Generic(description=request.POST["description"],
                              answer=request.POST["answer"])
            generic.save()
            """"create generic options"""
            genericOption1 = GenericOption(genericId=generic,
                                           option=request.POST["option1"],
                                           points=request.POST["option1Points"],
                                           optionNo=1)
            genericOption1.save()

            genericOption2 = GenericOption(genericId=generic,
                                           option=request.POST["option2"],
                                           points=request.POST["option2Points"],
                                           optionNo=2)
            genericOption2.save()

            genericOption3 = GenericOption(genericId=generic,
                                           option=request.POST["option3"],
                                           points=request.POST["option3Points"],
                                           optionNo=3)
            genericOption3.save()

            genericOption4 = GenericOption(genericId=generic,
                                           option=request.POST["option4"],
                                           points=request.POST["option4Points"],
                                           optionNo=4)
            genericOption4.save()

            data = {
                'success': 1,
                'message': 'Successfully created'
            }

        except:
            data = {
                'success': 0,
                'message': 'Please try again'
            }
    else:
        data = {
            'success': -99,
            'message': 'Please login again'
        }

    return JsonResponse(data, safe=True)

def rubric_template(request):
    instrutor = validateInstructor(request.COOKIES.get('token'))
    if instrutor != -1:
        template = loader.get_template('p2preview/rubric_template.html')
        rubrics = []
        rubric_data = Rubric.objects.filter(iId=instrutor).order_by('-pk')
        for rubric in rubric_data:
            criterias = []
            criterias_data = Criteria.objects.filter(rubricId=rubric).order_by('-pk')
            for criteria in criterias_data:
                criterias.append({
                    'generic_options': GenericOption.objects.filter(genericId=criteria.genericId).order_by('-pk'),
                    'criteria': criteria
                })
            rubrics.append({
                'rubric': rubric,
                'criterias': criterias
            })
        all_criterias = []
        generic_data = Generic.objects.filter().order_by('-pk')
        for generic in generic_data:
            all_criterias.append({
                'generic_options': GenericOption.objects.filter(genericId=generic).order_by('-pk'),
                'generic': generic
            })
        context = {
            'criterias': all_criterias,
            'rubrics': rubrics
        }
        return HttpResponse(template.render(context, request))
    else:
        return redirectToLogin()

def signUp_page(request):
    return render(request, 'p2preview/signup.html')

@csrf_exempt
def login(request):
    """
    Check crendentials
    """
    if request.method == 'POST':
        person = Person.objects.filter(email=request.POST['email'], password=request.POST['password'])
        if (person.count() == 1):
            char_set = string.ascii_uppercase + string.digits + string.ascii_lowercase
            token = ''.join(random.sample(char_set*10, 10))
            person.update(token=token)
            data = {
                'success': 1,
                'token': token,
                'message': 'Successfully logged In'
            }
        elif (person.count() > 1):
            data = {
                'success': 0,
                'message': 'Multiple accounts are associated with this email id. Please contact administrator'
            }
        elif (person.count() == 0):
            person = Person.objects.filter(email=request.POST['email'])
            if (person.count() == 1):
                data = {
                    'success': 0,
                    'message': 'Hi, ' + person[0].name + ' your password is wrong. Please try again'
                }
            elif (person.count() == 0):
                data = {
                    'success': 0,
                    'message': "Sorry, this email address isn't registered with us."
                }
            elif (person.count() > 1):
                data = {
                    'success': 0,
                    'message': "Multiple accounts are associated with this email id. Please contact administrator"
                }

        return JsonResponse(data, safe=True)

@csrf_exempt
def logout(request):
    person = validatePerson(request.META['HTTP_TOKEN'])
    if (person != -1):
        person.update(token='')
    data = {
        'success': 1,
        'message': "Successfully logged off"
    }
    return JsonResponse(data, safe=True)

@require_http_methods(["POST"])
@csrf_exempt
def verify_student(request):
    person = validatePerson(request.META['HTTP_TOKEN'])
    if (person != -1):
        student = get_student_from_email(request.POST['email'])
        if (student == -1):
            data = {
                'success': 0,
                'message': "No student is associated with this email ID."
            }
        elif (student == -2):
            data = {
                'success': 0,
                'message': "This email ID is not registered with our system."
            }
        else:
            """if course_code is received check this student is enrolled to that course or not"""
            if ('course_code' in request.POST):
                course_code = request.POST['course_code']
                """find course"""
                course = Course.objects.filter(code=course_code)
                if (course.count() == 1):
                    """find student in registered course"""
                    person_object = Person.objects.get(email=request.POST['email'])
                    student_object = Student.objects.get(sId=person_object)
                    registered_course = RegisteredCourses.objects.filter(courseId=course[0], sId=student_object)
                    if (registered_course.count() == 1):
                        data = {
                            'success': 1,
                            'message': "Student is valid",
                            'data': {
                                'student': student
                            }
                        }
                    else:
                        data = {
                            'success': 0,
                            'message': person_object.name + " is not registered to course",
                            'data': {}
                        }
                else:
                    data = {
                        'success': 0,
                        'message': "Activity course is not valid",
                        'data': {}
                    }
            else:
                data = {
                    'success': 1,
                    'message': "Student is valid",
                    'data': {
                        'student': student
                    }
                }
    else:
        date = {
            'success': -99,
            'message': "Please login again",
        }
    return JsonResponse(data, safe=True)

def get_student_from_email(email):
    persons = Person.objects.filter(personType=2, email=email)
    if (persons.count() == 1):
        students = Student.objects.filter(sId=persons[0])
        if (students.count() == 1):
            return {
                'name': persons[0].name,
                'email': persons[0].email,
                'rollNo': students[0].rollNo,
            }
        else:
            return -1
    else:
        return -2



@require_http_methods(["POST"])
@csrf_exempt
def create_student_group(request):
    person = validatePerson(request.META['HTTP_TOKEN'])
    if (person != -1):
        group = Group(name="")
        try:
            group.save()
            emails = request.POST['emails'].split(',')
            for email in emails:
                student = get_student_from_email(email)
                if (student != -1):
                    sId = Student.objects.filter(rollNo=student['rollNo'])
                    groupDetail = GroupDetail(groupId=group, sId=sId[0])
                    groupDetail.save()

            if ('activity_code' in request.POST):
                """register group to activity"""
                data = register_group_to_activity_data(group.pk, request.POST['activity_code'])
                data['data'].update({
                    'groups': [{
                        'members': get_group_members(group),
                        'name': group.name,
                        'id': group.pk
                    }]
                })
            else:
                data = {
                    'success': 1,
                    'message': 'Group successfully created',
                    'data': {
                        'groups': [{
                            'members': get_group_members(group),
                            'name': group.name,
                            'id': group.pk
                        }]
                    }
                }
        except:
            data = {}
    else:
        date = {
            'success': -99,
            'message': "Please login again",
        }
    return JsonResponse(data, safe=True)

def get_group_members(group):
    groupDetail = GroupDetail.objects.filter(groupId=group)
    members = []
    for member in groupDetail:
        members.append({
            'name': member.sId.sId.name,
            'email': member.sId.sId.email,
            'rollNo': member.sId.rollNo,
        })
    return members

def validatePerson(token):
    if token != '':
        person = Person.objects.filter(token=token)
        if (person.count() == 1):
            return person
        else:
            return -1
    else:
        return -1

def validateInstructor(token):
    person = validatePerson(token)
    if person == -1:
        return -1
    instrutors = Instrutor.objects.filter(iId=person)
    if (instrutors.count() == 1):
        return instrutors
    else:
        return -1

def validateStudent(token):
    person = validatePerson(token)
    if person == -1:
        return -1
    students = Student.objects.filter(sId=person)
    if (students.count() == 1):
        return students
    else:
        return -1

def validateCourse(code):
    courses = Course.objects.filter(code=code)
    if (courses.count() == 1):
        return courses
    else:
        return -1

def getRandomString(length):
    char_set = string.ascii_uppercase + string.digits + string.ascii_lowercase
    return ''.join(random.sample(char_set*length, length))

def redirectToLogin():
    response = HttpResponseRedirect('/login/')
    response.delete_cookie('token')
    return response

def getInstructorCourses(iId):
    return Course.objects.filter(instructorId=iId)

def getStudentsInCourse(cId):
    return RegisteredCourses.objects.filter(courseId=cId)

def addStudentInCourse(student, courseCode):
    course = validateCourse(courseCode)
    if (course == -1):
        return -1
    else:
        """Check if already registered"""
        registeredCourse = RegisteredCourses.objects.filter(courseId=course[0], sId=student)
        if (registeredCourse.count() == 1):
            return registeredCourse[0]
        try:
            registeredCourse = RegisteredCourses(courseId=course[0], sId=student)
            registeredCourse.save()
            return registeredCourse
        except:
            return -1
