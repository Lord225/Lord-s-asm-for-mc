import core.config as config
import core.error as error
import core.parse.tokenize as tokenize
from enum import Enum, auto
from typing import List

class TokenTypes(Enum):
    LITERAL_WORD = auto()
    ARGUMENT = auto()

def next_none(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return None

class Pattern:
    ARGUMENT_START_SYMBOL = '{'
    ARGUMENT_END_SYMBOL = '}'
    
    def __init__(self, pattern: str, argument_types: dict):
        self.arguments = dict()
        self.tokens = tokenize.remove_meaningless_tokens(tokenize.tokienize_line(pattern))
        self.tokens = self.__parse_tokens(argument_types)
    
    def match_expression(expr: List):
        pass
        
    def __get_token_str(self, id: int) -> str:
        try:
            return self.tokens[id]
        except IndexError:
            return None
    def __parse_tokens(self, argument_types: dict):
        i = 0
        processed_tokens = []
        while i < len(self.tokens):
            current_token = self.__get_token_str(i)
            next_token = self.__get_token_str(i+1)
            
            if current_token == Pattern.ARGUMENT_START_SYMBOL and next_token == Pattern.ARGUMENT_START_SYMBOL:
                i += 2 # seq: ['{', '{'], escaping
                processed_tokens.append((TokenTypes.LITERAL_WORD, Pattern.ARGUMENT_START_SYMBOL))
                continue

            if current_token == Pattern.ARGUMENT_END_SYMBOL and next_token == Pattern.ARGUMENT_END_SYMBOL:
                i += 2 # seq: ['}', '}'], escaping.
                processed_tokens.append((TokenTypes.LITERAL_WORD, Pattern.ARGUMENT_END_SYMBOL))
                continue

            if current_token == Pattern.ARGUMENT_START_SYMBOL:
                # seq: ['{', TOKEN, '}']
                close_token = self.__get_token_str(i+2)

                if close_token != Pattern.ARGUMENT_END_SYMBOL:
                    raise
                
                self.arguments[next_token] = len(processed_tokens)
                processed_tokens.append((TokenTypes.ARGUMENT, next_token, argument_types[next_token]))
                i += 2
            else:
                processed_tokens.append((TokenTypes.LITERAL_WORD, current_token)) #TODO FIX
                
            i += 1
        return processed_tokens
                
            



        
        
