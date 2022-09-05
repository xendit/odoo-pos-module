# -*- coding: utf-8 -*-
from ast import In, Or
import base64
from operator import or_
from cryptography.fernet import Fernet
from os import path

# default key generation
key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

def generateKey():
    """
    Generates a key and save it into a file
    """
    if path.exists('secret.key') is False:
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

def loadKey():
    """
    Load the previously generated key
    """
    generateKey()
    return open("secret.key", "rb").read()

def generateFernet():
    key = loadKey()
    return Fernet(key)

def encrypt(str):
    fernet = generateFernet()
    return fernet.encrypt(str.encode())

def decrypt(str):
    """
    Decrypts an encrypted string
    """
    fernet = generateFernet()
    decryptedString = fernet.decrypt(bytes(str, 'utf-8'))
    return decryptedString.decode()