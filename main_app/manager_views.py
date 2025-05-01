import json
from datetime import datetime
import calendar

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *
from .models import Task, Employee, Manager
from .forms import TaskForm



def manager_home(request):
    manager = get_object_or_404(Manager, admin=request.user)
    total_employees = Employee.objects.filter(division=manager.division).count()
    total_leave = LeaveReportManager.objects.filter(manager=manager).count()
    departments = Department.objects.filter(division=manager.division)
    total_department = departments.count()
    attendance_list = Attendance.objects.filter(department__in=departments)
    total_attendance = attendance_list.count()
    attendance_list = []
    department_list = []
    for department in departments:
        attendance_count = Attendance.objects.filter(department=department).count()
        department_list.append(department.name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Manager Panel - ' + str(manager.admin.last_name) + ' (' + str(manager.division) + ')',
        'total_employees': total_employees,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_department': total_department,
        'department_list': department_list,
        'attendance_list': attendance_list
    }
    return render(request, 'manager_template/home_content.html', context)


def manager_take_attendance(request):
    manager = get_object_or_404(Manager, admin=request.user)
    departments = Department.objects.filter(division=manager.division)
    context = {
        'departments': departments,
        'page_title': 'Take Attendance'
    }

    return render(request, 'manager_template/manager_take_attendance.html', context)


