import base64
import hashlib
import secrets
import string
import requests
import json

CLIENT_ID = "73b22f6b7a47415598faf4b57c2f0f45"          # wprowadź Client_ID aplikacji
CLIENT_SECRET = "RQf9EiQVweReagQD7Ob2BKoKGwHX8hTndVB4pLSKOOeuVpVRnFjWOJtDepzlf51H"      # wprowadź Client_Secret aplikacji
REDIRECT_URI = "http://127.0.0.1:8000/"       # wprowadź redirect_uri
AUTH_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/authorize"
TOKEN_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/token"


def generate_code_verifier():
    code_verifier = ''.join((secrets.choice(string.ascii_letters) for i in range(40)))
    return code_verifier


def generate_code_challenge(code_verifier):
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    base64_encoded = base64.urlsafe_b64encode(hashed).decode('utf-8')
    code_challenge = base64_encoded.replace('=', '')
    return code_challenge


def get_authorization_code(code_verifier):
    code_challenge = generate_code_challenge(code_verifier)
    authorization_redirect_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}" \
                                 f"&code_challenge_method=S256&code_challenge={code_challenge}"
    print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
    print(f"--- {authorization_redirect_url} ---")
    authorization_code = input('code: ')
    return authorization_code


def get_access_token(authorization_code, code_verifier):
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code,
                'redirect_uri': REDIRECT_URI, 'code_verifier': code_verifier}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=False)
        response_body = json.loads(access_token_response.text)
        return response_body
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def main():
    code_verifier = generate_code_verifier()
    authorization_code = get_authorization_code(code_verifier)
    response = get_access_token(authorization_code, code_verifier)
    access_token = response['access_token']
    print(f"access token = {access_token}")


if __name__ == "__main__":
    main()