import ast
import operator
import re

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}


def clean_expression(question: str) -> str:
    expression = question.lower()

    replacements = {
        "multiplied by": "*",
        "times": "*",
        "divided by": "/",
        "plus": "+",
        "minus": "-",
        "modulo": "%",
    }

    for text, symbol in replacements.items():
        expression = expression.replace(text, symbol)

    expression = re.sub(r"[^0-9+\-*/%().\s]", " ", expression)

    # Keep decimal points inside numeric literals, but discard sentence
    # punctuation at the end of natural-language prompts (for example,
    # "What is 2 + 2? Reply with only the number.").
    expression = re.sub(r"[.\s]+$", "", expression)

    return " ".join(expression.split())


def evaluate(node):
    if isinstance(node, ast.Expression):
        return evaluate(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = evaluate(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value

    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = evaluate(node.left)
        right = evaluate(node.right)

        if isinstance(node.op, ast.Div) and right == 0:
            raise ValueError("Division by zero is not allowed.")

        return OPERATORS[type(node.op)](left, right)

    raise ValueError("Only basic arithmetic is supported.")


class CalculatorTool:
    def run(self, question: str):
        try:
            expression = clean_expression(question)

            if not expression:
                raise ValueError("No mathematical expression was found.")

            tree = ast.parse(expression, mode="eval")
            result = evaluate(tree)

            return {
                "answer": str(result),
                "expression": expression,
            }

        except (SyntaxError, ValueError, TypeError) as error:
            return {
                "answer": f"Calculator error: {error}"
            }


calculator_tool = CalculatorTool()
