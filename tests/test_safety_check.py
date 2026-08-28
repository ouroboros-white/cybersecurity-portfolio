"""Tests for scripts/safety_check.py, the publishing gate.

A note on the fixtures below. This test file is itself tracked by git, so the
safety check scans it like any other file. Writing a literal flag or a
real-looking home path into a test would therefore make the scanner fail on its
own test suite, and the tempting fix, adding tests/ to the scanner's exclusion
list, would carve a permanent blind spot into the one control that stops a
secret being published.

So every fixture is assembled at runtime from fragments that do not match on
their own. The scanner keeps full coverage of this directory, and the tests
still exercise the real patterns.
"""
import unittest
from unittest import mock

from . import context  # noqa: F401  (import for sys.path setup)
import safety_check


def flag():
    return "THM" + "{" + "example_value" + "}"


def private_key_header():
    return "-----BEGIN OPENSSH " + "PRIVATE KEY" + "-----"


def bearer():
    return "Bearer " + ("A1b2C3d4E5" * 3)


def email(local="someone", domain="example.com"):
    return local + "@" + domain


def windows_path(user):
    return "C:" + "\\" + "Users" + "\\" + user


def unix_home(user):
    return "/" + "home" + "/" + user


def flag_file():
    return "user" + "." + "txt"


class NormaliseKeyTests(unittest.TestCase):
    """A secret must be caught whatever casing convention it arrives in."""

    def test_camel_case_is_split_into_words(self):
        joined, words = safety_check.normalise_key("sessionToken")
        self.assertEqual(joined, "sessiontoken")
        self.assertEqual(words, {"session", "token"})

    def test_snake_and_kebab_are_equivalent_to_camel(self):
        self.assertEqual(
            safety_check.normalise_key("session_token"),
            safety_check.normalise_key("session-token"),
        )
        self.assertEqual(
            safety_check.normalise_key("session_token")[0],
            safety_check.normalise_key("sessionToken")[0],
        )

    def test_digits_do_not_split_a_word(self):
        joined, _ = safety_check.normalise_key("apiKey2")
        self.assertEqual(joined, "apikey2")


class SensitiveKeyTests(unittest.TestCase):
    def test_credential_shaped_keys_are_flagged(self):
        for key in (
            "password", "passwd", "secret", "sessionToken", "api_key",
            "Authorization", "cookie", "privateKey", "credential",
            "sessionId", "accessKey", "pwd", "auth", "key", "salt",
            "hash", "signature",
        ):
            with self.subTest(key=key):
                self.assertTrue(safety_check.is_sensitive_key(key))

    def test_ordinary_content_keys_are_not_flagged(self):
        """The short-word list must not fire as a substring inside real fields.

        The API returns fields like authorName and rarityTier. If those tripped
        the check it would fail on every sync, which is the failure mode the
        whole key/value split exists to avoid.
        """
        for key in (
            "authorName", "roomTitle", "keyboard", "monkey", "difficulty",
            "earnedAt", "rarityTier", "imageURL", "description", "hashtag",
        ):
            with self.subTest(key=key):
                self.assertFalse(safety_check.is_sensitive_key(key))


class ValuePatternTests(unittest.TestCase):
    def scan(self, text):
        findings = []
        safety_check.scan_text(text, "fixture", findings)
        return findings

    def test_each_secret_shape_is_detected(self):
        cases = {
            "CTF flag": flag(),
            "private key block": private_key_header(),
            "bearer token": bearer(),
            "email address": email(),
            "Windows user path": windows_path("realname"),
            "Unix home path": unix_home("realname"),
            "flag file reference": flag_file(),
        }
        for label, value in cases.items():
            with self.subTest(label=label):
                findings = self.scan("prefix " + value + " suffix")
                self.assertTrue(
                    any(label in f for f in findings),
                    "%s not detected in %r (got %r)" % (label, value, findings),
                )

    def test_security_prose_does_not_trigger(self):
        """The design premise: lab content legitimately uses these words."""
        prose = (
            "Authentication Bypass is a room about password reuse, session "
            "tokens and credential stuffing. The key insight is that a hash "
            "is not encryption, and an authorization header carrying a bearer "
            "value should never be logged."
        )
        self.assertEqual(self.scan(prose), [])

    def test_long_matches_are_truncated_for_readability(self):
        findings = self.scan("Bearer " + ("B" * 200))
        self.assertTrue(findings[0].endswith("..."))
        self.assertLessEqual(len(findings[0].split(" -> ")[1]), 60)


