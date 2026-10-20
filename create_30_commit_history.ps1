$ErrorActionPreference = "Stop"

# Run this script from the library_management_system Git repository.
if (-not (Test-Path ".git") -or -not (Test-Path "main.py")) {
    throw "Open PowerShell in the library_management_system project root first."
}
$branch = (git branch --show-current).Trim()
if ($branch -ne "main") { throw "Expected branch 'main', found '$branch'." }
$remote = (git remote get-url origin)
if ($LASTEXITCODE -ne 0 -or -not $remote) { throw "GitHub remote 'origin' is not configured." }
if ((git status --porcelain | Out-String).Trim()) {
    throw "Working tree is not clean. Commit or back up your existing changes before running this script."
}

$testFile = "tests\test_performance.py"
if (-not (Test-Path $testFile)) { throw "Missing tests\test_performance.py." }

$tests = @(
@'
    def test_login_rejects_unknown_username(self):
        self.assertIsNone(self.db.verify_user("not-a-user", "admin123"))
'@,
@'
    def test_login_trims_username_whitespace(self):
        self.assertIsNotNone(self.db.verify_user(" admin ", "admin123"))
'@,
@'
    def test_empty_book_search_count(self):
        self.add_book(1, "ISBN-1", 1)
        self.add_book(2, "ISBN-2", 1)
        self.assertEqual(self.books.count(""), 2)
'@,
@'
    def test_book_search_is_case_insensitive(self):
        self.add_book()
        self.assertEqual(self.books.count("python book"), 1)
'@,
@'
    def test_book_category_filter_is_case_insensitive(self):
        self.add_book()
        self.assertEqual(self.books.count("", category="programming"), 1)
'@,
@'
    def test_book_categories_are_sorted(self):
        self.books.add([1, "ISBN-1", "Z Book", "Author", "Zoology", "Press", 2024, 1, 1])
        self.books.add([2, "ISBN-2", "A Book", "Author", "Biology", "Press", 2024, 1, 1])
        self.assertEqual(self.books.categories(), ["Biology", "Zoology"])
'@,
@'
    def test_missing_book_lookup_returns_none(self):
        self.assertIsNone(self.books.get(999))
'@,
@'
    def test_book_delete_removes_record(self):
        self.add_book()
        self.books.delete(1)
        self.assertIsNone(self.books.get(1))
'@,
@'
    def test_member_add_and_get_round_trip(self):
        self.add_member(7)
        row = self.members.get(7)
        self.assertEqual(row["name"], "Test Member")
        self.assertEqual(row["member_id"], 7)
'@,
@'
    def test_member_search_is_case_insensitive(self):
        self.add_member()
        self.assertEqual(len(self.members.list("test member")), 1)
'@,
@'
    def test_member_count_matches_search(self):
        self.add_member(1)
        self.members.add([2, "Different Person", "9999999999", "other@example.com", "BTech", date.today().isoformat()])
        self.assertEqual(self.members.count("Test Member"), 1)
'@,
@'
    def test_member_pagination_respects_limit(self):
        for i in range(1, 5):
            self.add_member(i)
        self.assertEqual(len(self.members.list(limit=2, offset=1)), 2)
'@,
@'
    def test_missing_member_lookup_returns_none(self):
        self.assertIsNone(self.members.get(999))
'@,
@'
    def test_issue_missing_book_does_not_create_transaction(self):
        self.add_member()
        with self.assertRaises(ValueError):
            self.transactions.issue(999, 1, (date.today() + timedelta(days=7)).isoformat())
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS n FROM transactions")["n"], 0)
'@,
@'
    def test_issue_missing_member_preserves_stock(self):
        self.add_book()
        with self.assertRaises(ValueError):
            self.transactions.issue(1, 999, (date.today() + timedelta(days=7)).isoformat())
        self.assertEqual(self.books.get(1)["available_quantity"], 3)
'@,
@'
    def test_issue_rejects_past_due_date(self):
        self.add_book()
        self.add_member()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            self.transactions.issue(1, 1, yesterday)
        self.assertEqual(self.books.get(1)["available_quantity"], 3)
'@,
@'
    def test_issue_rejects_zero_available_stock(self):
        self.add_book(quantity=0)
        self.add_member()
        with self.assertRaises(ValueError):
            self.transactions.issue(1, 1, (date.today() + timedelta(days=7)).isoformat())
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS n FROM transactions")["n"], 0)
'@,
@'
    def test_second_return_is_rejected(self):
        self.add_book()
        self.add_member()
        due = (date.today() + timedelta(days=7)).isoformat()
        self.transactions.issue(1, 1, due)
        self.transactions.return_book(1)
        with self.assertRaises(ValueError):
            self.transactions.return_book(1)
        self.assertEqual(self.books.get(1)["available_quantity"], 3)
'@,
@'
    def test_issued_list_excludes_returned_transactions(self):
        self.add_book(quantity=3)
        self.add_member()
        due = (date.today() + timedelta(days=7)).isoformat()
        self.transactions.issue(1, 1, due)
        self.transactions.return_book(1)
        self.transactions.issue(1, 1, due)
        rows = self.transactions.issued()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "Issued")
'@,
@'
    def test_recent_transactions_respects_limit(self):
        self.add_book(quantity=3)
        self.add_member()
        due = (date.today() + timedelta(days=7)).isoformat()
        for _ in range(3):
            self.transactions.issue(1, 1, due)
        self.assertEqual(len(self.transactions.recent(limit=2)), 2)
'@,
@'
    def test_database_journal_mode_is_wal(self):
        self.assertEqual(str(self.db.fetchone("PRAGMA journal_mode")[0]).lower(), "wal")
'@,
@'
    def test_database_busy_timeout_is_configured(self):
        self.assertGreaterEqual(self.db.fetchone("PRAGMA busy_timeout")[0], 1000)
'@
)

$added = 0
foreach ($method in $tests) {
    $source = Get-Content $testFile -Raw
    $methodName = [regex]::Match($method, 'def (test_[A-Za-z0-9_]+)\(').Groups[1].Value
    if (-not $methodName) { throw "Could not determine test method name." }

    if ($source -match "(?m)^\s*def $([regex]::Escape($methodName))\(") {
        Write-Host "Skipping existing test: $methodName"
        continue
    }

    $marker = 'if __name__ == "__main__":'
    $position = $source.LastIndexOf($marker)
    if ($position -lt 0) { throw "Could not find test-file insertion point." }

    $updated = $source.Insert($position, "`r`n$method`r`n")
    Set-Content -Path $testFile -Value $updated -Encoding UTF8

    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) {
        Set-Content -Path $testFile -Value $source -Encoding UTF8
        throw "Tests failed after adding $methodName. File restored; no commit for this test."
    }

    git add $testFile
    if ($LASTEXITCODE -ne 0) { Set-Content -Path $testFile -Value $source -Encoding UTF8; throw "git add failed." }

    git commit -m "Test: $($methodName -replace '^test_', '' -replace '_', ' ')"
    if ($LASTEXITCODE -ne 0) { throw "Commit failed while adding $methodName." }

    $added++
    Write-Host "Committed test $added of $($tests.Count): $methodName"
}

if ($added -eq 0) {
    Write-Host "No new test commits were needed; all listed tests already exist."
} else {
    Write-Host "Created $added test commits. Pushing commits to GitHub..."
}

git push origin main
if ($LASTEXITCODE -ne 0) { throw "Push failed. Commits are local; retry with: git push origin main" }

Write-Host "`nFinal Git status:"
git status
Write-Host "`nRecent commit history:"
git log --oneline -35
