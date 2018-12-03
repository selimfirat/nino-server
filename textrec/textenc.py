# Auxiliary classes representing different encodings of characters into natural numbers

def check(encoding, s):
    'Eliminate from string any character not handled by given encoding.'
    return ''.join(encoding.decode(c) for c in map(encoding.encode, s) if c != -1)

class Encoding:
    'Encodes any ASCII character into its 8-bit code'
    def __len__(self):
        return 128
    def encode(self, c):
        return ord(c)
    def decode(self, n):
        return chr(n)

class LowerEncoding(Encoding):
    def __len__(self):
        return 26
    def encode(self, c):
        c = c.lower()
        return ord(c) - ord('a') if c.isalpha() else -1
    def decode(self, n):
        return chr(n + ord('a'))

class LowerSpaceEncoding(Encoding):
    def __len__(self):
        return 27
    def encode(self, c):
        if c == ' ':
            return len(self) - 1
        c = c.lower()
        return ord(c) - ord('a') if c.isalpha() else -1
    def decode(self, n):
        if n == len(self) - 1:
            return ' '
        return chr(n + ord('a'))

class AlphaEncoding(Encoding):
    def __len__(self):
        return 52
    def encode(self, c):
        return 26*c.isupper() + ord(c.lower()) - ord('a') if c.isalpha() else -1
    def decode(self, n):
        c = chr(n % 26 + ord('a'))
        if n >= 26:
            c = c.upper()
        return c

class AlphaSpaceEncoding(Encoding):
    def __len__(self):
        return 53
    def encode(self, c):
        if c == ' ':
            return len(self) - 1
        return 26*c.isupper() + ord(c.lower()) - ord('a') if c.isalpha() else -1
    def decode(self, n):
        if n == len(self) - 1:
            return ' '
        c = chr(n % 26 + ord('a'))
        if n >= 26:
            c = c.upper()
        return c
    
encodings = {'all': Encoding,
             'lower': LowerEncoding, 
             'alpha': AlphaEncoding,
             'lowerspace': LowerSpaceEncoding,
             'alphaspace': AlphaSpaceEncoding}

