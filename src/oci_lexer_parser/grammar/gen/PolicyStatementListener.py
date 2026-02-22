# Generated from PolicyStatement.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .PolicyStatementParser import PolicyStatementParser
else:
    from PolicyStatementParser import PolicyStatementParser

# This class defines a complete listener for a parse tree produced by PolicyStatementParser.
class PolicyStatementListener(ParseTreeListener):

    # Enter a parse tree produced by PolicyStatementParser#statements.
    def enterStatements(self, ctx:PolicyStatementParser.StatementsContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#statements.
    def exitStatements(self, ctx:PolicyStatementParser.StatementsContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#statement.
    def enterStatement(self, ctx:PolicyStatementParser.StatementContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#statement.
    def exitStatement(self, ctx:PolicyStatementParser.StatementContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#allowStmt.
    def enterAllowStmt(self, ctx:PolicyStatementParser.AllowStmtContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#allowStmt.
    def exitAllowStmt(self, ctx:PolicyStatementParser.AllowStmtContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#effect.
    def enterEffect(self, ctx:PolicyStatementParser.EffectContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#effect.
    def exitEffect(self, ctx:PolicyStatementParser.EffectContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#AnyGroup.
    def enterAnyGroup(self, ctx:PolicyStatementParser.AnyGroupContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#AnyGroup.
    def exitAnyGroup(self, ctx:PolicyStatementParser.AnyGroupContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#AnyUser.
    def enterAnyUser(self, ctx:PolicyStatementParser.AnyUserContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#AnyUser.
    def exitAnyUser(self, ctx:PolicyStatementParser.AnyUserContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#ServiceSubject.
    def enterServiceSubject(self, ctx:PolicyStatementParser.ServiceSubjectContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#ServiceSubject.
    def exitServiceSubject(self, ctx:PolicyStatementParser.ServiceSubjectContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#GroupByName.
    def enterGroupByName(self, ctx:PolicyStatementParser.GroupByNameContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#GroupByName.
    def exitGroupByName(self, ctx:PolicyStatementParser.GroupByNameContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#GroupById.
    def enterGroupById(self, ctx:PolicyStatementParser.GroupByIdContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#GroupById.
    def exitGroupById(self, ctx:PolicyStatementParser.GroupByIdContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#DynGroupByName.
    def enterDynGroupByName(self, ctx:PolicyStatementParser.DynGroupByNameContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#DynGroupByName.
    def exitDynGroupByName(self, ctx:PolicyStatementParser.DynGroupByNameContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#DynGroupById.
    def enterDynGroupById(self, ctx:PolicyStatementParser.DynGroupByIdContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#DynGroupById.
    def exitDynGroupById(self, ctx:PolicyStatementParser.DynGroupByIdContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#verb.
    def enterVerb(self, ctx:PolicyStatementParser.VerbContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#verb.
    def exitVerb(self, ctx:PolicyStatementParser.VerbContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#resource.
    def enterResource(self, ctx:PolicyStatementParser.ResourceContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#resource.
    def exitResource(self, ctx:PolicyStatementParser.ResourceContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#LocTenancy.
    def enterLocTenancy(self, ctx:PolicyStatementParser.LocTenancyContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#LocTenancy.
    def exitLocTenancy(self, ctx:PolicyStatementParser.LocTenancyContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#LocCompartmentId.
    def enterLocCompartmentId(self, ctx:PolicyStatementParser.LocCompartmentIdContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#LocCompartmentId.
    def exitLocCompartmentId(self, ctx:PolicyStatementParser.LocCompartmentIdContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#LocCompartmentName.
    def enterLocCompartmentName(self, ctx:PolicyStatementParser.LocCompartmentNameContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#LocCompartmentName.
    def exitLocCompartmentName(self, ctx:PolicyStatementParser.LocCompartmentNameContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#compartmentPath.
    def enterCompartmentPath(self, ctx:PolicyStatementParser.CompartmentPathContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#compartmentPath.
    def exitCompartmentPath(self, ctx:PolicyStatementParser.CompartmentPathContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#nameList.
    def enterNameList(self, ctx:PolicyStatementParser.NameListContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#nameList.
    def exitNameList(self, ctx:PolicyStatementParser.NameListContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#idList.
    def enterIdList(self, ctx:PolicyStatementParser.IdListContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#idList.
    def exitIdList(self, ctx:PolicyStatementParser.IdListContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#qualifiedName.
    def enterQualifiedName(self, ctx:PolicyStatementParser.QualifiedNameContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#qualifiedName.
    def exitQualifiedName(self, ctx:PolicyStatementParser.QualifiedNameContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#name.
    def enterName(self, ctx:PolicyStatementParser.NameContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#name.
    def exitName(self, ctx:PolicyStatementParser.NameContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#ocid.
    def enterOcid(self, ctx:PolicyStatementParser.OcidContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#ocid.
    def exitOcid(self, ctx:PolicyStatementParser.OcidContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#defineStmt.
    def enterDefineStmt(self, ctx:PolicyStatementParser.DefineStmtContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#defineStmt.
    def exitDefineStmt(self, ctx:PolicyStatementParser.DefineStmtContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#defineTarget.
    def enterDefineTarget(self, ctx:PolicyStatementParser.DefineTargetContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#defineTarget.
    def exitDefineTarget(self, ctx:PolicyStatementParser.DefineTargetContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#admitStmt.
    def enterAdmitStmt(self, ctx:PolicyStatementParser.AdmitStmtContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#admitStmt.
    def exitAdmitStmt(self, ctx:PolicyStatementParser.AdmitStmtContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#endorseStmt.
    def enterEndorseStmt(self, ctx:PolicyStatementParser.EndorseStmtContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#endorseStmt.
    def exitEndorseStmt(self, ctx:PolicyStatementParser.EndorseStmtContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#endorseVerb.
    def enterEndorseVerb(self, ctx:PolicyStatementParser.EndorseVerbContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#endorseVerb.
    def exitEndorseVerb(self, ctx:PolicyStatementParser.EndorseVerbContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#endorseScope.
    def enterEndorseScope(self, ctx:PolicyStatementParser.EndorseScopeContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#endorseScope.
    def exitEndorseScope(self, ctx:PolicyStatementParser.EndorseScopeContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#conditionExpr.
    def enterConditionExpr(self, ctx:PolicyStatementParser.ConditionExprContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#conditionExpr.
    def exitConditionExpr(self, ctx:PolicyStatementParser.ConditionExprContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#conditionGroup.
    def enterConditionGroup(self, ctx:PolicyStatementParser.ConditionGroupContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#conditionGroup.
    def exitConditionGroup(self, ctx:PolicyStatementParser.ConditionGroupContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#CondEq.
    def enterCondEq(self, ctx:PolicyStatementParser.CondEqContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#CondEq.
    def exitCondEq(self, ctx:PolicyStatementParser.CondEqContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#CondIn.
    def enterCondIn(self, ctx:PolicyStatementParser.CondInContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#CondIn.
    def exitCondIn(self, ctx:PolicyStatementParser.CondInContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#CondBefore.
    def enterCondBefore(self, ctx:PolicyStatementParser.CondBeforeContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#CondBefore.
    def exitCondBefore(self, ctx:PolicyStatementParser.CondBeforeContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#CondAfter.
    def enterCondAfter(self, ctx:PolicyStatementParser.CondAfterContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#CondAfter.
    def exitCondAfter(self, ctx:PolicyStatementParser.CondAfterContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#CondBetween.
    def enterCondBetween(self, ctx:PolicyStatementParser.CondBetweenContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#CondBetween.
    def exitCondBetween(self, ctx:PolicyStatementParser.CondBetweenContext):
        pass


    # Enter a parse tree produced by PolicyStatementParser#condValue.
    def enterCondValue(self, ctx:PolicyStatementParser.CondValueContext):
        pass

    # Exit a parse tree produced by PolicyStatementParser#condValue.
    def exitCondValue(self, ctx:PolicyStatementParser.CondValueContext):
        pass



del PolicyStatementParser