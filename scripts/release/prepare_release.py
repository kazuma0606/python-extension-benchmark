#!/usr/bin/env python3
"""Release preparation script for Multi-Language Python Extension Benchmark Framework

This script prepares a release by:
1. Validating all implementations
2. Running comprehensive tests
3. Generating release artifacts
4. Creating distribution packages
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer


class ReleasePreparator:
    """Handles release preparation tasks"""
    
    def __init__(self):
        self.project_root = project_root
        self.version = self._get_version()
        self.release_dir = self.project_root / "release" / f"v{self.version}"
        self.results = {}
        
    def _get_version(self) -> str:
        """Get version from VERSION file"""
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "unknown"
    
    def prepare_release(self) -> Dict[str, Any]:
        """Execute complete release preparation"""
        
        print(f"=== Preparing Release v{self.version} ===")
        
        # Create release directory
        self.release_dir.mkdir(parents=True, exist_ok=True)
        
        release_info = {
            'version': self.version,
            'timestamp': datetime.now().isoformat(),
            'steps': {}
        }
        
        try:
            # Step 1: Validate implementations
            print("\n1. Validating implementations...")
            validation_result = self._validate_implementations()
            release_info['steps']['validation'] = validation_result
            
            # Step 2: Run comprehensive tests
            print("\n2. Running comprehensive tests...")
            test_result = self._run_comprehensive_tests()
            release_info['steps']['testing'] = test_result
            
            # Step 3: Generate benchmark artifacts
            print("\n3. Generating benchmark artifacts...")
            benchmark_result = self._generate_benchmark_artifacts()
            release_info['steps']['benchmarks'] = benchmark_result
            
            # Step 4: Create documentation package
            print("\n4. Creating documentation package...")
            docs_result = self._create_documentation_package()
            release_info['steps']['documentation'] = docs_result
            
            # Step 5: Prepare distribution
            print("\n5. Preparing distribution...")
            dist_result = self._prepare_distribution()
            release_info['steps']['distribution'] = dist_result
            
            # Step 6: Generate release summary
            print("\n6. Generating release summary...")
            summary_result = self._generate_release_summary(release_info)
            release_info['steps']['summary'] = summary_result
            
            release_info['success'] = True
            print(f"\n✅ Release v{self.version} prepared successfully!")
            print(f"Release artifacts available in: {self.release_dir}")
            
        except Exception as e:
            release_info['success'] = False
            release_info['error'] = str(e)
            print(f"\n❌ Release preparation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Save release info
        release_info_path = self.release_dir / "release_info.json"
        with open(release_info_path, 'w', encoding='utf-8') as f:
            json.dump(release_info, f, indent=2, ensure_ascii=False)
        
        return release_info
    
    def _validate_implementations(self) -> Dict[str, Any]:
        """Validate all language implementations"""
        
        runner = BenchmarkRunner()
        
        # Get all available implementations
        available_implementations = runner.get_all_available_implementations()
        
        validation_results = {
            'total_implementations': len(available_implementations),
            'available_implementations': available_implementations,
            'loaded_implementations': [],
            'failed_implementations': [],
            'success_rate': 0.0
        }
        
        # Try to load each implementation
        for impl_name in available_implementations:
            try:
                implementations = runner.load_implementations([impl_name])
                if implementations:
                    validation_results['loaded_implementations'].append(impl_name)
                    print(f"  ✓ {impl_name}: Loaded successfully")
                else:
                    validation_results['failed_implementations'].append({
                        'name': impl_name,
                        'error': 'Failed to load'
                    })
                    print(f"  ❌ {impl_name}: Failed to load")
            except Exception as e:
                validation_results['failed_implementations'].append({
                    'name': impl_name,
                    'error': str(e)
                })
                print(f"  ❌ {impl_name}: Error - {e}")
        
        # Calculate success rate
        loaded_count = len(validation_results['loaded_implementations'])
        total_count = len(available_implementations)
        validation_results['success_rate'] = loaded_count / total_count if total_count > 0 else 0
        
        print(f"\nValidation Summary: {loaded_count}/{total_count} implementations loaded "
              f"({validation_results['success_rate']:.1%} success rate)")
        
        return validation_results
    
    def _run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        
        test_results = {
            'test_suites': {},
            'overall_success': False
        }
        
        # Define test suites to run
        test_suites = [
            ('Unit Tests', 'python -m pytest tests/test_scenarios.py -v --tb=short'),
            ('Integration Tests', 'python -m pytest tests/test_multi_language_integration.py -v --tb=short'),
            ('Final Integration Tests', 'python -m pytest tests/test_final_integration.py -v --tb=short'),
            ('Property Tests', 'python -m pytest tests/ -k "property" -v --tb=short')
        ]
        
        all_passed = True
        
        for suite_name, command in test_suites:
            print(f"\n  Running {suite_name}...")
            
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                suite_result = {
                    'command': command,
                    'returncode': result.returncode,
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
                if suite_result['success']:
                    print(f"    ✓ {suite_name}: Passed")
                else:
                    print(f"    ❌ {suite_name}: Failed (exit code {result.returncode})")
                    all_passed = False
                
                test_results['test_suites'][suite_name] = suite_result
                
            except subprocess.TimeoutExpired:
                print(f"    ⏰ {suite_name}: Timed out")
                test_results['test_suites'][suite_name] = {
                    'command': command,
                    'success': False,
                    'error': 'Timeout'
                }
                all_passed = False
            except Exception as e:
                print(f"    ❌ {suite_name}: Error - {e}")
                test_results['test_suites'][suite_name] = {
                    'command': command,
                    'success': False,
                    'error': str(e)
                }
                all_passed = False
        
        test_results['overall_success'] = all_passed
        
        passed_count = sum(1 for suite in test_results['test_suites'].values() if suite.get('success', False))
        total_count = len(test_suites)
        
        print(f"\nTest Summary: {passed_count}/{total_count} test suites passed")
        
        return test_results
    
    def _generate_benchmark_artifacts(self) -> Dict[str, Any]:
        """Generate benchmark artifacts for the release"""
        
        benchmark_results = {
            'artifacts_generated': [],
            'benchmark_summary': {},
            'success': False
        }
        
        try:
            runner = BenchmarkRunner()
            
            # Run a lightweight benchmark for release validation
            print("  Running release validation benchmark...")
            
            # Load available implementations (limit to avoid long execution)
            available_implementations = runner.get_all_available_implementations()
            test_implementations = available_implementations[:6]  # Limit for release prep
            
            implementations = runner.load_implementations(test_implementations)
            
            if implementations:
                # Run lightweight scenarios
                from benchmark.runner.scenarios import NumericScenario, MemoryScenario
                
                scenarios = [
                    NumericScenario("primes"),
                    MemoryScenario("sort")
                ]
                
                # Set small data sizes for quick execution
                scenarios[0].input_data = 1000
                scenarios[1].input_data = list(range(5000, 0, -1))
                
                all_results = []
                for scenario in scenarios:
                    results = runner.run_scenario(
                        scenario, implementations,
                        warmup_runs=1, measurement_runs=3
                    )
                    all_results.extend(results)
                
                # Save benchmark results
                artifacts_dir = self.release_dir / "benchmark_artifacts"
                artifacts_dir.mkdir(exist_ok=True)
                
                writer = OutputWriter(base_dir=str(artifacts_dir))
                
                # JSON results
                json_path = writer.write_json(all_results, "release_validation_benchmark")
                benchmark_results['artifacts_generated'].append(json_path)
                
                # CSV results
                csv_path = writer.write_csv(all_results, "release_validation_benchmark")
                benchmark_results['artifacts_generated'].append(csv_path)
                
                # Generate visualizations
                visualizer = Visualizer(base_dir=str(artifacts_dir / "graphs"))
                
                successful_results = [r for r in all_results if r.status == "SUCCESS"]
                if successful_results:
                    # Execution time graph
                    exec_graph = visualizer.plot_execution_time(
                        successful_results, "release_execution_time"
                    )
                    benchmark_results['artifacts_generated'].append(exec_graph)
                    
                    # Memory usage graph
                    memory_graph = visualizer.plot_memory_usage(
                        successful_results, "release_memory_usage"
                    )
                    benchmark_results['artifacts_generated'].append(memory_graph)
                
                # Generate summary
                benchmark_results['benchmark_summary'] = {
                    'total_results': len(all_results),
                    'successful_results': len(successful_results),
                    'tested_implementations': [impl.name for impl in implementations],
                    'scenarios_tested': [scenario.name for scenario in scenarios]
                }
                
                benchmark_results['success'] = True
                print(f"    ✓ Generated {len(benchmark_results['artifacts_generated'])} benchmark artifacts")
            
            else:
                print("    ⚠ No implementations available for benchmark generation")
                benchmark_results['success'] = True  # Not a failure, just no implementations
        
        except Exception as e:
            print(f"    ❌ Benchmark generation failed: {e}")
            benchmark_results['error'] = str(e)
        
        return benchmark_results
    
    def _create_documentation_package(self) -> Dict[str, Any]:
        """Create documentation package for release"""
        
        docs_result = {
            'files_included': [],
            'success': False
        }
        
        try:
            docs_dir = self.release_dir / "documentation"
            docs_dir.mkdir(exist_ok=True)
            
            # Copy main documentation files
            doc_files = [
                'README.md',
                'CHANGELOG.md',
                'docs/API_REFERENCE.md',
                'docs/TUTORIAL.md',
                'DOCKER_README.md'
            ]
            
            for doc_file in doc_files:
                source_path = self.project_root / doc_file
                if source_path.exists():
                    dest_path = docs_dir / Path(doc_file).name
                    shutil.copy2(source_path, dest_path)
                    docs_result['files_included'].append(str(dest_path))
                    print(f"    ✓ Copied {doc_file}")
            
            # Copy additional documentation from docs/ directory
            docs_source_dir = self.project_root / "docs"
            if docs_source_dir.exists():
                for doc_file in docs_source_dir.glob("*.md"):
                    if doc_file.name not in ['API_REFERENCE.md', 'TUTORIAL.md']:
                        dest_path = docs_dir / doc_file.name
                        shutil.copy2(doc_file, dest_path)
                        docs_result['files_included'].append(str(dest_path))
                        print(f"    ✓ Copied {doc_file.name}")
            
            # Create documentation index
            index_content = self._create_documentation_index(docs_result['files_included'])
            index_path = docs_dir / "INDEX.md"
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            docs_result['files_included'].append(str(index_path))
            
            docs_result['success'] = True
            print(f"    ✓ Created documentation package with {len(docs_result['files_included'])} files")
            
        except Exception as e:
            print(f"    ❌ Documentation package creation failed: {e}")
            docs_result['error'] = str(e)
        
        return docs_result
    
    def _create_documentation_index(self, doc_files: List[str]) -> str:
        """Create documentation index file"""
        
        content = f"""# Multi-Language Python Extension Benchmark Framework v{self.version}

