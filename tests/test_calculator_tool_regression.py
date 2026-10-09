import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "backend" / "tools" / "calculator_tool.py"


spec = importlib.util.spec_from_file_location("calculator_tool_under_test", MODULE_PATH)
calculator_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(calculator_module)


CalculatorTool = calculator_module.CalculatorTool


def test_natural_language_prompt_with_trailing_period_returns_result():
    result = CalculatorTool().run(
        "What is 2 + 2? Reply with only the number."
    )

    assert result["answer"] == "4"
    assert result["expression"] == "2 + 2"


def test_decimal_literals_still_work_after_punctuation_cleanup():
    result = CalculatorTool().run("Calculate 2.5 * 2.")

    assert result["answer"] == "5.0"
    assert result["expression"] == "2.5 * 2"
