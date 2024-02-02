import pyotp
from django.core.mail import send_mail


def genarate_otp(email,password):
    totp = pyotp.TOTP(pyotp.random_base32())
    otp = totp.at(0)
    truncated_otp = str(otp)[:4] 

    # Send OTP via email
    send_mail(
        'OTP Verification',
        f'Your OTP is: {truncated_otp} \n and your password is: {password}',
        'sender@example.com',
        [email],  # Use user.email instead of undefined email variable
        fail_silently=False,
        )
    return truncated_otp

def sent_users_mail(email,content,title):

    # Send email this dynamic value
    send_mail(
        title,
        content,
        'sender@example.com',
        [email],  # user mail
        fail_silently=False,
        )
    return