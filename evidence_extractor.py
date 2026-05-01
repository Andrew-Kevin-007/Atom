import ast
import re

def extract_evidence(code: str, agent_role: str) -> list[dict]:
    try:
        tree = ast.parse(code)
    except Exception:
        return []

    evidence = []

    class EvidenceVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_function = None
            self.in_try_block = 0
            self.in_hasattr = 0

        def visit_FunctionDef(self, node):
            self.process_func(node)
            
        def visit_AsyncFunctionDef(self, node):
            self.process_func(node, is_async=True)

        def process_func(self, node, is_async=False):
            old_func = self.current_function
            self.current_function = node
            
            # ATLAS: Missing return annotation
            if agent_role == "ATLAS" and node.returns is None:
                evidence.append({
                    "evidence_type": "static_analysis",
                    "description": f"Function '{node.name}' lacks return type annotation.",
                    "line_number": node.lineno,
                    "severity": "low"
                })

            # ATLAS: Missing docstring
            if agent_role == "ATLAS":
                doc = ast.get_docstring(node)
                if not doc:
                    evidence.append({
                        "evidence_type": "static_analysis",
                        "description": f"Function '{node.name}' lacks a docstring.",
                        "line_number": node.lineno,
                        "severity": "low"
                    })

            # RIOT: Async without try/except
            if agent_role == "RIOT" and is_async:
                has_try = any(isinstance(stmt, ast.Try) for stmt in node.body)
                if not has_try:
                    evidence.append({
                        "evidence_type": "production_log",
                        "description": f"Async function '{node.name}' has no try/except block to catch failures.",
                        "line_number": node.lineno,
                        "severity": "high"
                    })

            self.generic_visit(node)
            self.current_function = old_func

        def visit_Try(self, node):
            self.in_try_block += 1
            for handler in node.handlers:
                # RIOT: Bare except
                if agent_role == "RIOT" and handler.type is None:
                    evidence.append({
                        "evidence_type": "production_log",
                        "description": "Bare except clause detected; may suppress critical failures.",
                        "line_number": handler.lineno,
                        "severity": "high"
                    })
            self.generic_visit(node)
            self.in_try_block -= 1

        def visit_Call(self, node):
            is_hasattr = isinstance(node.func, ast.Name) and node.func.id == "hasattr"
            if is_hasattr:
                self.in_hasattr += 1
            self.generic_visit(node)
            if is_hasattr:
                self.in_hasattr -= 1

        def visit_Attribute(self, node):
            # ATLAS: Unguarded attribute access
            if agent_role == "ATLAS":
                if self.in_try_block == 0 and self.in_hasattr == 0:
                    evidence.append({
                        "evidence_type": "contract_violation",
                        "description": f"Unguarded access to attribute '{node.attr}'.",
                        "line_number": node.lineno,
                        "severity": "medium"
                    })
            self.generic_visit(node)

        def visit_Return(self, node):
            # RIOT: Unhandled None returns / Implicit None
            if agent_role == "RIOT":
                is_none = False
                if node.value is None:
                    is_none = True
                elif isinstance(node.value, ast.Constant) and node.value.value is None:
                    is_none = True
                elif isinstance(node.value, ast.NameConstant) and node.value.value is None:
                    is_none = True
                
                if is_none:
                    evidence.append({
                        "evidence_type": "edge_case",
                        "description": "Function returns None explicitly, risk of NullPointer-style errors.",
                        "line_number": node.lineno,
                        "severity": "medium"
                    })
            self.generic_visit(node)

    visitor = EvidenceVisitor()
    visitor.visit(tree)
    
    return evidence
