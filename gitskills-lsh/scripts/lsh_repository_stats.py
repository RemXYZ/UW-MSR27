"""Summarise repository and owner overlap among the detected pairs."""
import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def owner(repo):
    return repo.split('/', 1)[0].casefold()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--pairs', type=Path,
        default=PROJECT_ROOT / 'lsh_results' / 'lsh_pairs.csv',
        help='CSV file produced by lsh_analysis.py',
    )
    parser.add_argument(
        '--owner', default='NeuralBlitz',
        help='Owner to examine separately (default: NeuralBlitz)',
    )
    args = parser.parse_args()

    counts = {'total': 0, 'same_repo': 0, 'same_owner': 0,
              'both_selected_owner': 0, 'same_repo_selected_owner': 0}
    selected_owner = args.owner.casefold()
    with args.pairs.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not {'repo_a', 'repo_b'}.issubset(reader.fieldnames or []):
            parser.error('The CSV file must contain repo_a and repo_b columns.')
        for row in reader:
            repo_a, repo_b = row['repo_a'].strip(), row['repo_b'].strip()
            if not repo_a or not repo_b or '/' not in repo_a or '/' not in repo_b:
                parser.error(f'Invalid repository name in CSV row {reader.line_num}.')
            same_repo = repo_a.casefold() == repo_b.casefold()
            owner_a, owner_b = owner(repo_a), owner(repo_b)
            both_selected = owner_a == selected_owner and owner_b == selected_owner
            counts['total'] += 1
            counts['same_repo'] += same_repo
            counts['same_owner'] += owner_a == owner_b
            counts['both_selected_owner'] += both_selected
            counts['same_repo_selected_owner'] += both_selected and same_repo

    total = counts['total']
    print(f'Number of pairs: {total:,}')
    for label, key in [
        ('Same repository', 'same_repo'),
        ('Same owner', 'same_owner'),
        (f'Both owned by {args.owner}', 'both_selected_owner'),
        (f'Same repository owned by {args.owner}', 'same_repo_selected_owner'),
    ]:
        value = counts[key]
        percentage = 100 * value / total if total else 0.0
        print(f'{label}: {value:,} ({percentage:.2f}%)')
    print('\nPercentages use all detected pairs as the denominator.')
    print('Repositories refer to representatives; other occurrences may be elsewhere.')


if __name__ == '__main__':
    main()
