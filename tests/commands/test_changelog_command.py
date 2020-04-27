import os
import sys
from datetime import date

import pytest

from commitizen import cli, git
from tests.utils import create_file_and_commit


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_on_empty_project(mocker):
    testargs = ["cz", "changelog", "--dry-run"]
    mocker.patch.object(sys, "argv", testargs)

    with pytest.raises(SystemExit):
        cli.main()


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_from_version_zero_point_two(mocker, capsys):
    create_file_and_commit("feat: new file")
    create_file_and_commit("refactor: not in changelog")

    # create tag
    testargs = ["cz", "bump", "--yes"]
    mocker.patch.object(sys, "argv", testargs)
    cli.main()
    capsys.readouterr()

    create_file_and_commit("feat: after 0.2.0")
    create_file_and_commit("feat: after 0.2")

    testargs = ["cz", "changelog", "--start-rev", "0.2.0", "--dry-run"]
    mocker.patch.object(sys, "argv", testargs)
    with pytest.raises(SystemExit):
        cli.main()

    out, _ = capsys.readouterr()
    assert out == "\n## Unreleased \n\n### Feat\n\n- after 0.2\n- after 0.2.0\n\n"


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_with_unsupported_cz(mocker, capsys):
    testargs = ["cz", "-n", "cz_jira", "changelog", "--dry-run"]
    mocker.patch.object(sys, "argv", testargs)

    with pytest.raises(SystemExit):
        cli.main()
    out, err = capsys.readouterr()
    assert "'cz_jira' rule does not support changelog" in err


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_from_start(mocker, capsys):
    changelog_path = os.path.join(os.getcwd(), "CHANGELOG.md")
    create_file_and_commit("feat: new file")
    create_file_and_commit("refactor: is in changelog")
    create_file_and_commit("Merge into master")

    testargs = ["cz", "changelog"]
    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    with open(changelog_path, "r") as f:
        out = f.read()

    assert (
        out
        == "\n## Unreleased \n\n### Refactor\n\n- is in changelog\n\n### Feat\n\n- new file\n"
    )


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_replacing_unreleased_using_incremental(mocker, capsys):
    changelog_path = os.path.join(os.getcwd(), "CHANGELOG.md")

    create_file_and_commit("feat: add new output")
    create_file_and_commit("fix: output glitch")
    create_file_and_commit("Merge into master")

    testargs = ["cz", "changelog"]
    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    testargs = ["cz", "bump", "--yes"]
    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    create_file_and_commit("fix: mama gotta work")
    create_file_and_commit("feat: add more stuff")
    create_file_and_commit("Merge into master")

    testargs = ["cz", "changelog", "--incremental"]
    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    with open(changelog_path, "r") as f:
        out = f.read()

    today = date.today().isoformat()
    assert (
        out
        == f"\n\n## Unreleased \n\n### Feat\n\n- add more stuff\n\n### Fix\n\n- mama gotta work\n\n## 0.2.0 ({today})\n\n### Fix\n\n- output glitch\n\n### Feat\n\n- add new output\n"
    )


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_is_persisted_using_incremental(mocker, capsys):
    changelog_path = os.path.join(os.getcwd(), "CHANGELOG.md")

    create_file_and_commit("feat: add new output")
    create_file_and_commit("fix: output glitch")
    create_file_and_commit("Merge into master")

    testargs = ["cz", "bump", "--yes"]
    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    testargs = ["cz", "changelog"]
    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    with open(changelog_path, "a") as f:
        f.write("\nnote: this should be persisted using increment\n")

    create_file_and_commit("fix: mama gotta work")
    create_file_and_commit("feat: add more stuff")
    create_file_and_commit("Merge into master")

    testargs = ["cz", "changelog", "--incremental"]

    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    with open(changelog_path, "r") as f:
        out = f.read()

    today = date.today().isoformat()
    assert (
        out
        == f"\n\n## Unreleased \n\n### Feat\n\n- add more stuff\n\n### Fix\n\n- mama gotta work\n\n## 0.2.0 ({today})\n\n### Fix\n\n- output glitch\n\n### Feat\n\n- add new output\n\nnote: this should be persisted using increment\n"
    )


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_incremental_angular_sample(mocker, capsys):
    changelog_path = os.path.join(os.getcwd(), "CHANGELOG.md")
    with open(changelog_path, "w") as f:
        f.write(
            "# [10.0.0-next.3](https://github.com/angular/angular/compare/10.0.0-next.2...10.0.0-next.3) (2020-04-22)\n"
            "\n"
            "### Bug Fixes"
            "\n"
            "* **common:** format day-periods that cross midnight ([#36611](https://github.com/angular/angular/issues/36611)) ([c6e5fc4](https://github.com/angular/angular/commit/c6e5fc4)), closes [#36566](https://github.com/angular/angular/issues/36566)\n"
        )
    create_file_and_commit("irrelevant commit")
    git.tag("10.0.0-next.3")

    create_file_and_commit("feat: add new output")
    create_file_and_commit("fix: output glitch")
    create_file_and_commit("fix: mama gotta work")
    create_file_and_commit("feat: add more stuff")
    create_file_and_commit("Merge into master")

    testargs = ["cz", "changelog", "--incremental"]

    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    with open(changelog_path, "r") as f:
        out = f.read()

    assert (
        out
        == "\n## Unreleased \n\n### Feat\n\n- add more stuff\n- add new output\n\n### Fix\n\n- mama gotta work\n- output glitch\n\n# [10.0.0-next.3](https://github.com/angular/angular/compare/10.0.0-next.2...10.0.0-next.3) (2020-04-22)\n\n### Bug Fixes\n* **common:** format day-periods that cross midnight ([#36611](https://github.com/angular/angular/issues/36611)) ([c6e5fc4](https://github.com/angular/angular/commit/c6e5fc4)), closes [#36566](https://github.com/angular/angular/issues/36566)\n"
    )


