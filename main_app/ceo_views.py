import json
import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView

from .forms import *
from .models import *

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from .models import LeaveReportManager
from .models import LeaveReportEmployee

def admin_home(request):
    total_manager = Manager.objects.all().count()
    total_employees = Employee.objects.all().count()
    departments = Department.objects.all()
    total_department = departments.count()
    total_division = Division.objects.all().count()
    attendance_list = Attendance.objects.filter(department__in=departments)
    total_attendance = attendance_list.count()
    attendance_list = []
    department_list = []
    for department in departments:
        attendance_count = Attendance.objects.filter(department=department).count()
        department_list.append(department.name[:7])
        attendance_list.append(attendance_count)
    context = {
        'page_title': "Administrative Dashboard",
        'total_employees': total_employees,
        'total_manager': total_manager,
        'total_division': total_division,
        'total_department': total_department,
        'department_list': department_list,
        'attendance_list': attendance_list

    }
    return render(request, 'ceo_template/home_content.html', context)


def add_manager(request):
    form = ManagerForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Manager'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            division = form.cleaned_data.get('division')
            passport = request.FILES.get('profile_pic')
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.manager.division = division
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_manager'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'ceo_template/add_manager_template.html', context)


def add_employee(request):
    employee_form = EmployeeForm(request.POST or None, request.FILES or None)
    context = {'form': employee_form, 'page_title': 'Add Employee'}
    
    # Handle AJAX request for departments based on division
    if request.method == 'GET' and 'division_id' in request.GET and 'action' in request.GET:
        division_id = request.GET.get('division_id')
        try:
            division = Division.objects.get(id=division_id)
            departments = Department.objects.filter(division=division)
            return JsonResponse({
                'departments': [{'id': dept.id, 'name': dept.name} for dept in departments]
            })
        except Division.DoesNotExist:
            return JsonResponse({'error': 'Division not found'}, status=404)
    
    if request.method == 'POST':
        if employee_form.is_valid():
            first_name = employee_form.cleaned_data.get('first_name')
            last_name = employee_form.cleaned_data.get('last_name')
            address = employee_form.cleaned_data.get('address')
            email = employee_form.cleaned_data.get('email')
            gender = employee_form.cleaned_data.get('gender')
            password = employee_form.cleaned_data.get('password')
            division = employee_form.cleaned_data.get('division')
            department = employee_form.cleaned_data.get('department')
            passport = request.FILES['profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.employee.division = division
                user.employee.department = department
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_employee'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: ")
    return render(request, 'ceo_template/add_employee_template.html', context)


def add_division(request):
    form = DivisionForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Division'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                division = Division()
                division.name = name
                division.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_division'))
            except:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'ceo_template/add_division_template.html', context)


def add_department(request):
    form = DepartmentForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Department'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            division = form.cleaned_data.get('division')
            try:
                department = Department()
                department.name = name
                department.division = division
                department.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_department'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'ceo_template/add_department_template.html', context)


def manage_manager(request):
    allManager = CustomUser.objects.filter(user_type=2)
    context = {
        'allManager': allManager,
        'page_title': 'Manage Manager'
    }
    return render(request, "ceo_template/manage_manager.html", context)


def manage_employee(request):
    employees = CustomUser.objects.filter(user_type=3)
    context = {
        'employees': employees,
        'page_title': 'Manage Employees'
    }
    return render(request, "ceo_template/manage_employee.html", context)


def manage_division(request):
    divisions = Division.objects.all()
    context = {
        'divisions': divisions,
        'page_title': 'Manage Divisions'
    }
    return render(request, "ceo_template/manage_division.html", context)


def manage_department(request):
    departments = Department.objects.all()
    context = {
        'departments': departments,
        'page_title': 'Manage Departments'
    }
    return render(request, "ceo_template/manage_department.html", context)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from main_app.models import Manager, CustomUser  # Adjust based on your models
from main_app.forms import ManagerForm  # Adjust based on your forms