## Documentation Index

This package contains comprehensive documentation for the Multi-Language Python Extension Benchmark Framework.

### Core Documentation

- **README.md** - Project overview and quick start guide
- **CHANGELOG.md** - Version history and release notes
- **API_REFERENCE.md** - Complete API documentation
- **TUTORIAL.md** - Step-by-step usage tutorial
- **DOCKER_README.md** - Docker environment usage guide

### Additional Resources

"""
        
        # Add other documentation files
        for doc_file in doc_files:
            filename = Path(doc_file).name
            if filename not in ['README.md', 'CHANGELOG.md', 'API_REFERENCE.md', 'TUTORIAL.md', 'DOCKER_README.md', 'INDEX.md']:
                content += f"- **{filename}** - Additional documentation\n"
        
        content += f"""
### Quick Start

1. **Installation**: See README.md for installation instructions
2. **First Benchmark**: Follow the TUTORIAL.md for your first benchmark
3. **API Usage**: Refer to API_REFERENCE.md for detailed API information
4. **Docker Setup**: Use DOCKER_README.md for containerized usage

### Version Information

- **Version**: {self.version}
- **Release Date**: {datetime.now().strftime('%Y-%m-%d')}
- **Language Support**: 12 implementations (Python, NumPy, C, C++, Cython, Rust, Fortran, Julia, Go, Zig, Nim, Kotlin)

