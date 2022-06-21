import core.parse.tokenize as tokenize
from enum import Enum, auto

class TokenTypes(Enum):
    LITERAL_WORD = auto()
    ARGUMENT = auto()

class ArgumentTypes(Enum):
    NUM = auto()
    LABEL = auto()
    TOKEN = auto()
    OFFSET_LABEL = auto()
    HEX_NUM = auto()
    BIN_NUM = auto()
    DEC_NUM = auto()
    STRING = auto()

class Pattern:
    ARGUMENT_START_SYMBOL = '{'
    ARGUMENT_END_SYMBOL = '}'
    TOKEN_SEPARATOR_SYMBOL = ':'
    
    def __init__(self, pattern: str):
        self.arguments = dict()
        self.tokens = tokenize.remove_meaningless_tokens_list(tokenize.tokienize_str(pattern))
        self.tokens = self.__parse_tokens()
        
    def __get_token_str(self, id: int):
        try:
            return self.tokens[id]
        except IndexError:
            return None
    
    def summarize(self):
        return ' '.join((token[1] for token in self.tokens))

    def __parse_tokens(self):
        i = 0
        processed_tokens = []
        while i < len(self.tokens):
            current_token = self.__get_token_str(i)
            next_token = self.__get_token_str(i+1)
            
            if current_token == Pattern.ARGUMENT_START_SYMBOL and next_token == Pattern.ARGUMENT_START_SYMBOL:
                i += 2 # seq: ['{', '{'], escaping '{'
                processed_tokens.append((TokenTypes.LITERAL_WORD, Pattern.ARGUMENT_START_SYMBOL))
                continue

            if current_token == Pattern.ARGUMENT_END_SYMBOL and next_token == Pattern.ARGUMENT_END_SYMBOL:
                i += 2 # seq: ['}', '}'], escaping '}'
                processed_tokens.append((TokenTypes.LITERAL_WORD, Pattern.ARGUMENT_END_SYMBOL))
                continue

            if current_token == Pattern.ARGUMENT_START_SYMBOL:
                # new: seq: ['{', NAME, ':', TYPE, '}']
                
                name_token = self.__get_token_str(i+1)
                separator = self.__get_token_str(i+2)
                type_token = self.__get_token_str(i+3)
                close_token = self.__get_token_str(i+4)
                
                if close_token is None or close_token != Pattern.ARGUMENT_END_SYMBOL:
                    raise
                if type_token is None or type_token == Pattern.ARGUMENT_END_SYMBOL:
                    raise
                if separator is None or separator != Pattern.TOKEN_SEPARATOR_SYMBOL:
                    raise

                self.arguments[next_token] = len(processed_tokens)
                processed_tokens.append((TokenTypes.ARGUMENT, name_token, ArgumentTypes[type_token.upper()]))
                i += 4
            else:
                processed_tokens.append((TokenTypes.LITERAL_WORD, current_token))
                
            i += 1
        return processed_tokens
                
            



        
        