@csrf_exempt
def get_employees(request):
    if request.method == 'POST':
        department_id = request.POST.get('department')
        try:
            department = get_object_or_404(Department, id=department_id)
            # Get employees that belong to the department's division
            employees = Employee.objects.filter(division=department.division)
            employee_list = []
            for employee in employees:
                employee_data = {
                    'id': employee.id,
                    'name': f"{employee.admin.last_name}, {employee.admin.first_name}"
                }
                employee_list.append(employee_data)
            return JsonResponse(employee_list, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse([], safe=False)



@csrf_exempt
def save_attendance(request):
    employee_data = request.POST.get('employee_ids')
    date = request.POST.get('date')
    department_id = request.POST.get('department')
    employees = json.loads(employee_data)
    try:
        department = get_object_or_404(Department, id=department_id)

        # Check if an attendance object already exists for the given date
        attendance, created = Attendance.objects.get_or_create(department=department, date=date)

        for employee_dict in employees:
            employee = get_object_or_404(Employee, id=employee_dict.get('id'))

            # Check if an attendance report already exists for the employee and the attendance object
            attendance_report, report_created = AttendanceReport.objects.get_or_create(employee=employee, attendance=attendance)

            # Update the status only if the attendance report was newly created
            if report_created:
                attendance_report.status = employee_dict.get('status')
                attendance_report.save()

    except Exception as e:
        return None

    return HttpResponse("OK")


def manager_update_attendance(request):
    manager = get_object_or_404(Manager, admin=request.user)
    departments = Department.objects.filter(division=manager.division)
    context = {
        'departments': departments,
        'page_title': 'Update Attendance'
    }

    return render(request, 'manager_template/manager_update_attendance.html', context)


@csrf_exempt
def get_employee_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        employee_data = []
        for attendance in attendance_data:
            data = {"id": attendance.employee.admin.id,
                    "name": attendance.employee.admin.last_name + " " + attendance.employee.admin.first_name,
                    "status": attendance.status}
            employee_data.append(data)
        return JsonResponse(json.dumps(employee_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    employee_data = request.POST.get('employee_ids')
    date = request.POST.get('date')
    employees = json.loads(employee_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for employee_dict in employees:
            employee = get_object_or_404(
                Employee, admin_id=employee_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, employee=employee, attendance=attendance)
            attendance_report.status = employee_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def manager_apply_leave(request):
    form = LeaveReportManagerForm(request.POST or None)
    manager = get_object_or_404(Manager, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportManager.objects.filter(manager=manager),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.manager = manager
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('manager_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "manager_template/manager_apply_leave.html", context)


def manager_feedback(request):
    form = FeedbackManagerForm(request.POST or None)
    manager = get_object_or_404(Manager, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackManager.objects.filter(manager=manager),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.manager = manager
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('manager_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "manager_template/manager_feedback.html", context)


def manager_view_profile(request):
    manager = get_object_or_404(Manager, admin=request.user)
    form = ManagerEditForm(request.POST or None, request.FILES or None,instance=manager)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = manager.admin
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
                manager.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('manager_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "manager_template/manager_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "manager_template/manager_view_profile.html", context)

    return render(request, "manager_template/manager_view_profile.html", context)


@csrf_exempt
def manager_fcmtoken(request):
    token = request.POST.get('token')
    try:
        manager_user = get_object_or_404(CustomUser, id=request.user.id)
        manager_user.fcm_token = token
        manager_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def manager_view_notification(request):
    manager = get_object_or_404(Manager, admin=request.user)
    notifications = NotificationManager.objects.filter(manager=manager)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "manager_template/manager_view_notification.html", context)


def manager_add_salary(request):
    manager = get_object_or_404(Manager, admin=request.user)
    departments = Department.objects.filter(division=manager.division)
    context = {
        'page_title': 'Add Employee Salary',
        'departments': departments
    }
    return render(request, 'manager_template/manager_add_salary.html', context)


@csrf_exempt
def fetch_employee_salary(request):
    if request.method == 'POST':
        department_id = request.POST.get('department')
        employee_id = request.POST.get('employee')
        
        try:
            if department_id:
                # Get all salaries for employees in this department's division
                department = get_object_or_404(Department, id=department_id)
                salaries = Salary.objects.filter(
                    employee__division=department.division
                ).select_related('employee', 'employee__admin').order_by('-month_year')
                
                salary_list = []
                for salary in salaries:
                    try:
                        leave_payment = 0
                        # Handle case where leave_payment column might not exist yet
                        try:
                            if hasattr(salary, 'leave_payment') and salary.leave_payment is not None:
                                leave_payment = float(salary.leave_payment)
                        except (AttributeError, TypeError):
                            leave_payment = 0
                            
                        salary_data = {
                            'id': salary.id,  # Include salary ID
                            'employee_id': salary.employee.id,  # Include employee ID
                            'employee_name': f"{salary.employee.admin.last_name}, {salary.employee.admin.first_name}",
                            'month_year': salary.month_year.strftime('%Y-%m-%d'),
                            'basic_salary': float(salary.basic_salary),
                            'meal_allowance': float(salary.meal_allowance),
                            'medical_allowance': float(salary.medical_allowance),
                            'transportation_allowance': float(salary.transportation_allowance),
                            'leave_payment': leave_payment,
                            'tax_amount': float(salary.tax_amount),
                            'insurance_amount': float(salary.insurance_amount),
                            'total_earnings': float(salary.total_earnings),
                            'total_deductions': float(salary.total_deductions),
                            'net_salary': float(salary.net_salary),
                            'status': salary.status
                        }
                        salary_list.append(salary_data)
                    except Exception as e:
                        print(f"Error processing salary {salary.id}: {str(e)}")
                        continue
                
                return JsonResponse({
                    'success': True,
                    'salaries': salary_list,
                    'message': None if salary_list else 'No salary records found for this department'
                })
            
            elif employee_id:
                # Get single employee salary
                try:
                    salary = Salary.objects.filter(employee_id=employee_id).latest('month_year')
                    
                    # Handle case where leave_payment column might not exist yet
                    leave_payment = 0
                    try:
                        if hasattr(salary, 'leave_payment') and salary.leave_payment is not None:
                            leave_payment = float(salary.leave_payment)
                    except (AttributeError, TypeError):
                        leave_payment = 0
                        
                    data = {
                        'success': True,
                        'salary': {
                            'basic_salary': float(salary.basic_salary),
                            'meal_allowance': float(salary.meal_allowance),
                            'medical_allowance': float(salary.medical_allowance),
                            'transportation_allowance': float(salary.transportation_allowance),
                            'leave_payment': leave_payment,
                            'tax_amount': float(salary.tax_amount),
                            'insurance_amount': float(salary.insurance_amount),
                            'total_earnings': float(salary.total_earnings),
                            'total_deductions': float(salary.total_deductions),
                            'net_salary': float(salary.net_salary)
                        }
                    }
                    return JsonResponse(data)
                except Salary.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'No salary record found for this employee'
                    })
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Either department_id or employee_id is required'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

@csrf_exempt
def save_salary(request):
    if request.method == 'POST':
        try:
            data = request.POST
            employee = get_object_or_404(Employee, id=data.get('employee'))
            month_year = data.get('month_year') + "-01"  # Add day to make a valid date
            
            # Check if the employee already has a paid salary for this month
            existing_salary = Salary.objects.filter(
                employee=employee,
                month_year=month_year,
                status='paid'
            ).first()
            
            if existing_salary:
                # Format month/year from the existing salary for readability
                formatted_date = existing_salary.month_year.strftime('%B %Y')
                
                # Get employee name
                employee_name = f"{employee.admin.last_name}, {employee.admin.first_name}"
                
                return JsonResponse({
                    'success': False,
                    'message': f'ALERT: {employee_name} already has a PAID salary record for {formatted_date}. Cannot add duplicate entry.',
                    'details': {
                        'employee_id': employee.id,
                        'employee_name': employee_name,
                        'month_year': formatted_date,
                        'status': existing_salary.status,
                        'payment_date': existing_salary.payment_date.strftime('%d-%m-%Y') if existing_salary.payment_date else 'Not set'
                    }
                }, status=400)
            
            # Validate numeric fields
            basic_salary = float(data.get('basic_salary', 0))
            meal_allowance = float(data.get('meal_allowance', 0))
            medical_allowance = float(data.get('medical_allowance', 0))
            transportation_allowance = float(data.get('transportation_allowance', 0))
            leave_payment = float(data.get('leave_payment', 0)) if data.get('leave_payment') else None
            
            if basic_salary <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Basic salary must be greater than 0'
                }, status=400)
            
            try:
                # Try to create or update salary record with leave_payment
                salary, created = Salary.objects.update_or_create(
                    employee=employee,
                    month_year=month_year,
                    defaults={
                        'basic_salary': basic_salary,
                        'meal_allowance': meal_allowance,
                        'medical_allowance': medical_allowance,
                        'transportation_allowance': transportation_allowance,
                        'leave_payment': leave_payment,
                        'tax_percentage': 13,  # Default tax percentage
                        'insurance_percentage': 5,  # Default insurance percentage
                        'status': 'pending'  # Default status
                    }
                )
            except Exception as e:
                # If there was an error (likely due to missing leave_payment column),
                # try again without leave_payment
                if "leave_payment" in str(e).lower():
                    salary, created = Salary.objects.update_or_create(
                        employee=employee,
                        month_year=month_year,
                        defaults={
                            'basic_salary': basic_salary,
                            'meal_allowance': meal_allowance,
                            'medical_allowance': medical_allowance,
                            'transportation_allowance': transportation_allowance,
                            'tax_percentage': 13,  # Default tax percentage
                            'insurance_percentage': 5,  # Default insurance percentage
                            'status': 'pending'  # Default status
                        }
                    )
                else:
                    # If it's some other error, re-raise it
                    raise
            
            # Calculate all values
            salary.refresh_from_db()
            
            # Manually set leave_payment if it doesn't exist in the DB
            if not hasattr(salary, 'leave_payment'):
                salary.leave_payment = leave_payment
            
            # Compute leave_payment value for response
            leave_payment_value = 0
            if hasattr(salary, 'leave_payment') and salary.leave_payment is not None:
                leave_payment_value = float(salary.leave_payment)
            
            # Return success response with the saved salary data
            return JsonResponse({
                'success': True,
                'message': 'Salary saved successfully',
                'salary': {
                    'employee_name': f"{employee.admin.last_name}, {employee.admin.first_name}",
                    'month_year': salary.month_year.strftime('%Y-%m-%d'),
                    'basic_salary': float(salary.basic_salary),
                    'meal_allowance': float(salary.meal_allowance),
                    'medical_allowance': float(salary.medical_allowance),
                    'transportation_allowance': float(salary.transportation_allowance),
                    'leave_payment': leave_payment_value,
                    'tax_amount': float(salary.tax_amount),
                    'insurance_amount': float(salary.insurance_amount),
                    'total_earnings': float(salary.total_earnings),
                    'total_deductions': float(salary.total_deductions),
                    'net_salary': float(salary.net_salary),
                    'status': salary.status
                }
            })
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Employee not found'
            }, status=404)
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': 'Invalid salary amount. Please enter valid numbers.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to save salary: {str(e)}'
            }, status=400)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

