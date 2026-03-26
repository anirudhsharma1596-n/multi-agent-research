# tools/calculator.py
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """
    Evaluates a basic math expression safely.
    Example: calculator("2 + 2 * 10") -> "22"

    The @tool decorator turns this into a LangChain tool
    that agents can call via tool_use.
    """
    try:
        # eval() is dangerous with untrusted input in production
        # For interviews: mention you'd use a proper math parser like numexpr
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"

        result = eval(expression)  # safe here — we validated chars above
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"