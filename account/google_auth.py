import requests
from django.conf import settings

def verify_google_id_token(id_token):
    """
    Verifies a Google ID Token using Google's tokeninfo API.
    Returns user info dict if valid, else None.
    """
    try:
        try:
            response = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': id_token},
                timeout=10
            )
        except requests.exceptions.SSLError:
            print("Google auth SSL verification failed. Retrying with verify=False...")
            response = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': id_token},
                timeout=10,
                verify=False
            )
        
        if response.status_code != 200:
            print("Google token verification failed. Status code:", response.status_code)
            return None
            
        token_info = response.json()
        
        # Ensure email is verified
        if token_info.get('email_verified') != 'true' and token_info.get('email_verified') is not True:
            print("Google email not verified.")
            return None
            
        return {
            'email': token_info.get('email'),
            'first_name': token_info.get('given_name', ''),
            'last_name': token_info.get('family_name', ''),
            'google_user_id': token_info.get('sub')
        }
    except Exception as e:
        print("Error verifying Google ID token:", e)
        return None
