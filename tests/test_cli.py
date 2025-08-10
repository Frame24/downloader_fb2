from click.testing import CliRunner
import pytest
from ranobe2fb2.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


# Здесь можно добавить тест запуска с моками аналогично тестам в client,
# подменив fetch_chapters_list и прочие через monkeypatch.
