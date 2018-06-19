import hashlib
from Crypto.Cipher import AES

# Generate key from password:
password = 'Micronaet'
key = hashlib.sha256(password).digest()
print 'Key used:', key
print 'Lungh.: ', len(key)
#key = '0123456789abcdef'
IV = 16 * '\x00'           # Initialization vector: discussed later
mode = AES.MODE_CBC
encryptor = AES.new(key, mode, IV=IV)

text = 'j' * 64 + 'i' * 128
ciphertext = encryptor.encrypt(text)
print '\nText: ', text, '\nCipher:', ciphertext


decryptor = AES.new(key, mode, IV=IV)
plain = decryptor.decrypt(ciphertext)
print '\nCipher:', ciphertext, '\nPlain: ', plain,

