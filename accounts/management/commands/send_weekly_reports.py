import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import get_connection, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import SubjectEnrollment, Attendance

# Run every Monday 8AM:
# 0 8 * * 1 python manage.py send_weekly_reports

class Command(BaseCommand):
    help = 'Sends a weekly attendance report to all students.'

    def handle(self, *args, **kwargs):
        # Calculate date range for the previous week (Monday to Sunday)
        today = timezone.now().date()
        # If running on Monday, today.weekday() is 0. 
        # So start_date is today - 7 days.
        days_since_monday = today.weekday()
        start_date = today - timedelta(days=days_since_monday + 7)
        end_date = start_date + timedelta(days=6)
        
        date_range_str = f"{start_date.strftime('%d %b')} to {end_date.strftime('%d %b')}"
        subject_line = f"📊 Weekly Report — {date_range_str}"

        students = User.objects.filter(is_staff=False, is_active=True).exclude(email="")
        
        self.stdout.write(f"Preparing weekly reports for {students.count()} students for {date_range_str}...")

        emails_to_send = []

        for student in students:
            # Get enrolled subjects
            enrollments = SubjectEnrollment.objects.filter(student=student).select_related('subject')
            subjects = [e.subject for e in enrollments]
            
            if not subjects:
                continue

            weekly_text_lines = []
            cumulative_text_lines = []
            
            weekly_html_lines = []
            cumulative_html_lines = []

            total_weekly_present = 0
            total_weekly_lectures = 0

            for subj in subjects:
                subj_display = f"[{subj.course_code}] {subj.name}" if subj.course_code else subj.name
                subj_code_display = f"[{subj.course_code}]" if subj.course_code else f"[{subj.name[:5]}]"

                # Cumulative calculation
                all_atts = Attendance.objects.filter(student=student, session__subject=subj)
                cum_total = all_atts.count()
                cum_present = all_atts.filter(status=True).count()
                
                if cum_total > 0:
                    cum_pct = round((cum_present / cum_total) * 100)
                    if cum_pct < 75:
                        cum_icon = "❌ CRITICAL"
                        cum_html_color = "#ef4444"
                    else:
                        cum_icon = "✅ GOOD"
                        cum_html_color = "#10b981"
                        
                    cumulative_text_lines.append(f"{subj_code_display}: {cum_pct}% {cum_icon}")
                    cumulative_html_lines.append(f"<tr><td style='padding: 8px; border-bottom: 1px solid #e2e8f0;'><strong>{subj_code_display}</strong></td><td style='padding: 8px; border-bottom: 1px solid #e2e8f0; color: {cum_html_color}; font-weight: bold;'>{cum_pct}% {cum_icon}</td></tr>")
                else:
                    cumulative_text_lines.append(f"{subj_code_display}: N/A")
                    cumulative_html_lines.append(f"<tr><td style='padding: 8px; border-bottom: 1px solid #e2e8f0;'><strong>{subj_code_display}</strong></td><td style='padding: 8px; border-bottom: 1px solid #e2e8f0; color: #64748b;'>N/A</td></tr>")

                # Weekly calculation
                week_atts = all_atts.filter(session__date__date__gte=start_date, session__date__date__lte=end_date)
                w_total = week_atts.count()
                w_present = week_atts.filter(status=True).count()
                
                if w_total > 0:
                    total_weekly_present += w_present
                    total_weekly_lectures += w_total
                    w_pct = round((w_present / w_total) * 100)
                    w_icon = "⚠️" if w_pct < 75 else "✅"
                    w_color = "#ef4444" if w_pct < 75 else "#10b981"
                    
                    weekly_text_lines.append(f"{subj_display}: {w_present}/{w_total} ({w_pct}%) {w_icon}")
                    weekly_html_lines.append(f"<tr><td style='padding: 8px; border-bottom: 1px solid #e2e8f0;'>{subj_display}</td><td style='padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;'><strong style='color: {w_color};'>{w_present}/{w_total} ({w_pct}%) {w_icon}</strong></td></tr>")

            if total_weekly_lectures == 0 and not cumulative_text_lines:
                # No attendance data at all, skip sending an empty email
                continue

            if total_weekly_lectures > 0:
                overall_weekly_pct = round((total_weekly_present / total_weekly_lectures) * 100)
                overall_text = f"Overall this week: {total_weekly_present}/{total_weekly_lectures} ({overall_weekly_pct}%)"
                overall_html = f"<div style='background: #f8fafc; padding: 15px; border-radius: 8px; margin-top: 15px; text-align: center; font-size: 16px;'>Overall this week: <strong>{total_weekly_present}/{total_weekly_lectures} ({overall_weekly_pct}%)</strong></div>"
            else:
                overall_text = "No lectures were held/recorded for you this week."
                overall_html = f"<div style='background: #f8fafc; padding: 15px; border-radius: 8px; margin-top: 15px; text-align: center; font-size: 16px; color: #64748b;'>No lectures were held/recorded for you this week.</div>"
                weekly_text_lines.append("No active sessions this week.")
                weekly_html_lines.append("<tr><td colspan='2' style='padding: 8px; color: #64748b; text-align: center;'>No active sessions this week.</td></tr>")

            name = student.first_name if student.first_name else student.username
            
            # Build plain text
            text_body = f"Dear {name},\n\nYour attendance this week:\n\n"
            text_body += "\n".join(weekly_text_lines)
            text_body += f"\n\n{overall_text}\n\nCumulative attendance:\n"
            text_body += "\n".join(cumulative_text_lines)
            text_body += "\n\n— LookIn AI"

            # Build HTML
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="background: #3b82f6; padding: 20px; text-align: center;">
                    <h2 style="color: white; margin: 0; letter-spacing: 1px;">Weekly Attendance Report</h2>
                    <p style="color: #e0e7ff; margin: 5px 0 0 0; font-size: 14px;">{date_range_str}</p>
                </div>
                <div style="padding: 30px; background: #ffffff;">
                    <p style="font-size: 16px; color: #334155;">Dear <strong>{name}</strong>,</p>
                    <p style="font-size: 15px; color: #475569; margin-bottom: 15px;">Your attendance this week:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
                        <tbody>
                            {"".join(weekly_html_lines)}
                        </tbody>
                    </table>
                    
                    {overall_html}
                    
                    <h3 style="color: #334155; margin-top: 30px; margin-bottom: 15px; font-size: 16px;">Cumulative attendance:</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tbody>
                            {"".join(cumulative_html_lines)}
                        </tbody>
                    </table>
                    
                    <p style="font-size: 14px; color: #64748b; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                        Contact your faculty if you observe any discrepancies.<br>— LookIn AI
                    </p>
                </div>
            </div>
            """

            msg = EmailMultiAlternatives(subject_line, text_body, settings.EMAIL_HOST_USER, [student.email])
            msg.attach_alternative(html_body, "text/html")
            emails_to_send.append(msg)

        if not emails_to_send:
            self.stdout.write(self.style.WARNING("No emails to send."))
            return

        self.stdout.write(f"Dispatching {len(emails_to_send)} emails...")

        # Send in chunks to avoid SMTP limits
        BATCH_SIZE = 10
        BATCH_DELAY = 5
        
        total_sent = 0
        total_failed = 0

        chunks = [emails_to_send[i:i + BATCH_SIZE] for i in range(0, len(emails_to_send), BATCH_SIZE)]

        for batch_num, chunk in enumerate(chunks, start=1):
            try:
                connection = get_connection(fail_silently=False)
                connection.send_messages(chunk)
                total_sent += len(chunk)
                self.stdout.write(f"Batch {batch_num}/{len(chunks)} sent OK.")
            except Exception as e:
                total_failed += len(chunk)
                self.stdout.write(self.style.ERROR(f"Batch {batch_num} failed: {str(e)}"))

            if batch_num < len(chunks):
                time.sleep(BATCH_DELAY)

        self.stdout.write(self.style.SUCCESS(f"Done! {total_sent} sent, {total_failed} failed."))