def edit_manager(request, manager_id):
    manager = get_object_or_404(Manager, id=manager_id)
    form = ManagerForm(request.POST or None, request.FILES or None, instance=manager)
    context = {
        'form': form,
        'manager_id': manager_id,
        'page_title': 'Edit Manager'
    }

    if request.method == 'POST':
        if form.is_valid():
            try:
                # Extract cleaned data
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                address = form.cleaned_data.get('address')
                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')
                gender = form.cleaned_data.get('gender')
                password = form.cleaned_data.get('password') or None
                division = form.cleaned_data.get('division')
                passport = request.FILES.get('profile_pic') or None

                # Update the associated user
                user = manager.admin  # Access related CustomUser via ForeignKey
                user.username = username
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address

                # Handle password update
                if password:
                    user.set_password(password)

                # Handle profile picture upload
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    user.profile_pic = fs.url(filename)

                # Save updates to user and manager
                user.save()
                manager.division = division
                manager.save()

                # Success message and redirect
                messages.success(request, "Manager details successfully updated.")
                return redirect(reverse('edit_manager', args=[manager_id]))

            except Exception as e:
                # Handle any unexpected errors
                messages.error(request, f"Could not update manager: {e}")
        else:
            # Provide error feedback for invalid form
            messages.error(request, "Please correct the highlighted errors below.")

    # Render the form with context (GET or POST with errors)
    return render(request, "ceo_template/edit_manager_template.html", context)



def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    form = EmployeeForm(request.POST or None, instance=employee)
    context = {
        'form': form,
        'employee_id': employee_id,
        'page_title': 'Edit Employee'
    }
    
    # Handle AJAX request for departments based on division
    if request.method == 'GET' and 'division_id' in request.GET and 'action' in request.GET:
        division_id = request.GET.get('division_id')
        try:
            division = Division.objects.get(id=division_id)
            departments = Department.objects.filter(division=division)
            return JsonResponse({
                'departments': [{'id': dept.id, 'name': dept.name} for dept in departments]
            })
        except Division.DoesNotExist:
            return JsonResponse({'error': 'Division not found'}, status=404)
    
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            division = form.cleaned_data.get('division')
            department = form.cleaned_data.get('department')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=employee.admin.id)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                employee.division = division
                employee.department = department
                user.save()
                employee.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_employee', args=[employee_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "ceo_template/edit_employee_template.html", context)


def edit_division(request, division_id):
    instance = get_object_or_404(Division, id=division_id)
    form = DivisionForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'division_id': division_id,
        'page_title': 'Edit Division'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                division = Division.objects.get(id=division_id)
                division.name = name
                division.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'ceo_template/edit_division_template.html', context)


def edit_department(request, department_id):
    instance = get_object_or_404(Department, id=department_id)
    form = DepartmentForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'department_id': department_id,
        'page_title': 'Edit Department'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            division = form.cleaned_data.get('division')
            try:
                department = Department.objects.get(id=department_id)
                department.name = name
                department.division = division
                department.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_department', args=[department_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'ceo_template/edit_department_template.html', context)


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


@csrf_exempt
def employee_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackEmployee.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Employee Feedback Messages'
        }
        return render(request, 'ceo_template/employee_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackEmployee, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def manager_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackManager.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Manager Feedback Messages'
        }
        return render(request, 'ceo_template/manager_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackManager, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def view_manager_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportManager.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Manager'
        }
        return render(request, "ceo_template/manager_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportManager, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
def view_employee_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportEmployee.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Employees'
        }
        return render(request, "ceo_template/employee_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportEmployee, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


def admin_view_attendance(request):
    departments = Department.objects.all()
    context = {
        'departments': departments,
        'page_title': 'View Attendance'
    }

    return render(request, "ceo_template/admin_view_attendance.html", context)


@csrf_exempt
def get_admin_attendance(request):
    department_id = request.POST.get('department')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        department = get_object_or_404(Department, id=department_id)
        attendance = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_reports = AttendanceReport.objects.filter(attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status": str(report.status),
                "name": str(report.employee)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None


def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "ceo_template/admin_view_profile.html", context)


def admin_notify_manager(request):
    manager = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Manager",
        'allManager': manager
    }
    return render(request, "ceo_template/manager_notification.html", context)


def admin_notify_employee(request):
    employee = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Employees",
        'employees': employee
    }
    return render(request, "ceo_template/employee_notification.html", context)


