import json
import math
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *


def employee_home(request):
    employee = get_object_or_404(Employee, admin=request.user)
    total_department = Department.objects.filter(division=employee.division).count()
    total_attendance = AttendanceReport.objects.filter(employee=employee).count()
    total_present = AttendanceReport.objects.filter(employee=employee, status=True).count()
    if total_attendance == 0:  # Don't divide. DivisionByZero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present/total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    department_name = []
    data_present = []
    data_absent = []
    departments = Department.objects.filter(division=employee.division)
    for department in departments:
        attendance = Attendance.objects.filter(department=department)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, employee=employee).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, employee=employee).count()
        department_name.append(department.name)
        data_present.append(present_count)
        data_absent.append(absent_count)
    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_department': total_department,
        'departments': departments,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': department_name,
        'page_title': 'Employee Homepage'

    }
    return render(request, 'employee_template/home_content.html', context)


@ csrf_exempt
def employee_view_attendance(request):
    employee = get_object_or_404(Employee, admin=request.user)
    if request.method != 'POST':
        division = get_object_or_404(Division, id=employee.division.id)
        context = {
            'departments': Department.objects.filter(division=division),
            'page_title': 'View Attendance'
        }
        return render(request, 'employee_template/employee_view_attendance.html', context)
    else:
        department_id = request.POST.get('department')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            department = get_object_or_404(Department, id=department_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), department=department)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, employee=employee)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date":  str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            return None


