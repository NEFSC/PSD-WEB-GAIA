"""
Security module for authentication with Earth Explorer and Maxar Geospatial Portal.
This module provides functions for authenticating with Earth Explorer and Maxar Geospatial Portal (MGP).
It handles login, token generation, storage and refresh functionality.
Functions:
    ee_login(session, username, password): Authenticates with Earth Explorer
    auth_local(username, password): Generates MGP bearer token and stores locally 
    refresh_local(refresh_token): Refreshes MGP access token
    mgp_login(username, password): Main MGP authentication handler
File contents are stored in user's home directory to prevent accidental exposure of credentials.
Dependencies:
    requests - For making HTTP requests
    json - For JSON parsing/writing
    pathlib - For cross-platform file path handling 
    os - For file operations
    time - For token expiration checks
    jwt - For JWT token decoding
References:
    Earth Explorer authentication based on:
    https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L90-L104
"""

import requests

import json
from pathlib import Path
import os
import time
import jwt

def ee_login(session, username, password):
    """ Logs a user into Earth Explorer after they provide
            their username and password. Returns the session
            with their authorization token imbeded in the
            header.

        SESSION - A session
        USERNAME - The end-user's username
        PASSWORD - The end-user's password

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L90-L104
    """
    payload = {"username": username, "password": password}
    
    url = "https://m2m.cr.usgs.gov/api/api/json/stable/login"
    
    r = session.post(url, json.dumps(payload))
    session.headers["X-Auth-Token"] = r.json().get("data")

    return session

def auth_local(username, password):
    """ When provided with a username and password, generates
             a JSON file containing the bearer token.

        USERNAME - User's Maxar Geospatial Portal username
        PASSWORD - User's Maxar Geospatial Portal password
    """
    
    config_path = Path.joinpath(Path.home(), "mgp_token.json")
    
    url = "https://account.maxar.com/auth/realms/mds/protocol/openid-connect/token"
    
    payload = {
        "client_id": "mgp",
        "username": username,
        "password": password,
        "grant_type": "password",
        "scope": "openid",
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        refresh_token = response.json()["refresh_token"]
        decoded = jwt.decode(response.json()["access_token"],options={"verify_signature":False})
        auth_json = {"expiration":decoded["exp"],"bearer_token": access_token, "refresh_token": refresh_token}
        with open(config_path, "w") as outfile:
            print("Writing file now!") # Added by JWX
            outfile.write(json.dumps(auth_json, indent=2))
    
    else:
        print(
            f"Failed to get Access Token with status code {response.status_code} & error {response.text}"
        )

def refresh_local(refresh_token):
    """ Refreshes the access token. """
    
    config_path = Path.joinpath(Path.home(), "mgp_token.json")
    
    url = "https://account.maxar.com/auth/realms/mds/protocol/openid-connect/token"
    
    payload = {
        "client_id": "mgp",
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "scope": "openid",
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        refresh_token = response.json()["refresh_token"]
        decoded = jwt.decode(response.json()["access_token"],options={"verify_signature":False})
        auth_json = {"expiration":decoded["exp"],"bearer_token": access_token, "refresh_token": refresh_token}
        with open(config_path, "w") as outfile:
            outfile.write(json.dumps(auth_json, indent=2))
    
    else:
        print(
            f"Failed to get Access Token with status code {response.status_code} & error {response.text}"
        )

def mgp_login(username, password):
    """ Generates a JSON file containing the bearer token using the
             user name and password. Stores this token file under
             the users home directory so it wont acidentally be
             uploaded to GitHub.
    """
    config_path = Path.joinpath(Path.home(), "mgp_token.json")
    
    if os.path.exists(config_path):
        with open(config_path) as jsonfile:
            data = json.load(jsonfile)
            if not "bearer_token" and "refresh_token" in data:
                auth_local(username,password)
            elif os.path.exists(config_path) and float(data["expiration"])>float(time.time()):
                bearer_token = data["bearer_token"]
                refresh_token = data["refresh_token"]
                refresh_local(refresh_token)
            elif os.path.exists(config_path) and float(data["expiration"])<float(time.time()):
                auth_local(username,password)
    
    elif not os.path.exists(config_path):
        print("File does not exist. Making it now.")
        auth_local(username, password)
    
    with open(config_path) as jsonfile:
        data = json.load(jsonfile)
        auth = {
            "Authorization": "Bearer {}".format(data["bearer_token"]),
            "content-type": "application/json",
        }
        
    return auth