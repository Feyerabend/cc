from typing import List
from basic_tokenizer import Token
from basic_parser import ParseBasic

def create_parser(tokens: List[Token]) -> ParseBasic:
    return ParseBasic(tokens)
