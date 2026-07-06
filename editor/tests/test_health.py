"""Tests for the Kubernetes liveness/readiness probe endpoints.

The probes are public (no authentication) and must behave correctly whether or
not the database is reachable — see ``editor.views.liveness`` /
``editor.views.readiness`` for the rationale behind the split.
"""
from unittest import mock

from django.db.utils import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse


class LivenessProbeTest(TestCase):
    def test_returns_200_ok(self):
        response = self.client.get(reverse("liveness"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_content_type_is_json(self):
        response = self.client.get(reverse("liveness"))
        self.assertEqual(response["Content-Type"], "application/json")

    def test_requires_no_authentication(self):
        # An anonymous client (no login) must get through, not be redirected to
        # the ADFS login form.
        response = self.client.get(reverse("liveness"))
        self.assertEqual(response.status_code, 200)

    def test_does_not_touch_the_database(self):
        # The whole point of liveness is that a DB outage must NOT fail it, so
        # it must issue zero queries.
        with self.assertNumQueries(0):
            self.client.get(reverse("liveness"))


class ReadinessProbeTest(TestCase):
    def test_healthy_returns_200_with_all_checks_ok(self):
        response = self.client.get(reverse("readiness"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["checks"]["database"], "ok")
        self.assertEqual(payload["checks"]["migrations"], "ok")

    def test_healthy_reports_database_latency(self):
        payload = self.client.get(reverse("readiness")).json()
        self.assertIn("database_latency_ms", payload)
        self.assertIsInstance(payload["database_latency_ms"], (int, float))

    def test_requires_no_authentication(self):
        response = self.client.get(reverse("readiness"))
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=True)
    def test_debug_flag_reflects_settings(self):
        self.assertIs(self.client.get(reverse("readiness")).json()["debug"], True)

    @override_settings(DEBUG=False)
    def test_debug_flag_reflects_settings_when_disabled(self):
        self.assertIs(self.client.get(reverse("readiness")).json()["debug"], False)

    def test_database_down_returns_503(self):
        # Simulate an unreachable database: connection.cursor() raises.
        broken = mock.MagicMock()
        broken.cursor.side_effect = OperationalError("connection refused")
        with mock.patch("editor.views.connection", broken):
            response = self.client.get(reverse("readiness"))

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["status"], "unhealthy")
        self.assertIn("error", payload["checks"]["database"])

    def test_database_down_skips_migration_check(self):
        # When the DB is unreachable the migration check must be skipped rather
        # than repeating the same failed connection (doubling probe latency).
        broken = mock.MagicMock()
        broken.cursor.side_effect = OperationalError("connection refused")
        with mock.patch("editor.views.connection", broken) as patched_conn, \
                mock.patch("editor.views.MigrationExecutor") as executor:
            response = self.client.get(reverse("readiness"))

        executor.assert_not_called()
        self.assertEqual(
            response.json()["checks"]["migrations"], "skipped: database unreachable"
        )
        # Latency is only reported on a successful DB round-trip.
        self.assertNotIn("database_latency_ms", response.json())

    def test_unapplied_migrations_returns_503(self):
        # DB is up, but there are pending migrations.
        executor = mock.MagicMock()
        executor.loader.graph.leaf_nodes.return_value = []
        executor.migration_plan.return_value = [("editor", "0002_something")]
        with mock.patch("editor.views.MigrationExecutor", return_value=executor):
            response = self.client.get(reverse("readiness"))

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["status"], "unhealthy")
        self.assertEqual(payload["checks"]["database"], "ok")
        self.assertIn("unapplied migration", payload["checks"]["migrations"])
