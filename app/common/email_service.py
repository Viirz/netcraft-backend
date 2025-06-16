import requests
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('MAIL_SERVER_API_KEY')
        self.domain = os.environ.get('MAIL_SERVER_DOMAIN')
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}"
        
    def send_otp_email(self, to_email, first_name, otp_code):
        """Send OTP email to user"""
        if not self.api_key or not self.domain:
            logger.error("Email service not configured - missing API key or domain")
            return False
            
        subject = "NETCRAFT APP - Password Reset Code"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Password Reset Request</h2>
                
                <p>Hello {first_name},</p>
                
                <p>You have requested to reset your password for your NETCRAFT APP account.</p>
                
                <div style="background-color: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                    <h3 style="margin: 0; color: #495057;">Your verification code is:</h3>
                    <div style="font-size: 32px; font-weight: bold; color: #007bff; margin: 10px 0; letter-spacing: 3px;">
                        {otp_code}
                    </div>
                    <p style="margin: 0; font-size: 14px; color: #6c757d;">This code will expire in 15 minutes</p>
                </div>
                
                <p><strong>Important:</strong></p>
                <ul>
                    <li>Do not share this code with anyone</li>
                    <li>This code can only be used once</li>
                    <li>If you didn't request this reset, please ignore this email</li>
                </ul>
                
                <p>If you continue to have problems, please contact our support team.</p>
                
                <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
                <p style="font-size: 12px; color: #6c757d;">
                    This is an automated message from NETCRAFT API. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {first_name},

        You have requested to reset your password for your NETCRAFT API account.

        Your verification code is: {otp_code}

        This code will expire in 15 minutes.

        Important:
        - Do not share this code with anyone
        - This code can only be used once
        - If you didn't request this reset, please ignore this email

        If you continue to have problems, please contact our support team.

        This is an automated message from NETCRAFT API.
        """
        
        data = {
            "from": f"NETCRAFT API <noreply@{self.domain}>",
            "to": [to_email],
            "subject": subject,
            "text": text_content,
            "html": html_content
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                auth=("api", self.api_key),
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"OTP email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Email service error: {e}")
            return False
    
    def is_configured(self):
        """Check if email service is properly configured"""
        return bool(self.api_key and self.domain)

# Create a global instance
email_service = EmailService()