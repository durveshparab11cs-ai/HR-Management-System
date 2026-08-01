import ast
import sys

files_to_check = [
    'app/blueprints/attendance/routes.py',
    'app/blueprints/attendance/attendance_engine.py',
    'app/models/employee.py',
    'app/__init__.py'
]

def check_syntax(filepath):
    """Parse file with AST to catch all syntax errors."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg} - {e.text}"
    except Exception as e:
        return False, str(e)

print("=" * 70)
print("PYTHON SYNTAX ANALYSIS REPORT")
print("=" * 70)
print()

all_ok = True
for filepath in files_to_check:
    ok, error = check_syntax(filepath)
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"{status} | {filepath}")
    if error:
        print(f"     Error: {error}")
        all_ok = False
    print()

print("=" * 70)
if all_ok:
    print("✅ All files passed syntax validation!")
    sys.exit(0)
else:
    print("❌ Some files have syntax errors!")
    sys.exit(1)