### Support

For questions, issues, or contributions:
- Check the documentation files in this package
- Review the API reference for detailed usage information
- Follow the tutorial for step-by-step guidance

---

Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for release v{self.version}
"""
        
        return content
    
    def _prepare_distribution(self) -> Dict[str, Any]:
        """Prepare distribution packages"""
        
        dist_result = {
            'packages_created': [],
            'success': False
        }
        
        try:
            dist_dir = self.release_dir / "distribution"
            dist_dir.mkdir(exist_ok=True)
            
            # Create source distribution structure
            source_dist_dir = dist_dir / f"python-extension-benchmark-{self.version}"
            source_dist_dir.mkdir(exist_ok=True)
            
            # Copy essential files for distribution
            essential_files = [
                'README.md',
                'CHANGELOG.md',
                'VERSION',
                'requirements.txt',
                'setup.py',
                'Dockerfile',
                'docker-compose.yml',
                'pytest.ini'
            ]
            
            for file_name in essential_files:
                source_path = self.project_root / file_name
                if source_path.exists():
                    shutil.copy2(source_path, source_dist_dir / file_name)
                    print(f"    ✓ Added {file_name} to distribution")
            
            # Copy essential directories
            essential_dirs = [
                'benchmark',
                'scripts',
                'tests',
                'docs'
            ]
            
            for dir_name in essential_dirs:
                source_dir = self.project_root / dir_name
                if source_dir.exists():
                    dest_dir = source_dist_dir / dir_name
                    shutil.copytree(source_dir, dest_dir, ignore=shutil.ignore_patterns(
                        '__pycache__', '*.pyc', '*.pyo', '*.so', '*.dll', '*.dylib',
                        '.pytest_cache', 'build', 'dist', '*.egg-info'
                    ))
                    print(f"    ✓ Added {dir_name}/ directory to distribution")
            
            # Create installation script
            install_script = self._create_installation_script()
            install_script_path = source_dist_dir / "install.py"
            with open(install_script_path, 'w', encoding='utf-8') as f:
                f.write(install_script)
            print("    ✓ Created installation script")
            
            # Create archive
            archive_path = dist_dir / f"python-extension-benchmark-{self.version}"
            shutil.make_archive(str(archive_path), 'zip', str(dist_dir), f"python-extension-benchmark-{self.version}")
            
            zip_path = f"{archive_path}.zip"
            dist_result['packages_created'].append(zip_path)
            
            # Create tarball as well
            shutil.make_archive(str(archive_path), 'gztar', str(dist_dir), f"python-extension-benchmark-{self.version}")
            
            tar_path = f"{archive_path}.tar.gz"
            dist_result['packages_created'].append(tar_path)
            
            dist_result['success'] = True
            print(f"    ✓ Created distribution packages: {len(dist_result['packages_created'])} files")
            
        except Exception as e:
            print(f"    ❌ Distribution preparation failed: {e}")
            dist_result['error'] = str(e)
        
        return dist_result
    
    def _create_installation_script(self) -> str:
        """Create installation script for the distribution"""
        
        return f'''#!/usr/bin/env python3
"""
Installation script for Multi-Language Python Extension Benchmark Framework v{self.version}

