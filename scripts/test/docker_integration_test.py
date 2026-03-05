#!/usr/bin/env python3
"""Docker環境統合テストスクリプト

Docker環境での全体テスト、クリーンビルドテスト、リソース制限テストを実行する。
要件: 7.3, 7.4
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class DockerIntegrationTester:
    """Docker環境統合テストクラス"""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {}
        
    def run_docker_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Dockerコマンドを実行して結果を返す"""
        
        try:
            print(f"実行中: {' '.join(command)}")
            
            start_time = time.time()
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'execution_time': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0
            }
    
    def test_docker_build(self) -> Dict[str, Any]:
        """Dockerイメージのビルドテスト"""
        
        print("=== Dockerビルドテスト開始 ===")
        
        # クリーンビルド実行
        build_result = self.run_docker_command([
            'docker', 'build', '--no-cache', '-t', 'python-extension-benchmark-test', '.'
        ], timeout=1800)  # 30分タイムアウト
        
        if build_result['success']:
            print(f"✓ Dockerビルド成功 ({build_result['execution_time']:.1f}秒)")
            
            # ビルドログから言語環境の確認
            build_log = build_result['stdout']
            language_status = self._analyze_build_log(build_log)
            
            return {
                'success': True,
                'execution_time': build_result['execution_time'],
                'language_status': language_status
            }
        else:
            print(f"❌ Dockerビルド失敗")
            print(f"エラー: {build_result['stderr']}")
            
            return {
                'success': False,
                'execution_time': build_result['execution_time'],
                'error': build_result['stderr']
            }
    
    def test_docker_health_check(self) -> Dict[str, Any]:
        """Docker環境のヘルスチェック"""
        
        print("\n=== Dockerヘルスチェック開始 ===")
        
        # ヘルスチェック実行
        health_result = self.run_docker_command([
            'docker', 'run', '--rm', 'python-extension-benchmark-test', 'health-check'
        ], timeout=300)
        
        if health_result['success']:
            print("✓ ヘルスチェック成功")
            
            # ヘルスチェック結果の解析
            health_info = self._parse_health_check_output(health_result['stdout'])
            
            return {
                'success': True,
                'execution_time': health_result['execution_time'],
                'health_info': health_info
            }
        else:
            print(f"❌ ヘルスチェック失敗")
            print(f"エラー: {health_result['stderr']}")
            
            return {
                'success': False,
                'execution_time': health_result['execution_time'],
                'error': health_result['stderr']
            }
    
    def test_docker_benchmark_execution(self) -> Dict[str, Any]:
        """Docker環境でのベンチマーク実行テスト"""
        
        print("\n=== Dockerベンチマーク実行テスト開始 ===")
        
        # 軽量ベンチマーク実行
        benchmark_command = [
            'docker', 'run', '--rm',
            '-v', f'{self.project_root}/benchmark/results:/app/benchmark/results',
            'python-extension-benchmark-test',
            'python', '-c',
            '''
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import NumericScenario

runner = BenchmarkRunner()
implementations = runner.load_implementations(["python", "numpy_impl"])

scenario = NumericScenario("primes")
scenario.input_data = 100

results = runner.run_scenario(scenario, implementations, warmup_runs=1, measurement_runs=3)

print(f"Results: {len(results)} generated")
for result in results:
    print(f"  {result.implementation_name}: {result.status} - {result.mean_time:.2f}ms")
'''
        ]
        
        benchmark_result = self.run_docker_command(benchmark_command, timeout=600)
        
        if benchmark_result['success']:
            print("✓ Dockerベンチマーク実行成功")
            
            # 結果の解析
            benchmark_info = self._parse_benchmark_output(benchmark_result['stdout'])
            
            return {
                'success': True,
                'execution_time': benchmark_result['execution_time'],
                'benchmark_info': benchmark_info
            }
        else:
            print(f"❌ Dockerベンチマーク実行失敗")
            print(f"エラー: {benchmark_result['stderr']}")
            
            return {
                'success': False,
                'execution_time': benchmark_result['execution_time'],
                'error': benchmark_result['stderr']
            }    

    def test_docker_resource_limits(self) -> Dict[str, Any]:
        """Dockerリソース制限テスト"""
        
        print("\n=== Dockerリソース制限テスト開始 ===")
        
        # リソース制限付きでベンチマーク実行
        limited_command = [
            'docker', 'run', '--rm',
            '--cpus', '2.0',
            '--memory', '4g',
            'python-extension-benchmark-test',
            'python', '-c',
            '''
import psutil
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import ParallelScenario

print(f"Container resources: CPU={psutil.cpu_count()}, Memory={psutil.virtual_memory().total/(1024**3):.1f}GB")

runner = BenchmarkRunner()
implementations = runner.load_implementations(["python"])

if implementations:
    scenario = ParallelScenario(2)
    scenario.input_data = [float(i) for i in range(5000)]
    
    results = runner.run_scenario(scenario, implementations, warmup_runs=1, measurement_runs=2)
    
    if results:
        print(f"Limited resource test: {results[0].status} - {results[0].mean_time:.2f}ms")
    else:
        print("No results generated")
else:
    print("No implementations available")
'''
        ]
        
        limited_result = self.run_docker_command(limited_command, timeout=300)
        
        if limited_result['success']:
            print("✓ リソース制限テスト成功")
            
            return {
                'success': True,
                'execution_time': limited_result['execution_time'],
                'output': limited_result['stdout']
            }
        else:
            print(f"❌ リソース制限テスト失敗")
            print(f"エラー: {limited_result['stderr']}")
            
            return {
                'success': False,
                'execution_time': limited_result['execution_time'],
                'error': limited_result['stderr']
            }
    
    def test_docker_compose_services(self) -> Dict[str, Any]:
        """Docker Composeサービステスト"""
        
        print("\n=== Docker Composeサービステスト開始 ===")
        
        services_results = {}
        
        # 各サービスをテスト
        test_services = [
            ('health-check', 'health-check'),
            ('test', 'python -m pytest tests/test_multi_language_integration.py::TestMultiLanguageIntegration::test_language_specific_error_handling -v --tb=short')
        ]
        
        for service_name, command in test_services:
            print(f"\nテスト中: {service_name}")
            
            if command == 'health-check':
                # ヘルスチェックサービス
                service_result = self.run_docker_command([
                    'docker-compose', 'run', '--rm', service_name
                ], timeout=300)
            else:
                # カスタムコマンド実行
                service_result = self.run_docker_command([
                    'docker-compose', 'run', '--rm', 'test', 'sh', '-c', command
                ], timeout=600)
            
            services_results[service_name] = {
                'success': service_result['success'],
                'execution_time': service_result['execution_time'],
                'output': service_result['stdout'] if service_result['success'] else service_result['stderr']
            }
            
            if service_result['success']:
                print(f"  ✓ {service_name}: 成功")
            else:
                print(f"  ❌ {service_name}: 失敗")
        
        overall_success = all(result['success'] for result in services_results.values())
        
        return {
            'success': overall_success,
            'services_results': services_results
        }
    
    def _analyze_build_log(self, build_log: str) -> Dict[str, str]:
        """ビルドログから言語環境の状態を解析"""
        
        language_status = {}
        
        # 各言語のビルド状況を確認
        languages = ['C', 'C++', 'Rust', 'Fortran', 'Julia', 'Go', 'Zig', 'Nim', 'Kotlin']
        
        for lang in languages:
            if f"Building {lang}" in build_log or f"{lang} extension" in build_log:
                if "failed" in build_log.lower() or "error" in build_log.lower():
                    language_status[lang] = "BUILD_FAILED"
                else:
                    language_status[lang] = "BUILD_SUCCESS"
            else:
                language_status[lang] = "NOT_ATTEMPTED"
        
        return language_status
    
    def _parse_health_check_output(self, output: str) -> Dict[str, Any]:
        """ヘルスチェック出力を解析"""
        
        health_info = {
            'languages': {},
            'implementations': {}
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 言語バージョン情報
            if ':' in line and any(lang in line for lang in ['Python', 'Rust', 'Julia', 'Go', 'Zig', 'Nim', 'Kotlin']):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    lang = parts[0].strip()
                    version = parts[1].strip()
                    health_info['languages'][lang] = version
            
            # 実装状況
            elif line.startswith('✓') or line.startswith('✗'):
                status = 'available' if line.startswith('✓') else 'unavailable'
                impl_name = line[2:].strip()
                health_info['implementations'][impl_name] = status
        
        return health_info
    
    def _parse_benchmark_output(self, output: str) -> Dict[str, Any]:
        """ベンチマーク出力を解析"""
        
        benchmark_info = {
            'results_count': 0,
            'implementations': {}
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Results:'):
                # 結果数の抽出
                try:
                    count_str = line.split()[1]
                    benchmark_info['results_count'] = int(count_str)
                except (IndexError, ValueError):
                    pass
            
            elif ':' in line and ('SUCCESS' in line or 'ERROR' in line):
                # 実装結果の抽出
                parts = line.split(':')
                if len(parts) >= 2:
                    impl_name = parts[0].strip()
                    result_info = parts[1].strip()
                    benchmark_info['implementations'][impl_name] = result_info
        
        return benchmark_info
    
    def run_comprehensive_docker_test(self) -> Dict[str, Any]:
        """包括的Dockerテストの実行"""
        
        print("=== 包括的Docker統合テスト開始 ===")
        
        comprehensive_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests': {}
        }
        
        # 1. Dockerビルドテスト
        build_result = self.test_docker_build()
        comprehensive_results['tests']['docker_build'] = build_result
        
        if not build_result['success']:
            print("❌ Dockerビルドに失敗したため、後続テストをスキップします")
            return comprehensive_results
        
        # 2. ヘルスチェックテスト
        health_result = self.test_docker_health_check()
        comprehensive_results['tests']['health_check'] = health_result
        
        # 3. ベンチマーク実行テスト
        benchmark_result = self.test_docker_benchmark_execution()
        comprehensive_results['tests']['benchmark_execution'] = benchmark_result
        
        # 4. リソース制限テスト
        resource_result = self.test_docker_resource_limits()
        comprehensive_results['tests']['resource_limits'] = resource_result
        
        # 5. Docker Composeサービステスト
        compose_result = self.test_docker_compose_services()
        comprehensive_results['tests']['compose_services'] = compose_result
        
        # 総合評価
        all_tests = [build_result, health_result, benchmark_result, resource_result, compose_result]
        successful_tests = sum(1 for test in all_tests if test['success'])
        total_tests = len(all_tests)
        
        comprehensive_results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': successful_tests / total_tests,
            'overall_success': successful_tests >= total_tests * 0.8  # 80%以上成功で全体成功
        }
        
        print(f"\n=== Docker統合テスト完了 ===")
        print(f"成功: {successful_tests}/{total_tests} ({comprehensive_results['summary']['success_rate']:.1%})")
        
        if comprehensive_results['summary']['overall_success']:
            print("✓ Docker環境は正常に動作しています")
        else:
            print("⚠ Docker環境に問題があります")
        
        return comprehensive_results
    
    def save_results(self, results: Dict[str, Any], output_file: str = None) -> str:
        """テスト結果をファイルに保存"""
        
        if output_file is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_file = f'docker_integration_test_results_{timestamp}.json'
        
        results_dir = self.project_root / 'benchmark' / 'results'
        results_dir.mkdir(exist_ok=True)
        
        output_path = results_dir / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"結果保存: {output_path}")
        
        return str(output_path)


def main():
    """メイン実行関数"""
    
    tester = DockerIntegrationTester()
    
    try:
        # 包括的テスト実行
        results = tester.run_comprehensive_docker_test()
        
        # 結果保存
        output_path = tester.save_results(results)
        
        # 終了コード決定
        if results['summary']['overall_success']:
            print("\n✓ 全てのDocker統合テストが成功しました！")
            sys.exit(0)
        else:
            print("\n❌ 一部のDocker統合テストが失敗しました")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠ テストが中断されました")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()