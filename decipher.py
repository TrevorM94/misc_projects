import re

def decipher_this(string):

    fully_deciphered = []

    for word in string.split():
        first_letter = chr(int(re.split('[a-zA-Z]+', word)[0]))
        letters = list(re.split('\d+', word)[1])
        if len(letters) > 1:
            letters[0], letters[-1] = letters[-1], letters[0]
        fully_deciphered.append(f'{first_letter}{"".join(letters)}')
    return " ".join(fully_deciphered)
        


print(decipher_this("65 119esi 111dl 111lw 108dvei 105n 97n 111ka")) #"A wise old owl lived in an oak"