@csrf_exempt
def send_employee_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    employee = get_object_or_404(Employee, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "OfficeOps",
                'body': message,
                'click_action': reverse('employee_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': employee.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationEmployee(employee=employee, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
def send_manager_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    manager = get_object_or_404(Manager, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "OfficeOps",
                'body': message,
                'click_action': reverse('manager_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': manager.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationManager(manager=manager, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def delete_manager(request, manager_id):
    manager = get_object_or_404(CustomUser, manager__id=manager_id)
    manager.delete()
    messages.success(request, "Manager deleted successfully!")
    return redirect(reverse('manage_manager'))


def delete_employee(request, employee_id):
    employee = get_object_or_404(CustomUser, employee__id=employee_id)
    employee.delete()
    messages.success(request, "Employee deleted successfully!")
    return redirect(reverse('manage_employee'))


def delete_division(request, division_id):
    division = get_object_or_404(Division, id=division_id)
    try:
        division.delete()
        messages.success(request, "Division deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some employees are assigned to this division already. Kindly change the affected employee division and try again")
    return redirect(reverse('manage_division'))


def delete_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    department.delete()
    messages.success(request, "Department deleted successfully!")
    return redirect(reverse('manage_department'))




@csrf_exempt  # Temporarily disable CSRF for debugging (remove in production)
def view_manager_leave(request):
    if request.method == "POST":
        # Debugging: Print POST data
        print("POST data:", request.POST)

        # Get leave ID and status from the POST request
        leave_id = request.POST.get("id")
        status = request.POST.get("status")

        # Debugging: Print leave ID and status
        print("Leave ID:", leave_id, "Status:", status)

        # Validate leave ID and status
        if not leave_id or not status:
            return JsonResponse("False", safe=False)

        try:
            # Fetch the leave request from the database
            leave = get_object_or_404(LeaveReportManager, id=leave_id)

            # Update the leave status
            leave.status = int(status)
            leave.save()

            # Define the email subject and message based on the status
            if leave.status == 1:
                subject = "Leave Request Approved ✅"
                message = f"Dear {leave.manager.admin.first_name},\n\nYour leave request for {leave.date} has been **approved** by the Admin.\n\nBest regards,\nHR Team"
            elif leave.status == -1:
                subject = "Leave Request Denied ❌"
                message = f"Dear {leave.manager.admin.first_name},\n\nYour leave request for {leave.date} has been **denied** by the Admin.\n\nPlease contact HR for more details.\n\nBest regards,\nHR Team"
            else:
                return JsonResponse("False", safe=False)

            # Send email notification to the manager
            try:
                send_mail(
                    subject,
                    message,
                    "alpen750@gmail.com",  # Replace with your sender email
                    [leave.manager.admin.email],  # Send email to the manager
                    fail_silently=False,
                )
                return JsonResponse("True", safe=False)
            except Exception as e:
                print(f"Error sending email: {e}")  # Debugging: Print email error
                return JsonResponse("False", safe=False)
        except Exception as e:
            print(f"Error processing leave request: {e}")  # Debugging: Print general error
            return JsonResponse("False", safe=False)
    else:
        # Handle GET request (render the leave requests page)
        allLeave = LeaveReportManager.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Manager'
        }
        return render(request, "ceo_template/manager_leave_view.html", context)
    
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import LeaveReportEmployee
from django.conf import settings

def view_employee_leave(request):
    if request.method == "GET":
        # ✅ Handle GET request to display leave requests in the admin panel
        allLeave = LeaveReportEmployee.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Employees'
        }
        return render(request, "ceo_template/employee_leave_view.html", context)

    elif request.method == "POST":
        # ✅ Handle POST request to approve/reject leave and send email
        leave_id = request.POST.get("id")
        status = request.POST.get("status")

        try:
            leave = LeaveReportEmployee.objects.get(id=leave_id)
        except LeaveReportEmployee.DoesNotExist:
            return JsonResponse({"status": "False", "message": "Leave request not found"}, safe=False)

        if status not in ['1', '-1']:
            return JsonResponse({"status": "False", "message": "Invalid status value"}, safe=False)

        # Update leave status
        leave.status = int(status)
        leave.save()

        # Define email content
        if leave.status == 1:
            subject = "Leave Request Approved ✅"
            message = f"Dear {leave.employee.admin.first_name},\n\nYour leave request for {leave.date} has been **approved** by the Admin.\n\nBest regards,\nHR Team"
        else:
            subject = "Leave Request Rejected ❌"
            message = f"Dear {leave.employee.admin.first_name},\n\nYour leave request for {leave.date} has been **rejected** by the Admin.\n\nPlease contact HR for more details.\n\nBest regards,\nHR Team"

        # Send email notification
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # Use email from settings
                [leave.employee.admin.email],  # Send email to employee
                fail_silently=False,
            )
        except Exception as e:
            return JsonResponse({"status": "False", "message": f"Error sending email: {e}"}, safe=False)

        return JsonResponse({"status": "True", "message": "Leave status updated and email sent successfully"}, safe=False)

    else:
        return JsonResponse({"status": "False", "message": "Invalid request method"}, safe=False)
    


# from django.shortcuts import render
# from django.http import JsonResponse, HttpResponse
# from django.template.loader import get_template
# from xhtml2pdf import pisa
# from django.conf import settings
# import os
# from datetime import datetime
# from employee.models import Employee, Attendance, Task
# from django.contrib.auth.decorators import login_required
# from main_app.decorators import ceo_required

# @login_required
# @ceo_required
# def ceo_rank_report(request):
#     if request.method == 'POST':
#         month = request.POST.get('month')
#         year = request.POST.get('year')
        
#         try:
#             # Get all employees
#             employees = Employee.objects.all()
#             employee_rankings = []
            
#             for employee in employees:
#                 # Calculate attendance metrics
#                 attendances = Attendance.objects.filter(
#                     employee=employee,
#                     date__year=year,
#                     date__month=month
#                 )
                
#                 total_days = attendances.count()
#                 present_days = attendances.filter(status=True).count()
#                 absent_days = total_days - present_days
#                 attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
                
#                 # Calculate task metrics
#                 tasks = Task.objects.filter(
#                     employee=employee,
#                     deadline__year=year,
#                     deadline__month=month
#                 )
                
#                 total_tasks = tasks.count()
#                 completed_tasks = tasks.filter(status='Completed').count()
#                 average_rating = tasks.aggregate(Avg('rating'))['rating__avg'] or 0
                
#                 # Calculate score (customize this formula as needed)
#                 score = (attendance_percentage * 0.4) + (average_rating * 20 * 0.6)
                
#                 employee_rankings.append({
#                     'employee': employee,
#                     'present_days': present_days,
#                     'absent_days': absent_days,
#                     'attendance_percentage': attendance_percentage,
#                     'total_tasks': total_tasks,
#                     'completed_tasks': completed_tasks,
#                     'average_rating': average_rating,
#                     'score': score
#                 })
            
#             # Sort employees by score (descending)
#             employee_rankings.sort(key=lambda x: x['score'], reverse=True)
            
#             # Generate PDF
#             template = get_template('ceo_rank_report_pdf.html')
#             context = {
#                 'employee_rankings': employee_rankings,
#                 'month': datetime.strptime(month, "%m").strftime("%B"),
#                 'year': year,
#                 'generated_on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             }
#             html = template.render(context)
            
#             # Create PDF
#             response = HttpResponse(content_type='application/pdf')
#             filename = f"CEO_Rank_Report_{month}_{year}.pdf"
#             response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
#             # Generate PDF
#             pisa_status = pisa.CreatePDF(html, dest=response)
#             if pisa_status.err:
#                 return HttpResponse('Error generating CEO report')
            
#             # Save PDF to media directory
#             pdf_path = os.path.join(settings.MEDIA_ROOT, 'ceo_reports', filename)
#             os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
#             with open(pdf_path, 'wb') as pdf_file:
#                 pisa.CreatePDF(html, dest=pdf_file)
            
#             return response
            
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})
    
#     # GET request - show form
#     current_month = datetime.now().month
#     current_year = datetime.now().year
#     months = [
#         (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
#         (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
#         (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
#     ]
#     years = range(datetime.now().year - 5, datetime.now().year + 1)
    
#     return render(request, 'ceo/ceo_rank_report.html', {
#         'months': months,
#         'years': reversed(years),  # Show recent years first
#         'current_month': current_month,
#         'current_year': current_year
#     })
