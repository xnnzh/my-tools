from click.testing import CliRunner

from my_tools.cli import cli


def test_db_batch_delete_help():
    result = CliRunner().invoke(cli, ["db", "batch-delete", "--help"])
    assert result.exit_code == 0
    assert "--dry-run" in result.output
    assert "--task" in result.output


def test_db_csv_to_insert_sql_help():
    result = CliRunner().invoke(cli, ["db", "csv-to-insert-sql", "--help"])
    assert result.exit_code == 0
    assert "--table" in result.output
    assert "--database" in result.output