KEEP_A_CHANGELOG = """# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2017-06-20
### Added
- New visual identity by [@tylerfortune8](https://github.com/tylerfortune8).
- Version navigation.

### Changed
- Start using "changelog" over "change log" since it's the common usage.

### Removed
- Section about "changelog" vs "CHANGELOG".

## [0.3.0] - 2015-12-03
### Added
- RU translation from [@aishek](https://github.com/aishek).
"""


@pytest.mark.usefixtures("tmp_commitizen_project")
def test_changlog_incremental_keep_a_changelog_sample(mocker, capsys):
    changelog_path = os.path.join(os.getcwd(), "CHANGELOG.md")
    with open(changelog_path, "w") as f:
        f.write(KEEP_A_CHANGELOG)
    create_file_and_commit("irrelevant commit")
    git.tag("1.0.0")

    create_file_and_commit("feat: add new output")
    create_file_and_commit("fix: output glitch")
    create_file_and_commit("fix: mama gotta work")
    create_file_and_commit("feat: add more stuff")
    create_file_and_commit("Merge into master")

    testargs = ["cz", "changelog", "--incremental"]

    mocker.patch.object(sys, "argv", testargs)
    cli.main()

    with open(changelog_path, "r") as f:
        out = f.read()

    assert (
        out
        == """# Changelog\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n\n## Unreleased \n\n### Feat\n\n- add more stuff\n- add new output\n\n### Fix\n\n- mama gotta work\n- output glitch\n\n## [1.0.0] - 2017-06-20\n### Added\n- New visual identity by [@tylerfortune8](https://github.com/tylerfortune8).\n- Version navigation.\n\n### Changed\n- Start using "changelog" over "change log" since it\'s the common usage.\n\n### Removed\n- Section about "changelog" vs "CHANGELOG".\n\n## [0.3.0] - 2015-12-03\n### Added\n- RU translation from [@aishek](https://github.com/aishek).\n"""
    )
