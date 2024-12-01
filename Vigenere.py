import sys
from Encryption import Encryption

class VigenereCipher(Encryption):
    mod = 26  # The modulus used in the Vigenere cipher
    key = None  # The encryption key for Vigenere Cipher
    
    def __init__(self, keyValue, 
                 modValue=26, 
                 removeSpace=True,          # Remove spaces in text
                 encryptSpace=False,        # Encrypt spaces as symbols
                 encryptSymbol=False,       # Encrypt symbols
                 upperCaseAll=True,         # Convert all text to uppercase
                 reverseText=False          # Reverse the text before encrypting
                 ) -> None:
        super().__init__(removeSpace, encryptSpace, encryptSymbol, upperCaseAll, reverseText)
        self.mod = modValue  # Set the modulus for encryption

        if not keyValue:
            print("Error: You need to provide a key.")
            sys.exit()        
        self.key = keyValue  # Set the encryption key
        self.name = "Vigenere Cipher"  # Set the name for the cipher
    
    def encrypt(self, plainText):
        cleaned_plainText, indexToSkip = self.applySettings(plainText)  # Apply settings like space removal, case, etc.
        cipherText = ""  # Initialize the ciphertext string

        for i, char in enumerate(cleaned_plainText):  # Loop through each character in the cleaned text
            if i not in indexToSkip:  # Skip characters that should not be encrypted (e.g., spaces or symbols)
                sub = chr(((ord(char.upper()) + ord(self.key[i % len(self.key)].upper())) % self.mod) + ord('A'))  # Encryption logic
                if char.islower():  # Preserve original case
                    cipherText += sub.lower() 
                else:
                    cipherText += sub
            else:
                cipherText += char  # Preserve spaces or non-alphabetic characters as is
        return cipherText
    
    def decrypt(self, cipherText):
        cleaned_cipherText, indexToSkip = self.applySettings(cipherText)  # Apply settings like space removal, case, etc.
        plainText = ""  # Initialize the plaintext string

        for i, char in enumerate(cleaned_cipherText):  # Loop through each character in the cleaned ciphertext
            if i not in indexToSkip:  # Skip characters that should not be decrypted (e.g., spaces or symbols)
                sub = chr(((ord(char.upper()) - ord(self.key[i % len(self.key)].upper())) % self.mod) + ord('A'))  # Decryption logic
                if char.islower():  # Preserve original case
                    plainText += sub.lower() 
                else:
                    plainText += sub
            else:
                plainText += char  # Preserve spaces or non-alphabetic characters as is
        return plainText
