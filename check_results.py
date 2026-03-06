import json

# Load the benchmark results
with open('benchmark/results/json/comprehensive_12_language_benchmark.json', 'r') as f:
    data = json.load(f)

print(f'Total results: {len(data["results"])}')

# Check for failed results
failed = [r for r in data['results'] if r.get('error_message') is not None]
print(f'Failed results: {len(failed)}')

if failed:
    print('Failed implementations:')
    for r in failed[:10]:
        print(f'  {r["implementation_name"]} - {r["scenario_name"]}: {r["error_message"]}')

# Check implementation counts
implementations = {}
for r in data['results']:
    impl = r['implementation_name']
    if impl not in implementations:
        implementations[impl] = 0
    implementations[impl] += 1

print('\nImplementation counts:')
for impl, count in sorted(implementations.items()):
    print(f'  {impl}: {count}')

# Check scenarios
scenarios = set(r['scenario_name'] for r in data['results'])
print(f'\nScenarios: {len(scenarios)}')
for scenario in sorted(scenarios):
    print(f'  {scenario}')