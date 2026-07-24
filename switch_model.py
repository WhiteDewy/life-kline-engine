#!/usr/bin/env python3
"""Agent model switcher - Usage: python switch_model.py <profile>

Directly writes model names into each agent's .md config file.
PM (astrologer-pm) uses its own model; all other agents share the default.
"""

import json
import re
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, '.claude', 'agent-models.json')
AGENTS_DIR = os.path.join(SCRIPT_DIR, '.claude', 'agents')

# Which agent uses the pm model instead of the default
PM_AGENT = 'astrologer-pm'


def main():
    if len(sys.argv) < 2:
        print("Usage: python switch_model.py <profile>")
        print()
        print("Available profiles:")
        with open(CONFIG_FILE, encoding='utf-8') as f:
            config = json.load(f)
        for name, info in config['profiles'].items():
            desc = info.get('description', '')
            pm_model = info.get('pm', info.get('default'))
            print(f"  {name:<12} - {desc}")
            print(f"  {'':12}   pm={pm_model}, default={info.get('default')}")
        return

    profile_name = sys.argv[1]

    with open(CONFIG_FILE, encoding='utf-8') as f:
        config = json.load(f)

    if profile_name not in config['profiles']:
        print(f"Error: Profile '{profile_name}' not found")
        print("Available profiles:")
        for name in config['profiles']:
            print(f"  {name}")
        sys.exit(1)

    profile = config['profiles'][profile_name]
    default_model = profile.get('default')
    pm_model = profile.get('pm', default_model)

    if not default_model:
        print(f"Error: Profile '{profile_name}' has no 'default' model defined")
        sys.exit(1)

    print(f"Switching to '{profile_name}' profile...\n")

    updated = 0
    for fname in sorted(os.listdir(AGENTS_DIR)):
        if not fname.endswith('.md'):
            continue

        agent_name = fname[:-3]
        target_model = pm_model if agent_name == PM_AGENT else default_model
        agent_file = os.path.join(AGENTS_DIR, fname)

        with open(agent_file, encoding='utf-8') as f:
            content = f.read()

        model_match = re.search(r'^model: (.+)$', content, re.MULTILINE)
        if model_match:
            current_model = model_match.group(1).strip()
            if current_model != target_model:
                new_content = re.sub(
                    r'^model: .+$',
                    f'model: {target_model}',
                    content,
                    flags=re.MULTILINE
                )
                with open(agent_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                updated += 1
                print(f"  [OK] {agent_name}: {current_model} -> {target_model}")
            else:
                print(f"  [=] {agent_name}: {target_model} (unchanged)")

    label = 'PM_MODEL' if PM_AGENT in os.listdir(AGENTS_DIR) else 'pm'
    print(f"\nSummary:")
    print(f"  Profile: {profile_name}")
    print(f"  {PM_AGENT}: {pm_model}")
    print(f"  others:   {default_model}")
    print(f"  Updated:  {updated} files")


if __name__ == '__main__':
    main()