def employee_apply_leave(request):
    form = LeaveReportEmployeeForm(request.POST or None)
    employee = get_object_or_404(Employee, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportEmployee.objects.filter(employee=employee),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.employee = employee
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('employee_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "employee_template/employee_apply_leave.html", context)


def employee_feedback(request):
    form = FeedbackEmployeeForm(request.POST or None)
    employee = get_object_or_404(Employee, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackEmployee.objects.filter(employee=employee),
        'page_title': 'Employee Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.employee = employee
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('employee_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "employee_template/employee_feedback.html", context)


def employee_view_profile(request):
    employee = get_object_or_404(Employee, admin=request.user)
    form = EmployeeEditForm(request.POST or None, request.FILES or None,
                           instance=employee)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = employee.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                employee.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('employee_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "employee_template/employee_view_profile.html", context)


@csrf_exempt
def employee_fcmtoken(request):
    token = request.POST.get('token')
    employee_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        employee_user.fcm_token = token
        employee_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def employee_view_notification(request):
    employee = get_object_or_404(Employee, admin=request.user)
    notifications = NotificationEmployee.objects.filter(employee=employee)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "employee_template/employee_view_notification.html", context)


def employee_view_salary(request):
    employee = get_object_or_404(Employee, admin=request.user)
    try:
        # Get the current month and year
        current_date = datetime.now()
        current_month_year = current_date.replace(day=1)
        
        # Get the latest salary record
        salary = Salary.objects.filter(employee=employee).latest('month_year')
        
        # Check if leave_payment attribute exists
        if hasattr(salary, 'leave_payment'):
            # Check if leave_payment is None, set it to 0 for template rendering
            if salary.leave_payment is None:
                salary.leave_payment = 0
        else:
            # If leave_payment doesn't exist in the model (due to migration issues),
            # add it as a property to the instance
            salary.leave_payment = 0
        
        # Check if salary is already paid for current month
        is_paid = Salary.objects.filter(
            employee=employee,
            month_year__year=current_date.year,
            month_year__month=current_date.month,
            status='paid'
        ).exists()
        
    except Salary.DoesNotExist:
        salary = None
        is_paid = False
    
    # Format employee data
    employee_data = {
        'name': f"{employee.admin.last_name}, {employee.admin.first_name}",
        'id': employee.id,
        'department': employee.department.name if employee.department else 'Not Assigned'
    }
    
    context = {
        'employee': employee,
        'employee_data': employee_data,
        'salary': salary,
        'is_paid': is_paid,
        'current_month': current_date.strftime('%B %Y'),
        'page_title': 'My Salary'
    }
    return render(request, 'employee_template/employee_view_salary.html', context)

def employee_view_tasks(request):
    employee = get_object_or_404(Employee, admin=request.user)
    tasks = Task.objects.filter(employee=employee)

    context = {
        'tasks': tasks,
        'page_title': 'My Tasks'
    }
    return render(request, 'employee_template/view_tasks.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Task, Employee

def employee_home(request):
    employee = get_object_or_404(Employee, admin=request.user)
    task_count = Task.objects.filter(employee=employee, status="Pending").count()  # Only count pending tasks

    context = {
        "page_title": "Employee Dashboard",
        "task_count": task_count,  # Pass task count to the template
    }
    return render(request, "employee_template/home_content.html", context)

from django.http import JsonResponse

def employee_task_count(request):
    employee = get_object_or_404(Employee, admin=request.user)
    task_count = Task.objects.filter(employee=employee, status="Pending").count()
    
    return JsonResponse({"task_count": task_count})

from django.http import JsonResponse # type: ignore
from django.shortcuts import get_object_or_404 # type: ignore
from .models import Task
from django.core.files.storage import FileSystemStorage # type: ignore

# Update Task Status
def update_task_status(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        new_status = request.POST.get("status")
        task = get_object_or_404(Task, id=task_id)
        task.status = new_status
        task.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

# Upload Task File
def upload_task_file(request):
    if request.method == "POST" and request.FILES.get("task_file"):
        task_id = request.POST.get("task_id")
        task = get_object_or_404(Task, id=task_id)

        # Save file
        file = request.FILES["task_file"]
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        task.file = fs.url(filename)  # Save file URL in database
        task.save()

        return JsonResponse({"success": True, "file_url": task.file.url})
    return JsonResponse({"success": False})



# from django.shortcuts import render
# from django.http import JsonResponse, HttpResponse
# from django.template.loader import get_template
# from xhtml2pdf import pisa
# from django.conf import settings
# import os
# from datetime import datetime
# from employee.models import Attendance, Task
# from django.contrib.auth.decorators import login_required
# from main_app.decorators import employee_required

# @login_required
# @employee_required
# def employee_rank_report(request):
#     if request.method == 'POST':
#         month = request.POST.get('month')
#         year = request.POST.get('year')
        
#         try:
#             employee = request.user.employee
            
#             # Calculate attendance metrics
#             attendances = Attendance.objects.filter(
#                 employee=employee,
#                 date__year=year,
#                 date__month=month
#             )
            
#             total_days = attendances.count()
#             present_days = attendances.filter(status=True).count()
#             absent_days = total_days - present_days
#             attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
#             # Calculate task metrics
#             tasks = Task.objects.filter(
#                 employee=employee,
#                 deadline__year=year,
#                 deadline__month=month
#             )
            
#             total_tasks = tasks.count()
#             completed_tasks = tasks.filter(status='Completed').count()
#             average_rating = tasks.aggregate(Avg('rating'))['rating__avg'] or 0
            
#             # Generate PDF
#             template = get_template('employee/employee_rank_report_pdf.html')
#             context = {
#                 'employee': employee,
#                 'present_days': present_days,
#                 'absent_days': absent_days,
#                 'attendance_percentage': attendance_percentage,
#                 'total_tasks': total_tasks,
#                 'completed_tasks': completed_tasks,
#                 'average_rating': average_rating,
#                 'month': datetime.strptime(month, "%m").strftime("%B"),
#                 'year': year,
#                 'generated_on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             }
#             html = template.render(context)
            
#             # Create PDF
#             response = HttpResponse(content_type='application/pdf')
#             filename = f"Employee_Rank_Report_{employee.id}_{month}_{year}.pdf"
#             response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
#             # Generate PDF
#             pisa_status = pisa.CreatePDF(html, dest=response)
#             if pisa_status.err:
#                 return HttpResponse('Error generating employee report')
            
#             # Save PDF to media directory
#             pdf_path = os.path.join(settings.MEDIA_ROOT, 'employee_reports', filename)
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
    
#     return render(request, 'employee/employee_rank_report.html', {
#         'months': months,
#         'years': reversed(years),  # Show recent years first
#         'current_month': current_month,
#         'current_year': current_year
#     })

