import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "visualization" / "wts-v0-1-sop"
DIST = SITE / "dist"


class WtsSopVisualizationTest(unittest.TestCase):
    def read_required(self, path):
        self.assertTrue(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
        return path.read_text(encoding="utf-8")

    def test_required_site_files_exist(self):
        for relative_path in (
            "dist/index.html",
            "dist/styles.css",
            "dist/app.js",
            ".openai/hosting.json",
        ):
            self.assertTrue((SITE / relative_path).is_file(), relative_path)

    def test_page_covers_the_product_journey(self):
        html = self.read_required(DIST / "index.html")
        required_copy = (
            "JD 输入",
            "需求澄清",
            "需求确认门",
            "多轮检索",
            "隔离评分",
            "终态报告",
            "SearchPlan",
            "Controller",
            "Top 10",
        )
        for copy in required_copy:
            self.assertIn(copy, html)

    def test_page_exposes_six_key_nodes_and_four_roles(self):
        html = self.read_required(DIST / "index.html")
        self.assertEqual(html.count('class="node-card'), 6)
        for role in ("user", "agent", "browser", "pause"):
            self.assertIn(f'data-role="{role}"', html)

    def test_expanders_are_accessible(self):
        html = self.read_required(DIST / "index.html")
        controls = re.findall(
            r'<button[^>]+class="node-toggle"[^>]+aria-expanded="false"[^>]+aria-controls="([^"]+)"',
            html,
        )
        self.assertEqual(len(controls), 6)
        for target_id in controls:
            self.assertRegex(html, rf'id="{re.escape(target_id)}"[^>]+class="node-detail"')

    def test_site_has_no_external_runtime_assets(self):
        for path in DIST.glob("*"):
            if path.suffix in {".html", ".css", ".js"}:
                content = path.read_text(encoding="utf-8")
                self.assertNotRegex(content, r'(?:src|href)=["\']https?://')
                self.assertNotIn("@import url(http", content)

    def test_hosting_points_to_dist(self):
        config = json.loads(self.read_required(SITE / ".openai" / "hosting.json"))
        self.assertEqual(config["static"]["directory"], "dist")

    def test_final_outputs_match_the_frozen_contract(self):
        html = self.read_required(DIST / "index.html")
        self.assertIn("未满足原因", html)
        self.assertIn("失败项", html)
        self.assertNotIn("不推荐摘要", html)

    def test_retrieval_order_matches_the_browser_workflow(self):
        html = self.read_required(DIST / "index.html")
        loop = html[html.index('class="loop-diagram"'):html.index('</section>', html.index('class="loop-diagram"'))]
        expected_order = ("搜索与抽卡", "卡片预筛", "详情采集", "详情终筛", "隔离评分")
        for label in expected_order:
            self.assertIn(label, loop)
        positions = [loop.index(label) for label in expected_order]
        self.assertEqual(positions, sorted(positions))

    def test_stop_copy_preserves_controller_priority(self):
        html = self.read_required(DIST / "index.html")
        self.assertIn("达到最大轮次", html)
        self.assertIn("词族耗尽", html)
        self.assertIn("先放宽一次", html)
        self.assertNotIn("已有 2 轮但本轮没有新候选人", html)

    def test_role_colors_use_high_contrast_values(self):
        css = self.read_required(DIST / "styles.css")
        self.assertIn("--user: #9b3f00", css.lower())
        self.assertIn("--browser: #006b60", css.lower())


if __name__ == "__main__":
    unittest.main()
