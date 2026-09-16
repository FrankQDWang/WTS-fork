"""Shared fixture builders for pacing tests; writes only temporary files."""
import copy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]


def load_builder(relative):
    spec = importlib.util.spec_from_file_location('builder', ROOT / relative / 'scripts/build_workflow.py')
    module = importlib.util.module_from_spec(spec)
    script_dir = str(ROOT / relative / 'scripts')
    sys.path.insert(0, script_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(script_dir)
    return module


def build(module, kind='search', iteration=2, plan=None):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'plan.json'
        path.write_text(json.dumps(plan if plan is not None else {
            'primary_query': 'Python 后端', 'secondary_query': 'Python API',
        }))
        args = SimpleNamespace(task_id='pacing-test', iteration=iteration,
                               deadline_minutes=20, plan_file=str(path))
        return getattr(module, 'build_' + kind)(args, module.load_assets())


def stable(workflow):
    result = copy.deepcopy(workflow)
    for key in ('workflow_id', 'created_at', 'expires_at', 'skill'):
        result.pop(key, None)
    return result
