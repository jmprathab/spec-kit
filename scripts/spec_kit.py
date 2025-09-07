#!/usr/bin/env python3

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path


class ProjectManager:
    """Manages project root and configuration without VCS dependency"""

    CONFIG_FILE = 'spec-kit.json'

    def __init__(self):
        self.project_root = self._find_project_root()
        self.config_path = os.path.join(self.project_root, self.CONFIG_FILE)
        self.config = self._load_config()

    def _find_project_root(self):
        """Find project root by looking for spec-kit.json or specs directory"""
        current_dir = os.getcwd()

        # Stop at filesystem root
        while current_dir != os.path.dirname(current_dir):
            config_file = os.path.join(current_dir, self.CONFIG_FILE)
            specs_dir = os.path.join(current_dir, 'specs')

            if os.path.isfile(config_file) or os.path.isdir(specs_dir):
                return current_dir

            current_dir = os.path.dirname(current_dir)

        # If not found, use current working directory
        return os.getcwd()

    def _load_config(self):
        """Load configuration from spec-kit.json"""
        if os.path.isfile(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"Warning: Could not load config from {self.config_path}: {e}")

        return {
            "current_feature": None
        }

    def _save_config(self):
        """Save configuration to spec-kit.json"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error: Could not save config to {self.config_path}: {e}")
            raise

    def get_project_root(self):
        """Get project root directory"""
        return self.project_root

    def get_current_feature(self):
        """Get current feature name"""
        return self.config.get("current_feature")

    def set_current_feature(self, feature_name):
        """Set current feature name"""
        self.config["current_feature"] = feature_name
        self._save_config()

    def get_next_feature_number(self):
        """Get next available feature number by scanning existing features"""
        specs_dir = os.path.join(self.project_root, 'specs')
        highest = 0

        if os.path.isdir(specs_dir):
            for entry in os.listdir(specs_dir):
                entry_path = os.path.join(specs_dir, entry)
                if os.path.isdir(entry_path):
                    match = re.match(r'^(\d+)', entry)
                    if match:
                        number = int(match.group(1))
                        if number > highest:
                            highest = number

        return highest + 1

    def get_project_name(self):
        """Get project name from directory name"""
        return os.path.basename(self.project_root)


class FeatureManager:
    """Manages feature creation and validation"""

    def __init__(self, project_manager):
        self.project_manager = project_manager

    def check_feature_name(self, feature_name):
        """Check if feature name follows the required pattern"""
        if not feature_name:
            print("ERROR: No current feature set.")
            print("Run 'create-new-feature' first to create a feature.")
            return False

        if not re.match(r'^[0-9]{3}-', feature_name):
            print(f"ERROR: Invalid feature name: {feature_name}")
            print("Feature names should be like: 001-feature-name")
            return False
        return True

    def get_feature_dir(self, feature_name):
        """Get feature directory path"""
        return os.path.join(self.project_manager.get_project_root(), 'specs', feature_name)

    def get_feature_paths(self):
        """Get all standard paths for current feature"""
        project_root = self.project_manager.get_project_root()
        current_feature = self.project_manager.get_current_feature()

        if not current_feature:
            raise SystemExit(
                "ERROR: No current feature set. Run 'create-new-feature' first.")

        feature_dir = self.get_feature_dir(current_feature)

        return {
            'PROJECT_ROOT': project_root,
            'CURRENT_FEATURE': current_feature,
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md'),
            'RESEARCH': os.path.join(feature_dir, 'research.md'),
            'DATA_MODEL': os.path.join(feature_dir, 'data-model.md'),
            'QUICKSTART': os.path.join(feature_dir, 'quickstart.md'),
            'CONTRACTS_DIR': os.path.join(feature_dir, 'contracts')
        }

    def create_new_feature(self, feature_description):
        """Create a new feature with auto-generated name"""
        if not feature_description.strip():
            raise ValueError("Feature description cannot be empty")

        project_root = self.project_manager.get_project_root()
        specs_dir = os.path.join(project_root, 'specs')

        # Create specs directory if it doesn't exist
        os.makedirs(specs_dir, exist_ok=True)

        # Get next feature number
        next_num = self.project_manager.get_next_feature_number()
        feature_num = f"{next_num:03d}"

        # Create feature name from description
        feature_name = re.sub(r'[^a-z0-9]', '-', feature_description.lower())
        feature_name = re.sub(r'-+', '-', feature_name)
        feature_name = feature_name.strip('-')

        # Extract 2-3 meaningful words
        words = [w for w in feature_name.split('-') if w]
        words = words[:3]
        words_str = '-'.join(words)

        # Final feature name
        final_feature_name = f"{feature_num}-{words_str}"

        # Create feature directory
        feature_dir = os.path.join(specs_dir, final_feature_name)
        os.makedirs(feature_dir, exist_ok=True)

        # Update configuration
        self.project_manager.set_current_feature(final_feature_name)

        return {
            "feature_name": final_feature_name,
            "feature_dir": feature_dir,
            "feature_num": feature_num
        }


class FileManager:
    """Manages file operations and template handling"""

    def __init__(self, project_manager):
        self.project_manager = project_manager

    def check_file(self, file_path, description):
        """Check if a file exists and report"""
        if os.path.isfile(file_path):
            print(f" ✓ {description}")
            return True
        else:
            print(f" ✗ {description}")
            return False

    def check_dir(self, dir_path, description):
        """Check if a directory exists and has files"""
        if os.path.isdir(dir_path) and os.listdir(dir_path):
            print(f" ✓ {description}")
            return True
        else:
            print(f" ✗ {description}")
            return False

    def copy_template(self, template_name, target_path):
        """Copy template file if it exists"""
        project_root = self.project_manager.get_project_root()
        template = os.path.join(project_root, 'templates', template_name)

        if os.path.isfile(template):
            import shutil
            shutil.copy2(template, target_path)
            return True
        else:
            print(
                f"Warning: Template not found at {template}", file=sys.stderr)
            Path(target_path).touch()
            return False


class SpecKit:
    """Main SpecKit class that orchestrates all operations"""

    def __init__(self):
        self.script_name = sys.argv[0] if sys.argv[0] else 'spec_kit.py'
        self.project_manager = ProjectManager()
        self.feature_manager = FeatureManager(self.project_manager)
        self.file_manager = FileManager(self.project_manager)

    def check_task_prerequisites(self, json_mode=False):
        """Implementation of check-task-prerequisites.sh"""
        try:
            paths = self.feature_manager.get_feature_paths()
        except SystemExit as e:
            print(str(e))
            sys.exit(1)

        current_feature = paths['CURRENT_FEATURE']

        # Check if feature name is valid
        if not self.feature_manager.check_feature_name(current_feature):
            sys.exit(1)

        # Check if feature directory exists
        if not os.path.isdir(paths['FEATURE_DIR']):
            print(
                f"ERROR: Feature directory not found: {paths['FEATURE_DIR']}")
            print("Run 'create-new-feature' first to create the feature structure.")
            sys.exit(1)

        # Check for implementation plan (required)
        if not os.path.isfile(paths['IMPL_PLAN']):
            print(f"ERROR: plan.md not found in {paths['FEATURE_DIR']}")
            print("Run 'setup-plan' first to create the plan.")
            sys.exit(1)

        if json_mode:
            # Build JSON array of available docs that actually exist
            docs = []
            if os.path.isfile(paths['RESEARCH']):
                docs.append("research.md")
            if os.path.isfile(paths['DATA_MODEL']):
                docs.append("data-model.md")
            if os.path.isdir(paths['CONTRACTS_DIR']) and os.listdir(paths['CONTRACTS_DIR']):
                docs.append("contracts/")
            if os.path.isfile(paths['QUICKSTART']):
                docs.append("quickstart.md")

            result = {
                "FEATURE_DIR": paths['FEATURE_DIR'],
                "AVAILABLE_DOCS": docs
            }
            print(json.dumps(result))
        else:
            # List available design documents (optional)
            print(f"FEATURE_DIR:{paths['FEATURE_DIR']}")
            print("AVAILABLE_DOCS:")

            # Use common check functions
            self.file_manager.check_file(paths['RESEARCH'], "research.md")
            self.file_manager.check_file(paths['DATA_MODEL'], "data-model.md")
            self.file_manager.check_dir(paths['CONTRACTS_DIR'], "contracts/")
            self.file_manager.check_file(paths['QUICKSTART'], "quickstart.md")

    def get_feature_paths_command(self):
        """Implementation of get-feature-paths.sh"""
        try:
            paths = self.feature_manager.get_feature_paths()
        except SystemExit as e:
            print(str(e))
            sys.exit(1)

        current_feature = paths['CURRENT_FEATURE']

        # Check if feature name is valid
        if not self.feature_manager.check_feature_name(current_feature):
            sys.exit(1)

        # Output paths (don't create anything)
        print(f"PROJECT_ROOT: {paths['PROJECT_ROOT']}")
        print(f"FEATURE_NAME: {paths['CURRENT_FEATURE']}")
        print(f"FEATURE_DIR: {paths['FEATURE_DIR']}")
        print(f"FEATURE_SPEC: {paths['FEATURE_SPEC']}")
        print(f"IMPL_PLAN: {paths['IMPL_PLAN']}")
        print(f"TASKS: {paths['TASKS']}")

    def create_new_feature(self, feature_description, json_mode=False):
        """Implementation of create-new-feature.sh"""
        if not feature_description.strip():
            print(
                f"Usage: {self.script_name} create-new-feature [--json] <feature_description>", file=sys.stderr)
            sys.exit(1)

        try:
            result = self.feature_manager.create_new_feature(
                feature_description)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        # Copy template if it exists
        project_root = self.project_manager.get_project_root()
        spec_file = os.path.join(result['feature_dir'], 'spec.md')
        self.file_manager.copy_template('spec-template.md', spec_file)

        if json_mode:
            output = {
                "FEATURE_NAME": result['feature_name'],
                "SPEC_FILE": spec_file,
                "FEATURE_NUM": result['feature_num']
            }
            print(json.dumps(output))
        else:
            # Output results for the LLM to use (legacy key: value format)
            print(f"FEATURE_NAME: {result['feature_name']}")
            print(f"SPEC_FILE: {spec_file}")
            print(f"FEATURE_NUM: {result['feature_num']}")

    def setup_plan(self, json_mode=False):
        """Implementation of setup-plan.sh"""
        try:
            paths = self.feature_manager.get_feature_paths()
        except SystemExit as e:
            print(str(e))
            sys.exit(1)

        current_feature = paths['CURRENT_FEATURE']

        # Check if feature name is valid
        if not self.feature_manager.check_feature_name(current_feature):
            sys.exit(1)

        # Create specs directory if it doesn't exist
        os.makedirs(paths['FEATURE_DIR'], exist_ok=True)

        # Copy plan template if it exists
        self.file_manager.copy_template('plan-template.md', paths['IMPL_PLAN'])

        if json_mode:
            result = {
                "FEATURE_SPEC": paths['FEATURE_SPEC'],
                "IMPL_PLAN": paths['IMPL_PLAN'],
                "SPECS_DIR": paths['FEATURE_DIR'],
                "FEATURE_NAME": paths['CURRENT_FEATURE']
            }
            print(json.dumps(result))
        else:
            # Output all paths for LLM use
            print(f"FEATURE_SPEC: {paths['FEATURE_SPEC']}")
            print(f"IMPL_PLAN: {paths['IMPL_PLAN']}")
            print(f"SPECS_DIR: {paths['FEATURE_DIR']}")
            print(f"FEATURE_NAME: {paths['CURRENT_FEATURE']}")

    def set_current_feature(self, feature_name):
        """Set the current feature name"""
        if not self.feature_manager.check_feature_name(feature_name):
            sys.exit(1)

        # Check if feature directory exists
        feature_dir = self.feature_manager.get_feature_dir(feature_name)
        if not os.path.isdir(feature_dir):
            print(f"ERROR: Feature directory not found: {feature_dir}")
            print("Available features:")
            specs_dir = os.path.join(
                self.project_manager.get_project_root(), 'specs')
            if os.path.isdir(specs_dir):
                for entry in sorted(os.listdir(specs_dir)):
                    entry_path = os.path.join(specs_dir, entry)
                    if os.path.isdir(entry_path) and re.match(r'^[0-9]{3}-', entry):
                        print(f"  {entry}")
            sys.exit(1)

        self.project_manager.set_current_feature(feature_name)
        print(f"Current feature set to: {feature_name}")

    def get_current_feature_info(self):
        """Get information about the current feature"""
        current_feature = self.project_manager.get_current_feature()
        if not current_feature:
            print("No current feature set.")
            print("Use 'create-new-feature' to create a new feature or 'set-current-feature' to switch to an existing one.")
            return

        print(f"Current feature: {current_feature}")
        try:
            paths = self.feature_manager.get_feature_paths()
            print(f"Feature directory: {paths['FEATURE_DIR']}")
            print(f"Feature spec: {paths['FEATURE_SPEC']}")
            print(f"Implementation plan: {paths['IMPL_PLAN']}")
        except SystemExit:
            print("(Feature directory not found)")

    def list_available_features(self):
        """List all available features"""
        specs_dir = os.path.join(
            self.project_manager.get_project_root(), 'specs')
        current_feature = self.project_manager.get_current_feature()

        if not os.path.isdir(specs_dir):
            print(
                "No features found. Use 'create-new-feature' to create the first feature.")
            return

        print("Available features:")
        features = []
        for entry in os.listdir(specs_dir):
            entry_path = os.path.join(specs_dir, entry)
            if os.path.isdir(entry_path) and re.match(r'^[0-9]{3}-', entry):
                features.append(entry)

        if not features:
            print(
                "No features found. Use 'create-new-feature' to create the first feature.")
            return

        for feature in sorted(features):
            marker = " (current)" if feature == current_feature else ""
            print(f"  {feature}{marker}")

        print("")
        print(f"Usage: {self.script_name} set-current-feature <feature-name>")
        print(f"       {self.script_name} get-current-feature")

    def update_agent_context(self, agent_type=None):
        """Implementation of update-agent-context.sh"""
        try:
            paths = self.feature_manager.get_feature_paths()
        except SystemExit as e:
            print(str(e))
            sys.exit(1)

        project_root = paths['PROJECT_ROOT']
        current_feature = paths['CURRENT_FEATURE']
        feature_dir = paths['FEATURE_DIR']
        new_plan = paths['IMPL_PLAN']

        # Determine which agent context files to update
        claude_file = os.path.join(project_root, 'CLAUDE.md')
        gemini_file = os.path.join(project_root, 'GEMINI.md')
        copilot_file = os.path.join(
            project_root, '.github', 'copilot-instructions.md')

        if not os.path.isfile(new_plan):
            print(f"ERROR: No plan.md found at {new_plan}")
            sys.exit(1)

        print(
            f"=== Updating agent context files for feature {current_feature} ===")

        # Extract tech from new plan
        new_lang = ""
        new_framework = ""
        new_testing = ""
        new_db = ""
        new_project_type = ""

        try:
            with open(new_plan, 'r') as f:
                content = f.read()

            # Extract information using regex
            lang_match = re.search(
                r'^\*\*Language/Version\*\*: (.+)$', content, re.MULTILINE)
            if lang_match and "NEEDS CLARIFICATION" not in lang_match.group(1):
                new_lang = lang_match.group(1).strip()

            framework_match = re.search(
                r'^\*\*Primary Dependencies\*\*: (.+)$', content, re.MULTILINE)
            if framework_match and "NEEDS CLARIFICATION" not in framework_match.group(1):
                new_framework = framework_match.group(1).strip()

            testing_match = re.search(
                r'^\*\*Testing\*\*: (.+)$', content, re.MULTILINE)
            if testing_match and "NEEDS CLARIFICATION" not in testing_match.group(1):
                new_testing = testing_match.group(1).strip()

            storage_match = re.search(
                r'^\*\*Storage\*\*: (.+)$', content, re.MULTILINE)
            if storage_match and "N/A" not in storage_match.group(1) and "NEEDS CLARIFICATION" not in storage_match.group(1):
                new_db = storage_match.group(1).strip()

            project_match = re.search(
                r'^\*\*Project Type\*\*: (.+)$', content, re.MULTILINE)
            if project_match:
                new_project_type = project_match.group(1).strip()

        except Exception as e:
            print(f"Warning: Could not parse plan.md: {e}")

        def update_agent_file(target_file, agent_name):
            """Update a single agent context file"""
            print(f"Updating {agent_name} context file: {target_file}")

            if not os.path.isfile(target_file):
                print(f"Creating new {agent_name} context file...")

                # Check if this is the SDD repo itself
                template_path = os.path.join(
                    project_root, 'templates', 'agent-file-template.md')
                if os.path.isfile(template_path):
                    with open(template_path, 'r') as f:
                        template_content = f.read()

                    # Replace placeholders
                    template_content = template_content.replace(
                        '[PROJECT NAME]', os.path.basename(project_root))
                    template_content = template_content.replace(
                        '[DATE]', datetime.now().strftime('%Y-%m-%d'))
                    template_content = template_content.replace('[EXTRACTED FROM ALL PLAN.MD FILES]',
                                                                f"- {new_lang} + {new_framework} ({current_feature})")

                    # Add project structure based on type
                    if "web" in new_project_type.lower():
                        structure = "backend/\nfrontend/\ntests/"
                    else:
                        structure = "src/\ntests/"
                    template_content = template_content.replace(
                        '[ACTUAL STRUCTURE FROM PLANS]', structure)

                    # Add minimal commands
                    if "Python" in new_lang:
                        commands = "cd src && pytest && ruff check ."
                    elif "Rust" in new_lang:
                        commands = "cargo test && cargo clippy"
                    elif "JavaScript" in new_lang or "TypeScript" in new_lang:
                        commands = "npm test && npm run lint"
                    else:
                        commands = f"# Add commands for {new_lang}"

                    template_content = template_content.replace(
                        '[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]', commands)

                    # Add code style
                    template_content = template_content.replace('[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]',
                                                                f"{new_lang}: Follow standard conventions")

                    # Add recent changes
                    template_content = template_content.replace('[LAST 3 FEATURES AND WHAT THEY ADDED]',
                                                                f"- {current_feature}: Added {new_lang} + {new_framework}")

                    with open(target_file, 'w') as f:
                        f.write(template_content)
                else:
                    print(f"ERROR: Template not found at {template_path}")
                    return False
            else:
                print(f"Updating existing {agent_name} context file...")

                try:
                    with open(target_file, 'r') as f:
                        content = f.read()

                    # Check if new tech already exists
                    tech_section_match = re.search(
                        r'## Active Technologies\n(.*?)\n\n', content, re.DOTALL)
                    if tech_section_match:
                        existing_tech = tech_section_match.group(1)

                        # Add new tech if not already present
                        new_additions = []
                        if new_lang and new_lang not in existing_tech:
                            new_additions.append(
                                f"- {new_lang} + {new_framework} ({current_feature})")
                        if new_db and new_db not in existing_tech and new_db != "N/A":
                            new_additions.append(
                                f"- {new_db} ({current_feature})")

                        if new_additions:
                            updated_tech = existing_tech + \
                                "\n" + "\n".join(new_additions)
                            content = content.replace(tech_section_match.group(0),
                                                      f"## Active Technologies\n{updated_tech}\n\n")

                    # Update project structure if needed
                    if new_project_type == "web" and "frontend/" not in content:
                        struct_match = re.search(
                            r'## Project Structure\n```\n(.*?)\n```', content, re.DOTALL)
                        if struct_match:
                            updated_struct = struct_match.group(
                                1) + "\nfrontend/src/ # Web UI"
                            content = re.sub(r'(## Project Structure\n```\n).*?(\n```)',
                                             f'\\1{updated_struct}\\2', content, flags=re.DOTALL)

                    # Add new commands if language is new
                    if new_lang and f"# {new_lang}" not in content:
                        commands_match = re.search(
                            r'## Commands\n```bash\n(.*?)\n```', content, re.DOTALL)
                        if not commands_match:
                            commands_match = re.search(
                                r'## Commands\n(.*?)\n\n', content, re.DOTALL)

                        if commands_match:
                            new_commands = commands_match.group(1)
                            if "Python" in new_lang:
                                new_commands += "\ncd src && pytest && ruff check ."
                            elif "Rust" in new_lang:
                                new_commands += "\ncargo test && cargo clippy"
                            elif "JavaScript" in new_lang or "TypeScript" in new_lang:
                                new_commands += "\nnpm test && npm run lint"

                            if "```bash" in content:
                                content = re.sub(r'(## Commands\n```bash\n).*?(\n```)',
                                                 f'\\1{new_commands}\\2', content, flags=re.DOTALL)
                            else:
                                content = re.sub(r'(## Commands\n).*?(\n\n)',
                                                 f'\\1{new_commands}\\2', content, flags=re.DOTALL)

                    # Update recent changes (keep only last 3)
                    changes_match = re.search(
                        r'## Recent Changes\n(.*?)(\n\n|$)', content, re.DOTALL)
                    if changes_match:
                        changes = [c.strip() for c in changes_match.group(
                            1).strip().split('\n') if c.strip()]
                        changes.insert(
                            0, f"- {current_feature}: Added {new_lang} + {new_framework}")
                        changes = changes[:3]  # Keep only last 3
                        content = re.sub(r'(## Recent Changes\n).*?(\n\n|$)',
                                         f'\\1{chr(10).join(changes)}\\2', content, flags=re.DOTALL)

                    # Update date
                    content = re.sub(r'Last updated: \d{4}-\d{2}-\d{2}',
                                     f'Last updated: {datetime.now().strftime("%Y-%m-%d")}', content)

                    with open(target_file, 'w') as f:
                        f.write(content)

                except Exception as e:
                    print(f"ERROR: Failed to update {target_file}: {e}")
                    return False

            print(f"✅ {agent_name} context file updated successfully")
            return True

        # Update files based on argument or detect existing files
        if agent_type == "claude":
            update_agent_file(claude_file, "Claude Code")
        elif agent_type == "gemini":
            update_agent_file(gemini_file, "Gemini CLI")
        elif agent_type == "copilot":
            update_agent_file(copilot_file, "GitHub Copilot")
        elif agent_type is None:
            # Update all existing files
            updated_any = False
            if os.path.isfile(claude_file):
                update_agent_file(claude_file, "Claude Code")
                updated_any = True
            if os.path.isfile(gemini_file):
                update_agent_file(gemini_file, "Gemini CLI")
                updated_any = True
            if os.path.isfile(copilot_file):
                update_agent_file(copilot_file, "GitHub Copilot")
                updated_any = True

            # If no files exist, create based on current directory or ask user
            if not updated_any:
                print(
                    "No agent context files found. Creating Claude Code context file by default.")
                os.makedirs(os.path.dirname(claude_file), exist_ok=True)
                update_agent_file(claude_file, "Claude Code")
        else:
            print(
                f"ERROR: Unknown agent type '{agent_type}'. Use: claude, gemini, copilot, or leave empty for all.")
            sys.exit(1)

        print("")
        print("Summary of changes:")
        if new_lang:
            print(f"- Added language: {new_lang}")
        if new_framework:
            print(f"- Added framework: {new_framework}")
        if new_db and new_db != "N/A":
            print(f"- Added database: {new_db}")

        print("")
        print(
            f"Usage: {self.script_name} update-agent-context [claude|gemini|copilot]")
        print(" - No argument: Update all existing agent context files")
        print(" - claude: Update only CLAUDE.md")
        print(" - gemini: Update only GEMINI.md")
        print(" - copilot: Update only .github/copilot-instructions.md")


def main():
    """Main function to handle command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: spec_kit.py <command> [args...]")
        print("")
        print("Available commands:")
        print("  check-task-prerequisites [--json]")
        print("  get-feature-paths")
        print("  create-new-feature [--json] <description>")
        print("  setup-plan [--json]")
        print("  update-agent-context [claude|gemini|copilot]")
        print("  set-current-feature <feature-name>")
        print("  get-current-feature")
        print("  list-features")
        print("")
        print("Examples:")
        print("  spec_kit.py check-task-prerequisites")
        print("  spec_kit.py check-task-prerequisites --json")
        print("  spec_kit.py create-new-feature 'user authentication system'")
        print("  spec_kit.py create-new-feature --json 'user authentication system'")
        print("  spec_kit.py setup-plan")
        print("  spec_kit.py setup-plan --json")
        print("  spec_kit.py update-agent-context")
        print("  spec_kit.py update-agent-context claude")
        print("  spec_kit.py set-current-feature 001-user-auth")
        print("  spec_kit.py get-current-feature")
        print("  spec_kit.py list-features")
        sys.exit(1)

    kit = SpecKit()
    command = sys.argv[1]

    if command == "check-task-prerequisites":
        json_mode = "--json" in sys.argv[2:]
        if "--help" in sys.argv[2:] or "-h" in sys.argv[2:]:
            print("Usage: spec_kit.py check-task-prerequisites [--json]")
            sys.exit(0)
        kit.check_task_prerequisites(json_mode)

    elif command == "get-feature-paths":
        kit.get_feature_paths_command()

    elif command == "create-new-feature":
        json_mode = "--json" in sys.argv[2:]
        args = [arg for arg in sys.argv[2:]
                if arg not in ["--json", "--help", "-h"]]

        if "--help" in sys.argv[2:] or "-h" in sys.argv[2:]:
            print(
                "Usage: spec_kit.py create-new-feature [--json] <description>")
            sys.exit(0)

        if not args:
            print(
                "Usage: spec_kit.py create-new-feature [--json] <description>", file=sys.stderr)
            sys.exit(1)

        description = " ".join(args)
        kit.create_new_feature(description, json_mode)

    elif command == "setup-plan":
        json_mode = "--json" in sys.argv[2:]
        if "--help" in sys.argv[2:] or "-h" in sys.argv[2:]:
            print("Usage: spec_kit.py setup-plan [--json]")
            sys.exit(0)
        kit.setup_plan(json_mode)

    elif command == "update-agent-context":
        agent_type = None
        if len(sys.argv) > 2:
            agent_type = sys.argv[2]
            if agent_type in ["--help", "-h"]:
                print(
                    "Usage: spec_kit.py update-agent-context [claude|gemini|copilot]")
                sys.exit(0)
        kit.update_agent_context(agent_type)

    elif command == "set-current-feature":
        if len(sys.argv) < 3 or sys.argv[2] in ["--help", "-h"]:
            print("Usage: spec_kit.py set-current-feature <feature-name>")
            kit.list_available_features()
            sys.exit(0 if len(sys.argv) >= 3 else 1)

        feature_name = sys.argv[2]
        kit.set_current_feature(feature_name)

    elif command == "get-current-feature":
        kit.get_current_feature_info()

    elif command == "list-features":
        kit.list_available_features()

    else:
        print(f"ERROR: Unknown command '{command}'", file=sys.stderr)
        print("Run 'spec_kit.py' without arguments to see available commands.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
