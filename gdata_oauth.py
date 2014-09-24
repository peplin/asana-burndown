import gdata.gauth
import os

Client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
Client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
Scope='https://spreadsheets.google.com/feeds/'
User_agent='myself'

token = gdata.gauth.OAuth2Token(client_id=Client_id,
        client_secret=Client_secret,scope=Scope,user_agent=User_agent)
print(token.generate_authorize_url(redirect_uri='urn:ietf:wg:oauth:2.0:oob'))
code = raw_input('What is the verification code? ').strip()
token.get_access_token(code)
print("Refresh token\n")
print(token.refresh_token)
print("Access Token\n")
print(token.access_token)
