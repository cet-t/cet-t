# Claude Code 向けルール

- 変更は `main` に直接 push せず、作業ブランチから `main` 向けの Pull Request を作成する。
- コミットメッセージと PR 本文にセッション ID やセッション URL（`Claude-Session:` 行など）を含めない。
- `README.md` は `scripts/generate.py` が `projects.toml` から生成する。直接編集せず、`projects.toml` を変更して `python scripts/generate.py` を実行する。
- 変更後は `python -m unittest discover -s tests` を実行する。