class ExemptionTests(unittest.TestCase):
    def test_noreply_addresses_are_exempt(self):
        self.assertTrue(
            safety_check.is_exempt(
                "email address", email("actions", "users.noreply.github.com")
            )
        )

    def test_contactable_addresses_are_not_exempt(self):
        self.assertFalse(safety_check.is_exempt("email address", email()))

    def test_vetted_content_username_is_exempt(self):
        for username in sorted(safety_check.CONTENT_USERNAMES):
            with self.subTest(username=username):
                self.assertTrue(
                    safety_check.is_exempt("Unix home path", unix_home(username))
                )
                self.assertTrue(
                    safety_check.is_exempt(
                        "Windows user path", windows_path(username)
                    )
                )

    def test_unlisted_username_still_fails(self):
        """The allow-list is opt-in by name, so an unknown user path is a finding.

        This is the property that keeps the assessor's real name catchable
        without listing that name in a public file.
        """
        self.assertFalse(
            safety_check.is_exempt("Unix home path", unix_home("unknownperson"))
        )
        self.assertFalse(
            safety_check.is_exempt(
                "Windows user path", windows_path("unknownperson")
            )
        )

    def test_exemption_is_case_insensitive(self):
        for username in sorted(safety_check.CONTENT_USERNAMES):
            with self.subTest(username=username):
                self.assertTrue(
                    safety_check.is_exempt(
                        "Windows user path", windows_path(username.upper())
                    )
                )


class ScanJsonTests(unittest.TestCase):
    def scan(self, node):
        findings = []
        safety_check.scan_json(node, "", findings)
        return findings

    def test_credential_key_holding_a_value_is_a_finding(self):
        findings = self.scan({"sessionToken": "anything at all"})
        self.assertEqual(len(findings), 1)
        self.assertIn("credential-shaped key", findings[0])

    def test_empty_credential_key_is_not_a_finding(self):
        for empty in (None, "", [], {}):
            with self.subTest(empty=empty):
                self.assertEqual(self.scan({"password": empty}), [])

    def test_secret_in_a_value_is_found_under_a_harmless_key(self):
        findings = self.scan({"roomDescription": "the answer was " + flag()})
        self.assertEqual(len(findings), 1)
        self.assertIn("CTF flag", findings[0])

    def test_findings_report_their_json_path(self):
        findings = self.scan({"rooms": [{"notes": unix_home("realname")}]})
        self.assertEqual(len(findings), 1)
        self.assertIn("rooms[0].notes", findings[0])

    def test_realistic_room_payload_is_clean(self):
        payload = {
            "profile": "ouroboroswhite",
            "rooms": [
                {
                    "title": "Authentication Bypass",
                    "difficulty": "Easy",
                    "description": "Learn how to defeat login password checks.",
                },
                {
                    "title": "Hashing - Crypto 101",
                    "difficulty": "Easy",
                    "description": "Hashing, salting and key derivation.",
                },
            ],
            "badges": [{"name": "OWASP Top 10", "rarityTier": "rare"}],
        }
        self.assertEqual(self.scan(payload), [])


class TrackedFilesTests(unittest.TestCase):
    def run_with_git_output(self, stdout):
        result = mock.Mock(stdout=stdout)
        with mock.patch.object(safety_check.subprocess, "run", return_value=result):
            return safety_check.tracked_files()

    def test_the_scanner_excludes_itself(self):
        """Otherwise the scanner's own pattern literals become findings."""
        files = self.run_with_git_output("README.md\n" + safety_check.SELF + "\n")
        self.assertEqual(files, ["README.md"])

    def test_binary_suffixes_are_skipped(self):
        files = self.run_with_git_output(
            "README.md\nimg/badge.PNG\ndocs/report.pdf\nnotes.md\n"
        )
        self.assertEqual(files, ["README.md", "notes.md"])

    def test_missing_git_falls_back_to_the_fixed_list(self):
        with mock.patch.object(
            safety_check.subprocess, "run", side_effect=OSError("no git")
        ):
            self.assertEqual(
                safety_check.tracked_files(), safety_check.FALLBACK_TARGETS
            )


if __name__ == "__main__":
    unittest.main()