def manager_assign_task(request):
    manager = get_object_or_404(Manager, admin=request.user)
    employees = Employee.objects.filter(division=manager.division)

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.manager = manager
            task.save()
            messages.success(request, "Task assigned successfully!")
            return redirect('manager_view_tasks')
    else:
        form = TaskForm()

    context = {'form': form, 'employees': employees}
    return render(request, 'manager_template/assign_task.html', context)

def manager_view_tasks(request):
    manager = get_object_or_404(Manager, admin=request.user)
    tasks = Task.objects.filter(manager=manager)

    context = {'tasks': tasks}
    return render(request, 'manager_template/view_tasks.html', context)

def update_task_rating(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        rating = request.POST.get("rating")
        task = get_object_or_404(Task, id=task_id)

        # Save rating in database
        task.rating = int(rating)
        task.save()

        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

@csrf_exempt
def update_salary_status(request):
    if request.method == 'POST':
        try:
            salary_id = request.POST.get('salary_id')
            new_status = request.POST.get('status')
            
            # Validate status
            if new_status not in ['pending', 'paid']:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid status value'
                }, status=400)
            
            # Find and update the salary record
            salary = get_object_or_404(Salary, id=salary_id)
            
            # Update status and payment date if paid
            salary.status = new_status
            if new_status == 'paid':
                salary.payment_date = datetime.now().date()
            else:
                salary.payment_date = None
            
            salary.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Status updated successfully'
            })
            
        except Salary.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Salary record not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to update status: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