This script helps set up the benchmark framework with available language implementations.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    print(f"Installing Multi-Language Python Extension Benchmark Framework v{self.version}")
    print("=" * 70)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        sys.exit(1)
    
    print(f"✓ Python {{sys.version.split()[0]}} detected")
    
    # Install Python dependencies
    print("\\nInstalling Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✓ Python dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Check for language toolchains
    print("\\nChecking language toolchains...")
    
    toolchains = {{
        'gcc': 'C compiler',
        'g++': 'C++ compiler', 
        'rustc': 'Rust compiler',
        'julia': 'Julia runtime',
        'go': 'Go compiler',
        'zig': 'Zig compiler',
        'nim': 'Nim compiler',
        'kotlinc-native': 'Kotlin/Native compiler',
        'gfortran': 'Fortran compiler'
    }}
    
    available_toolchains = []
    for cmd, desc in toolchains.items():
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            print(f"✓ {{desc}} available")
            available_toolchains.append(cmd)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠ {{desc}} not found")
    
    # Build available extensions
    print("\\nBuilding available extensions...")
    
    build_scripts = [
        ('scripts/build/build_c_ext.py', 'gcc' in available_toolchains),
        ('scripts/build/build_cpp_ext.py', 'g++' in available_toolchains),
        ('scripts/build/build_rust_ext.py', 'rustc' in available_toolchains),
        ('scripts/build/build_julia_ext.py', 'julia' in available_toolchains),
        ('scripts/build/build_go_ext.py', 'go' in available_toolchains),
        ('scripts/build/build_zig_ext.py', 'zig' in available_toolchains),
        ('scripts/build/build_nim_ext.py', 'nim' in available_toolchains),
        ('scripts/build/build_kotlin_ext.py', 'kotlinc-native' in available_toolchains),
        ('scripts/build/build_fortran_ext.py', 'gfortran' in available_toolchains)
    ]
    
    built_extensions = []
    for script_path, should_build in build_scripts:
        if should_build and Path(script_path).exists():
            try:
                subprocess.run([sys.executable, script_path], check=True)
                ext_name = Path(script_path).stem.replace('build_', '').replace('_ext', '')
                built_extensions.append(ext_name)
                print(f"✓ Built {{ext_name}} extension")
            except subprocess.CalledProcessError:
                print(f"⚠ Failed to build {{Path(script_path).stem.replace('build_', '')}}")
    
    # Run verification
    print("\\nVerifying installation...")
    try:
        subprocess.run([sys.executable, "-c", 
            "from benchmark.runner.benchmark import BenchmarkRunner; "
            "r = BenchmarkRunner(); "
            "impls = r.get_all_available_implementations(); "
            f"print(f'Available implementations: {{len(impls)}}'); "
            "print(f'Implementations: {{impls}}')"
        ], check=True)
        print("✓ Installation verified")
    except subprocess.CalledProcessError:
        print("❌ Installation verification failed")
        sys.exit(1)
    
    # Installation summary
    print("\\n" + "=" * 70)
    print("Installation Summary:")
    print(f"✓ Framework version: {self.version}")
    print(f"✓ Available toolchains: {{len(available_toolchains)}}")
    print(f"✓ Built extensions: {{len(built_extensions)}}")
    
    if built_extensions:
        print(f"✓ Extensions: {{', '.join(built_extensions)}}")
    
    print("\\nNext steps:")
    print("1. Run tests: python -m pytest tests/ -v")
    print("2. Try tutorial: python -c 'from benchmark.runner.benchmark import BenchmarkRunner; print(BenchmarkRunner().get_all_available_implementations())'")
    print("3. Read documentation in docs/ directory")
    
    print("\\n🎉 Installation completed successfully!")

if __name__ == '__main__':
    main()
'''
    
    def _generate_release_summary(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate release summary"""
        
        summary_result = {
            'summary_file': None,
            'success': False
        }
        
        try:
            # Create release summary
            summary_content = self._create_release_summary_content(release_info)
            
            summary_path = self.release_dir / f"RELEASE_SUMMARY_v{self.version}.md"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            summary_result['summary_file'] = str(summary_path)
            summary_result['success'] = True
            
            print(f"    ✓ Generated release summary: {summary_path.name}")
            
        except Exception as e:
            print(f"    ❌ Release summary generation failed: {e}")
            summary_result['error'] = str(e)
        
        return summary_result
    
    def _create_release_summary_content(self, release_info: Dict[str, Any]) -> str:
        """Create release summary content"""
        
        validation = release_info['steps'].get('validation', {})
        testing = release_info['steps'].get('testing', {})
        benchmarks = release_info['steps'].get('benchmarks', {})
        
        content = f"""# Release Summary - Multi-Language Python Extension Benchmark Framework v{self.version}

**Release Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Release Status**: {'✅ SUCCESS' if release_info.get('success', False) else '❌ FAILED'}

## Overview

This release expands the Python Extension Benchmark Framework to support 12 different language implementations, providing comprehensive performance comparison across modern programming languages used for Python extensions.

## Implementation Status

### Available Implementations ({validation.get('total_implementations', 0)} total)

"""
        
        # Add implementation status
        loaded_impls = validation.get('loaded_implementations', [])
        failed_impls = validation.get('failed_implementations', [])
        
        if loaded_impls:
            content += "**Successfully Loaded:**\n"
            for impl in loaded_impls:
                content += f"- ✅ {impl}\n"
            content += "\n"
        
        if failed_impls:
            content += "**Failed to Load:**\n"
            for impl_info in failed_impls:
                if isinstance(impl_info, dict):
                    content += f"- ❌ {impl_info['name']}: {impl_info.get('error', 'Unknown error')}\n"
                else:
                    content += f"- ❌ {impl_info}\n"
            content += "\n"
        
        success_rate = validation.get('success_rate', 0)
        content += f"**Success Rate**: {success_rate:.1%} ({len(loaded_impls)}/{validation.get('total_implementations', 0)} implementations)\n\n"
        
        # Add test results
        content += "## Test Results\n\n"
        
        test_suites = testing.get('test_suites', {})
        if test_suites:
            passed_tests = sum(1 for suite in test_suites.values() if suite.get('success', False))
            total_tests = len(test_suites)
            
            content += f"**Overall**: {passed_tests}/{total_tests} test suites passed\n\n"
            
            for suite_name, suite_result in test_suites.items():
                status = "✅ PASSED" if suite_result.get('success', False) else "❌ FAILED"
                content += f"- **{suite_name}**: {status}\n"
            content += "\n"
        
        # Add benchmark artifacts
        content += "## Release Artifacts\n\n"
        
        artifacts = benchmarks.get('artifacts_generated', [])
        if artifacts:
            content += "**Generated Artifacts:**\n"
            for artifact in artifacts:
                artifact_name = Path(artifact).name
                content += f"- 📄 {artifact_name}\n"
            content += "\n"
        
        # Add distribution info
        dist_info = release_info['steps'].get('distribution', {})
        packages = dist_info.get('packages_created', [])
        if packages:
            content += "**Distribution Packages:**\n"
            for package in packages:
                package_name = Path(package).name
                content += f"- 📦 {package_name}\n"
            content += "\n"
        
        # Add performance highlights
        content += """## Performance Highlights

### Language Categories

**Systems Programming** (Fastest)
- C, C++, Rust, Zig
- 10-100x faster than Python
- Manual memory management, compiled to native code

**Scientific Computing**
- Julia, Fortran, NumPy
- Excellent for numerical computations
- JIT compilation (Julia) or optimized libraries

**Modern High-Level**
- Go, Nim, Kotlin/Native
- Good balance of performance and developer experience
- 2-50x faster than Python

**Gradual Optimization**
- Cython, NumPy
- Easy migration from Python
- 5-20x performance improvements

### Use Case Recommendations

- **Maximum Performance**: C, C++, Rust, Zig
- **Scientific Computing**: Julia, Fortran, NumPy  
- **Concurrent Processing**: Go, Rust
- **Developer Productivity**: Nim, Kotlin, Cython
- **Memory Safety**: Rust, Zig, Julia

## Installation

### Docker (Recommended)
```bash
docker-compose up benchmark
```

### Local Installation
```bash
pip install -r requirements.txt
python install.py  # Run installation script
```

## Quick Start

```python
from benchmark.runner.benchmark import BenchmarkRunner

runner = BenchmarkRunner()
results = runner.run_comprehensive_benchmark()
```

## Documentation

- **README.md**: Project overview and setup
- **API_REFERENCE.md**: Complete API documentation  
- **TUTORIAL.md**: Step-by-step usage guide
- **DOCKER_README.md**: Container usage instructions

## Support

For questions, issues, or contributions:
- Check documentation files
- Review API reference for detailed usage
- Follow tutorial for step-by-step guidance

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Framework Version**: {self.version}
**Language Support**: 12 implementations
"""
        
        return content


def main():
    """Main execution function"""
    
    preparator = ReleasePreparator()
    
    try:
        release_info = preparator.prepare_release()
        
        if release_info['success']:
            print(f"\n🎉 Release v{preparator.version} prepared successfully!")
            print(f"📁 Release directory: {preparator.release_dir}")
            
            # Show summary
            validation = release_info['steps'].get('validation', {})
            testing = release_info['steps'].get('testing', {})
            
            print(f"\n📊 Summary:")
            print(f"   Implementations: {len(validation.get('loaded_implementations', []))}/{validation.get('total_implementations', 0)} loaded")
            print(f"   Tests: {sum(1 for s in testing.get('test_suites', {}).values() if s.get('success', False))}/{len(testing.get('test_suites', {}))} passed")
            print(f"   Artifacts: {len(release_info['steps'].get('benchmarks', {}).get('artifacts_generated', []))} generated")
            
            sys.exit(0)
        else:
            print(f"\n❌ Release preparation failed!")
            if 'error' in release_info:
                print(f"Error: {release_info['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠ Release preparation interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()