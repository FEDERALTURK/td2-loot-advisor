"""Regresyon testleri — 9.1.5.19'da düzeltilen iki gerçek çökme hatasının
tekrar kodun içine girmediğini statik analizle (AST) doğrular.

    python -B -m unittest discover -s tests -p test_regression_crash_patterns.py -v

Bu testler GUI'yi açmaz; tüm `.py` dosyalarını (kök dizin + td2app/) AST
olarak ayrıştırıp iki bilinen hata desenini arar:

1) `webbrowser.open(...)` gibi "bare" (modül adı üzerinden doğrudan)
   kullanımlar varsa, `webbrowser` o dosyanın en üstünde modül
   seviyesinde `import webbrowser` ile içe aktarılmış olmalı. Yalnızca
   bir fonksiyonun içinde yapılan yerel `import webbrowser` başka bir
   fonksiyondaki bare kullanımı kurtarmaz — tam olarak 9.1.5.19'dan
   önceki "Kaynağı aç" / "Aç" düğmeleri çökmesinin nedeni buydu.

2) Bir `except X as e:` bloğu içinde, `root.after` / `after_idle` /
   `call_soon` / `call_later` / `Timer(...)` ile GECİKMELİ çalışacak
   şekilde zamanlanan bir `lambda` içinde `e` doğrudan kullanılmamalı.
   CPython, except bloğu bitince bağladığı adı otomatik siler
   (traceback referans döngülerini önlemek için); lambda daha sonra
   çalıştığında bu NameError'a yol açar — tam olarak Tanılama Merkezi
   ve Sürüm Geçmişi hatalarının nedeni buydu.
"""
import ast
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PY_FILES = sorted(REPO_ROOT.glob("*.py")) + sorted((REPO_ROOT / "td2app").rglob("*.py"))

DEFERRED_CALL_ATTRS = {"after", "after_idle", "call_soon", "call_later", "call_soon_threadsafe"}


def _parse(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _module_level_import_names(tree: ast.Module) -> set:
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def _uses_bare_attr(tree: ast.Module, modname: str) -> bool:
    return any(
        isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == modname
        for n in ast.walk(tree)
    )


def _is_deferred_call(call: ast.Call) -> bool:
    fn = call.func
    if isinstance(fn, ast.Attribute) and fn.attr in DEFERRED_CALL_ATTRS:
        return True
    if isinstance(fn, ast.Name) and fn.id == "Timer":
        return True
    return False


def _find_except_name_in_deferred_lambda(tree: ast.Module):
    violations = []

    class V(ast.NodeVisitor):
        def visit_ExceptHandler(self, node: ast.ExceptHandler):
            if node.name:
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) and _is_deferred_call(sub):
                        for arg in list(sub.args) + [kw.value for kw in sub.keywords]:
                            if isinstance(arg, ast.Lambda):
                                for inner in ast.walk(arg.body):
                                    if isinstance(inner, ast.Name) and inner.id == node.name:
                                        violations.append((sub.lineno, node.name))
            self.generic_visit(node)

    V().visit(tree)
    return violations


class WebbrowserImportRegressionTest(unittest.TestCase):
    """9.1.5.19 öncesi: 'Kaynağı aç'/'Aç' düğmeleri webbrowser modülü
    yalnızca başka bir fonksiyonda yerel import edildiği için NameError
    veriyordu."""

    def test_no_bare_webbrowser_usage_without_module_level_import(self):
        failures = []
        for path in PY_FILES:
            tree = _parse(path)
            if _uses_bare_attr(tree, "webbrowser") and "webbrowser" not in _module_level_import_names(tree):
                failures.append(str(path.relative_to(REPO_ROOT)))
        self.assertFalse(
            failures,
            "Bu dosyalarda 'webbrowser.xxx(...)' bare kullanılıyor ama modül "
            "seviyesinde 'import webbrowser' yok (bkz. 9.1.5.19 çökme "
            f"düzeltmesi): {failures}",
        )


class ExceptClosureRegressionTest(unittest.TestCase):
    """9.1.5.19 öncesi: Tanılama Merkezi ve Sürüm Geçmişi hata bildirimleri,
    except bloğunun değişkenini gecikmeli bir lambda içinde kullandığı için
    (CPython'un bloğu bitince değişkeni silmesi yüzünden) ikinci bir
    NameError üretiyordu."""

    def test_no_except_name_captured_in_deferred_lambda(self):
        failures = []
        for path in PY_FILES:
            tree = _parse(path)
            violations = _find_except_name_in_deferred_lambda(tree)
            for lineno, name in violations:
                failures.append(f"{path.relative_to(REPO_ROOT)}:{lineno} (değişken '{name}')")
        self.assertFalse(
            failures,
            "Gecikmeli zamanlanmış (after/after_idle/call_soon/call_later/Timer) "
            "bir lambda içinde, except bloğunun bağladığı değişken doğrudan "
            "kullanılıyor; değeri önce ayrı bir yerel değişkene kopyalayın "
            f"(bkz. 9.1.5.19 çökme düzeltmesi): {failures}",
        )


if __name__ == "__main__":
    unittest.main()
