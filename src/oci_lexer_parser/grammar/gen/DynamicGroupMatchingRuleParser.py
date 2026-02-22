# Generated from DynamicGroupMatchingRule.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,11,75,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,1,0,3,0,22,8,0,1,0,1,0,1,0,1,1,1,1,3,1,
        29,8,1,1,2,1,2,3,2,33,8,2,1,2,1,2,1,3,1,3,1,3,5,3,40,8,3,10,3,12,
        3,43,9,3,1,3,3,3,46,8,3,1,4,3,4,49,8,4,1,4,1,4,3,4,53,8,4,1,5,1,
        5,1,6,1,6,1,6,1,6,3,6,61,8,6,1,7,1,7,1,7,5,7,66,8,7,10,7,12,7,69,
        9,7,1,8,1,8,1,9,1,9,1,9,0,0,10,0,2,4,6,8,10,12,14,16,18,0,2,1,0,
        1,2,1,0,3,4,73,0,21,1,0,0,0,2,28,1,0,0,0,4,30,1,0,0,0,6,36,1,0,0,
        0,8,52,1,0,0,0,10,54,1,0,0,0,12,56,1,0,0,0,14,62,1,0,0,0,16,70,1,
        0,0,0,18,72,1,0,0,0,20,22,3,10,5,0,21,20,1,0,0,0,21,22,1,0,0,0,22,
        23,1,0,0,0,23,24,3,2,1,0,24,25,5,0,0,1,25,1,1,0,0,0,26,29,3,4,2,
        0,27,29,3,6,3,0,28,26,1,0,0,0,28,27,1,0,0,0,29,3,1,0,0,0,30,32,5,
        5,0,0,31,33,3,6,3,0,32,31,1,0,0,0,32,33,1,0,0,0,33,34,1,0,0,0,34,
        35,5,6,0,0,35,5,1,0,0,0,36,41,3,8,4,0,37,38,5,7,0,0,38,40,3,8,4,
        0,39,37,1,0,0,0,40,43,1,0,0,0,41,39,1,0,0,0,41,42,1,0,0,0,42,45,
        1,0,0,0,43,41,1,0,0,0,44,46,5,7,0,0,45,44,1,0,0,0,45,46,1,0,0,0,
        46,7,1,0,0,0,47,49,3,10,5,0,48,47,1,0,0,0,48,49,1,0,0,0,49,50,1,
        0,0,0,50,53,3,4,2,0,51,53,3,12,6,0,52,48,1,0,0,0,52,51,1,0,0,0,53,
        9,1,0,0,0,54,55,7,0,0,0,55,11,1,0,0,0,56,60,3,14,7,0,57,58,3,16,
        8,0,58,59,3,18,9,0,59,61,1,0,0,0,60,57,1,0,0,0,60,61,1,0,0,0,61,
        13,1,0,0,0,62,67,5,10,0,0,63,64,5,8,0,0,64,66,5,10,0,0,65,63,1,0,
        0,0,66,69,1,0,0,0,67,65,1,0,0,0,67,68,1,0,0,0,68,15,1,0,0,0,69,67,
        1,0,0,0,70,71,7,1,0,0,71,17,1,0,0,0,72,73,5,9,0,0,73,19,1,0,0,0,
        9,21,28,32,41,45,48,52,60,67
    ]