@csrf_exempt
def delete_salary(request):
    if request.method == 'POST':
        try:
            salary_id = request.POST.get('salary_id')
            
            # Get the salary record
            salary = get_object_or_404(Salary, id=salary_id)
            
            # Check if the salary is already paid
            if salary.status == 'paid':
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot delete PAID salary record for {salary.employee.admin.last_name}, {salary.employee.admin.first_name} ({salary.month_year.strftime("%B %Y")})'
                }, status=400)
            
            # Store info for response
            employee_name = f"{salary.employee.admin.last_name}, {salary.employee.admin.first_name}"
            month_year = salary.month_year.strftime('%B %Y')
            
            # Delete the salary record
            salary.delete()
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': f'Salary record for {employee_name} ({month_year}) deleted successfully',
                'employee_name': employee_name,
                'month_year': month_year
            })
            
        except Salary.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Salary record not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to delete salary: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

@csrf_exempt
def get_employee_stats(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        month_year = request.POST.get('month_year')
        
        try:
            employee = get_object_or_404(Employee, id=employee_id)
            
            # Parse the month_year string to datetime
            date_parts = month_year.split('-')
            year = int(date_parts[0])
            month = int(date_parts[1])
            
            # Get the first and last day of the month
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, calendar.monthrange(year, month)[1])
            
            # Get attendance records for the month
            attendances = Attendance.objects.filter(
                date__gte=first_day,
                date__lte=last_day,
                department=employee.department
            )
            
            # Count present days
            present_count = AttendanceReport.objects.filter(
                attendance__in=attendances,
                employee=employee,
                status=True
            ).count()
            
            # Count absent days
            absent_count = AttendanceReport.objects.filter(
                attendance__in=attendances,
                employee=employee,
                status=False
            ).count()
            
            # Get approved leave count
            leave_count = LeaveReportEmployee.objects.filter(
                employee=employee,
                status=1,  # Approved leave
                created_at__year=year,
                created_at__month=month
            ).count()
            
            # Get total working days in the month
            total_attendance_days = attendances.count()
            
            # Calculate attendance percentage
            attendance_percentage = 0
            if total_attendance_days > 0:
                attendance_percentage = round((present_count / total_attendance_days) * 100)
            
            return JsonResponse({
                'success': True,
                'stats': {
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'leave_count': leave_count,
                    'total_days': total_attendance_days,
                    'attendance_percentage': attendance_percentage
                }
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

