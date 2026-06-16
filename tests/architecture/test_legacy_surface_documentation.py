import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INFRA_ROOT = REPOSITORY_ROOT / "infra"
LIVE_SURFACE_CATALOG = (
    REPOSITORY_ROOT / "documentation" / "system" / "live-operation-surfaces.adoc"
)
DEPLOYMENT_DOC = REPOSITORY_ROOT / "documentation" / "deployment" / "system.adoc"


class TestLegacySurfaceDocumentation(unittest.TestCase):
    def test_live_operation_surface_catalog_defines_supported_statuses(self):
        catalog = _read_document(LIVE_SURFACE_CATALOG)

        for status in ("Supported", "Transitional", "Retired", "Supported Asset"):
            with self.subTest(status=status):
                self.assertIn(f"| {status} |", catalog)

    def test_live_operation_surface_catalog_classifies_key_entrypoints(self):
        catalog = _read_document(LIVE_SURFACE_CATALOG)
        expected_rows = {
            "`infra/prepare/prepare.sh`": "Retired",
            "`infra/prepare/portainer/prepare.sh`": "Retired",
            "`infra/prepare/portainer/portain_setup.py`": "Retired",
            "`infra/prepare/nexus/setup.py`": "Retired",
            "`infra/prepare/nexus/prepare.sh`": "Retired",
            "`infra/prepare/nexus/addMavenMirror.sh`": "Retired",
            "`infra/prepare/nexus/addLocalDockerRepository.sh`": "Retired",
            "`infra/prepare/nexus/test.sh`": "Retired",
            "Former `create_dockerfiles.sh` helper": "Retired",
            "Former `upload_all_stacks.sh` helper": "Retired",
            "`infra/config/compose/portainer/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/nexus/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/jenkins/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/swagger/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/swagger/nginx/default.conf`": "Supported Asset",
            "`infra/config/compose/service-access/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/service-access/dashboard/**`": "Supported Asset",
            "`infra/config/compose/service-access/nginx/**`": "Supported Asset",
        }

        for path, status in expected_rows.items():
            with self.subTest(path=path):
                self.assertIn(f"| {path} | {status} |", catalog)

    def test_compose_area_has_no_host_side_shell_orchestration(self):
        allowed_container_entrypoint_scripts = {
            "infra/config/compose/service-access/nginx/generate-self-signed-cert.sh",
        }
        shell_scripts = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in (REPOSITORY_ROOT / "infra" / "config" / "compose").rglob("*.sh")
        }

        self.assertEqual(allowed_container_entrypoint_scripts, shell_scripts)

        forbidden_fragments = (
            "docker build",
            "docker login",
            "docker push",
            "docker stack",
            "api/auth",
            "api/stacks",
            "portainer",
        )
        violations = {
            path: fragment
            for path in shell_scripts
            for fragment in forbidden_fragments
            if fragment in (REPOSITORY_ROOT / path).read_text(encoding="utf-8").lower()
        }

        self.assertEqual({}, violations)

    def test_swagger_nginx_uses_official_image_with_mounted_runtime_config(self):
        nginx_config = (
            REPOSITORY_ROOT / "infra" / "config" / "compose" / "swagger" / "nginx" / "default.conf"
        ).read_text(encoding="utf-8")
        compose = (REPOSITORY_ROOT / "infra" / "config" / "compose" / "swagger" / "docker-compose.yml").read_text(
            encoding="utf-8"
        )

        self.assertFalse(
            (REPOSITORY_ROOT / "infra" / "config" / "compose" / "swagger" / "nginx" / "Dockerfile").exists()
        )
        self.assertFalse(
            (REPOSITORY_ROOT / "infra" / "config" / "compose" / "swagger" / "nginx" / "wait-for-it.sh").exists()
        )
        self.assertIn("image: nginx:mainline-alpine", compose)
        self.assertIn("/swagger/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro", compose)
        self.assertIn("resolver 127.0.0.11", nginx_config)
        self.assertIn("set $swagger_api_upstream http://tasks.swagger-api:8000;", nginx_config)
        self.assertIn("return 302 /status;", nginx_config)
        self.assertIn("proxy_pass $swagger_api_upstream;", nginx_config)

    def test_compose_area_has_no_stack_definitions(self):
        self.assertFalse((REPOSITORY_ROOT / "infra" / "compose").exists())

    def test_service_access_assets_do_not_introduce_frontend_project_or_live_orchestration_surface(self):
        roots = [
            INFRA_ROOT / "config" / "compose" / "service-access",
        ]
        forbidden_names = {
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "vite.config.js",
            "vite.config.ts",
        }
        forbidden_suffixes = {".jsx", ".tsx"}
        forbidden_fragments = (
            "docker build",
            "docker login",
            "docker push",
            "docker stack",
            "docker compose",
            "docker swarm",
            "api/auth",
            "api/stacks",
            "portainer/api",
            "multipass",
            "socat",
        )

        forbidden_files = sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for root in roots
            for path in root.rglob("*")
            if path.is_file() and (path.name in forbidden_names or path.suffix.lower() in forbidden_suffixes)
        )
        self.assertEqual([], forbidden_files)

        live_violations = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): fragment
            for root in roots
            for path in root.rglob("*")
            if path.is_file()
            for fragment in forbidden_fragments
            if fragment in path.read_text(encoding="utf-8").lower()
        }
        self.assertEqual({}, live_violations)

    def test_service_access_nginx_owns_central_routes_without_request_logs(self):
        nginx_config = (
            INFRA_ROOT / "config" / "compose" / "service-access" / "nginx" / "default.conf"
        ).read_text(encoding="utf-8")

        self.assertEqual(3, nginx_config.count("access_log off;"))
        self.assertIn("listen 80;", nginx_config)
        self.assertIn("listen 8086;", nginx_config)
        self.assertIn("listen 443 ssl;", nginx_config)
        self.assertIn("ssl_certificate /etc/nginx/tls/infisical.crt;", nginx_config)
        self.assertIn("ssl_certificate_key /etc/nginx/tls/infisical.key;", nginx_config)
        self.assertIn("proxy_set_header X-Forwarded-Proto https;", nginx_config)
        self.assertIn("resolver 127.0.0.11", nginx_config)
        self.assertIn(
            "set $dashboard_upstream http://tasks.service-access-dashboard:80;",
            nginx_config,
        )
        self.assertIn("set $infisical_upstream http://tasks.infisical:8080;", nginx_config)
        for route in ("jenkins", "nexus", "portainer", "pulsar", "sonarqube", "swagger", "infisical"):
            with self.subTest(route=route):
                self.assertIn(f"location = /{route}", nginx_config)
        self.assertNotIn("password=", nginx_config)
        self.assertNotIn("token=", nginx_config)
        self.assertNotIn("secret=", nginx_config)
        self.assertNotIn("api_key=", nginx_config)

    def test_legacy_helper_areas_are_removed(self):
        removed_paths = (
            REPOSITORY_ROOT / "infra" / "prepare",
            REPOSITORY_ROOT / "infra" / "swarm",
            REPOSITORY_ROOT / "window-wsl-setup.ps1",
        )
        present_paths = [
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in removed_paths
            if path.exists()
        ]

        self.assertEqual([], present_paths)

    def test_java_maven_project_surface_is_not_reintroduced(self):
        forbidden_paths = (
            REPOSITORY_ROOT / "pom.xml",
            REPOSITORY_ROOT / "src" / "main" / "java",
        )
        present_paths = [
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in forbidden_paths
            if path.exists()
        ]

        self.assertEqual([], present_paths)

    def test_operator_docs_reference_live_operation_surface_catalog(self):
        catalog_path = "documentation/system/live-operation-surfaces.adoc"
        docs = [
            REPOSITORY_ROOT / "README.md",
            REPOSITORY_ROOT / "documentation" / "deployment" / "system.adoc",
            REPOSITORY_ROOT / "documentation" / "user_guide" / "usage.adoc",
            REPOSITORY_ROOT / "documentation" / "user_guide" / "installation.adoc",
        ]

        missing_reference = [
            doc.relative_to(REPOSITORY_ROOT).as_posix()
            for doc in docs
            if catalog_path not in _read_document(doc)
        ]

        self.assertEqual([], missing_reference)

    def test_nexus_bootstrap_is_routed_through_setup_workflow(self):
        deployment_doc = _read_document(DEPLOYMENT_DOC)

        self.assertIn("PYTHONPATH=src python3 -m tiny_swarm_world setup run --live", deployment_doc)
        self.assertIn("Nexus setup is owned by the Python setup workflow", deployment_doc)
        self.assertNotIn("python3 infra/prepare/nexus/setup.py", deployment_doc)

def _read_document(path: Path) -> str:
    return path.read_text(encoding="utf-8")