class DynamicGroupMatchingRuleParser ( Parser ):

    grammarFileName = "DynamicGroupMatchingRule.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "'!='", "'='", 
                     "'{'", "'}'", "','", "'.'" ]

    symbolicNames = [ "<INVALID>", "ALL", "ANY", "NEQ", "EQ", "LBRACE", 
                      "RBRACE", "COMMA", "DOT", "STRING", "IDENT", "WS" ]

    RULE_matchingRule = 0
    RULE_groupOrList = 1
    RULE_group = 2
    RULE_elementList = 3
    RULE_element = 4
    RULE_dgMode = 5
    RULE_predicate = 6
    RULE_path = 7
    RULE_op = 8
    RULE_literal = 9

    ruleNames =  [ "matchingRule", "groupOrList", "group", "elementList", 
                   "element", "dgMode", "predicate", "path", "op", "literal" ]

    EOF = Token.EOF
    ALL=1
    ANY=2
    NEQ=3
    EQ=4
    LBRACE=5
    RBRACE=6
    COMMA=7
    DOT=8
    STRING=9
    IDENT=10
    WS=11

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class MatchingRuleContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def groupOrList(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.GroupOrListContext,0)


        def EOF(self):
            return self.getToken(DynamicGroupMatchingRuleParser.EOF, 0)

        def dgMode(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.DgModeContext,0)


        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_matchingRule

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMatchingRule" ):
                listener.enterMatchingRule(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMatchingRule" ):
                listener.exitMatchingRule(self)




    def matchingRule(self):

        localctx = DynamicGroupMatchingRuleParser.MatchingRuleContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_matchingRule)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 21
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,0,self._ctx)
            if la_ == 1:
                self.state = 20
                self.dgMode()


            self.state = 23
            self.groupOrList()
            self.state = 24
            self.match(DynamicGroupMatchingRuleParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GroupOrListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def group(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.GroupContext,0)


        def elementList(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.ElementListContext,0)


        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_groupOrList

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterGroupOrList" ):
                listener.enterGroupOrList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitGroupOrList" ):
                listener.exitGroupOrList(self)




    def groupOrList(self):

        localctx = DynamicGroupMatchingRuleParser.GroupOrListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_groupOrList)
        try:
            self.state = 28
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 26
                self.group()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 27
                self.elementList()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GroupContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LBRACE(self):
            return self.getToken(DynamicGroupMatchingRuleParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(DynamicGroupMatchingRuleParser.RBRACE, 0)

        def elementList(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.ElementListContext,0)


        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_group

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterGroup" ):
                listener.enterGroup(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitGroup" ):
                listener.exitGroup(self)




    def group(self):

        localctx = DynamicGroupMatchingRuleParser.GroupContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_group)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 30
            self.match(DynamicGroupMatchingRuleParser.LBRACE)
            self.state = 32
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1062) != 0):
                self.state = 31
                self.elementList()


            self.state = 34
            self.match(DynamicGroupMatchingRuleParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElementListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def element(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(DynamicGroupMatchingRuleParser.ElementContext)
            else:
                return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.ElementContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(DynamicGroupMatchingRuleParser.COMMA)
            else:
                return self.getToken(DynamicGroupMatchingRuleParser.COMMA, i)

        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_elementList

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElementList" ):
                listener.enterElementList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElementList" ):
                listener.exitElementList(self)




    def elementList(self):

        localctx = DynamicGroupMatchingRuleParser.ElementListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_elementList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 36
            self.element()
            self.state = 41
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,3,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 37
                    self.match(DynamicGroupMatchingRuleParser.COMMA)
                    self.state = 38
                    self.element() 
                self.state = 43
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,3,self._ctx)

            self.state = 45
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7:
                self.state = 44
                self.match(DynamicGroupMatchingRuleParser.COMMA)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def group(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.GroupContext,0)


        def dgMode(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.DgModeContext,0)


        def predicate(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.PredicateContext,0)


        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_element

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElement" ):
                listener.enterElement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElement" ):
                listener.exitElement(self)




    def element(self):

        localctx = DynamicGroupMatchingRuleParser.ElementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_element)
        self._la = 0 # Token type
        try:
            self.state = 52
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1, 2, 5]:
                self.enterOuterAlt(localctx, 1)
                self.state = 48
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==1 or _la==2:
                    self.state = 47
                    self.dgMode()


                self.state = 50
                self.group()
                pass
            elif token in [10]:
                self.enterOuterAlt(localctx, 2)
                self.state = 51
                self.predicate()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DgModeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ALL(self):
            return self.getToken(DynamicGroupMatchingRuleParser.ALL, 0)

        def ANY(self):
            return self.getToken(DynamicGroupMatchingRuleParser.ANY, 0)

        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_dgMode

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDgMode" ):
                listener.enterDgMode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDgMode" ):
                listener.exitDgMode(self)




    def dgMode(self):

        localctx = DynamicGroupMatchingRuleParser.DgModeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_dgMode)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 54
            _la = self._input.LA(1)
            if not(_la==1 or _la==2):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PredicateContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def path(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.PathContext,0)


        def op(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.OpContext,0)


        def literal(self):
            return self.getTypedRuleContext(DynamicGroupMatchingRuleParser.LiteralContext,0)


        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_predicate

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPredicate" ):
                listener.enterPredicate(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPredicate" ):
                listener.exitPredicate(self)




    def predicate(self):

        localctx = DynamicGroupMatchingRuleParser.PredicateContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_predicate)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 56
            self.path()
            self.state = 60
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==3 or _la==4:
                self.state = 57
                self.op()
                self.state = 58
                self.literal()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PathContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENT(self, i:int=None):
            if i is None:
                return self.getTokens(DynamicGroupMatchingRuleParser.IDENT)
            else:
                return self.getToken(DynamicGroupMatchingRuleParser.IDENT, i)

        def DOT(self, i:int=None):
            if i is None:
                return self.getTokens(DynamicGroupMatchingRuleParser.DOT)
            else:
                return self.getToken(DynamicGroupMatchingRuleParser.DOT, i)

        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_path

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPath" ):
                listener.enterPath(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPath" ):
                listener.exitPath(self)




    def path(self):

        localctx = DynamicGroupMatchingRuleParser.PathContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_path)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 62
            self.match(DynamicGroupMatchingRuleParser.IDENT)
            self.state = 67
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==8:
                self.state = 63
                self.match(DynamicGroupMatchingRuleParser.DOT)
                self.state = 64
                self.match(DynamicGroupMatchingRuleParser.IDENT)
                self.state = 69
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OpContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EQ(self):
            return self.getToken(DynamicGroupMatchingRuleParser.EQ, 0)

        def NEQ(self):
            return self.getToken(DynamicGroupMatchingRuleParser.NEQ, 0)

        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_op

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOp" ):
                listener.enterOp(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOp" ):
                listener.exitOp(self)




    def op(self):

        localctx = DynamicGroupMatchingRuleParser.OpContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_op)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 70
            _la = self._input.LA(1)
            if not(_la==3 or _la==4):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LiteralContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(DynamicGroupMatchingRuleParser.STRING, 0)

        def getRuleIndex(self):
            return DynamicGroupMatchingRuleParser.RULE_literal

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLiteral" ):
                listener.enterLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLiteral" ):
                listener.exitLiteral(self)




    def literal(self):

        localctx = DynamicGroupMatchingRuleParser.LiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_literal)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 72
            self.match(DynamicGroupMatchingRuleParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





