"""
Scientific Computing Performance Verification

This module verifies the numerical accuracy and performance characteristics
of Fortran and Julia FFI implementations for scientific computing tasks.
"""

import time
import math
import numpy as np
from typing import List, Tuple, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScientificVerification:
    """Verifies scientific computing accuracy and performance."""
    
    def __init__(self):
        self.tolerance = 1e-10  # Numerical tolerance for floating-point comparisons
        self.results = {}
    
    def verify_numerical_accuracy(self, ffi_impl, implementation_name: str) -> Dict[str, bool]:
        """Verify numerical accuracy of FFI implementation.
        
        Args:
            ffi_impl: FFI implementation instance
            implementation_name: Name of the implementation
            
        Returns:
            Dictionary of test results
        """
        logger.info(f"Verifying numerical accuracy for {implementation_name}")
        
        results = {}
        
        # Test 1: Prime number accuracy
        try:
            primes_ffi = ffi_impl.find_primes(100)
            primes_expected = self._sieve_of_eratosthenes(100)
            results['primes_accuracy'] = primes_ffi == primes_expected
            logger.info(f"Primes accuracy: {results['primes_accuracy']}")
        except Exception as e:
            logger.error(f"Primes test failed: {e}")
            results['primes_accuracy'] = False
        
        # Test 2: Matrix multiplication accuracy
        try:
            a = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
            b = [[7.0, 8.0], [9.0, 10.0], [11.0, 12.0]]
            result_ffi = ffi_impl.matrix_multiply(a, b)
            result_expected = self._matrix_multiply_reference(a, b)
            results['matrix_accuracy'] = self._matrices_equal(result_ffi, result_expected, self.tolerance)
            logger.info(f"Matrix accuracy: {results['matrix_accuracy']}")
        except Exception as e:
            logger.error(f"Matrix test failed: {e}")
            results['matrix_accuracy'] = False
        
        # Test 3: Sorting accuracy
        try:
            test_array = [64, 34, 25, 12, 22, 11, 90, 5]
            sorted_ffi = ffi_impl.sort_array(test_array)
            sorted_expected = sorted(test_array)
            results['sorting_accuracy'] = sorted_ffi == sorted_expected
            logger.info(f"Sorting accuracy: {results['sorting_accuracy']}")
        except Exception as e:
            logger.error(f"Sorting test failed: {e}")
            results['sorting_accuracy'] = False
        
        # Test 4: Filtering accuracy
        try:
            test_array = [1, 5, 3, 8, 2, 9, 4, 7, 6]
            threshold = 5
            filtered_ffi = ffi_impl.filter_array(test_array, threshold)
            filtered_expected = [x for x in test_array if x >= threshold]
            results['filtering_accuracy'] = sorted(filtered_ffi) == sorted(filtered_expected)
            logger.info(f"Filtering accuracy: {results['filtering_accuracy']}")
        except Exception as e:
            logger.error(f"Filtering test failed: {e}")
            results['filtering_accuracy'] = False
        
        # Test 5: Parallel computation accuracy
        try:
            test_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
            sum_ffi = ffi_impl.parallel_compute(test_data, 2)
            sum_expected = sum(test_data)
            results['parallel_accuracy'] = abs(sum_ffi - sum_expected) < self.tolerance
            logger.info(f"Parallel computation accuracy: {results['parallel_accuracy']}")
        except Exception as e:
            logger.error(f"Parallel computation test failed: {e}")
            results['parallel_accuracy'] = False
        
        return results
    
    def verify_scientific_features(self, ffi_impl, implementation_name: str) -> Dict[str, Any]:
        """Verify scientific computing specific features.
        
        Args:
            ffi_impl: FFI implementation instance
            implementation_name: Name of the implementation
            
        Returns:
            Dictionary of feature verification results
        """
        logger.info(f"Verifying scientific features for {implementation_name}")
        
        results = {}
        
        # Test large prime computation (scientific scale)
        try:
            start_time = time.time()
            large_primes = ffi_impl.find_primes(10000)
            end_time = time.time()
            
            results['large_prime_count'] = len(large_primes)
            results['large_prime_time'] = end_time - start_time
            results['large_prime_success'] = len(large_primes) > 1000  # Should find many primes
            logger.info(f"Large primes: {len(large_primes)} found in {end_time - start_time:.4f}s")
        except Exception as e:
            logger.error(f"Large prime test failed: {e}")
            results['large_prime_success'] = False
        
        # Test large matrix operations (scientific scale)
        try:
            # Create larger matrices for scientific computing test
            size = 50
            a = [[float(i * size + j) for j in range(size)] for i in range(size)]
            b = [[float(j * size + i) for j in range(size)] for i in range(size)]
            
            start_time = time.time()
            result = ffi_impl.matrix_multiply(a, b)
            end_time = time.time()
            
            results['large_matrix_size'] = f"{size}x{size}"
            results['large_matrix_time'] = end_time - start_time
            results['large_matrix_success'] = len(result) == size and len(result[0]) == size
            logger.info(f"Large matrix ({size}x{size}): completed in {end_time - start_time:.4f}s")
        except Exception as e:
            logger.error(f"Large matrix test failed: {e}")
            results['large_matrix_success'] = False
        
        # Test numerical stability with edge cases
        try:
            # Test with very small numbers
            small_data = [1e-10, 2e-10, 3e-10, 4e-10, 5e-10]
            small_sum = ffi_impl.parallel_compute(small_data, 1)
            expected_small = sum(small_data)
            
            # Test with very large numbers
            large_data = [1e10, 2e10, 3e10, 4e10, 5e10]
            large_sum = ffi_impl.parallel_compute(large_data, 1)
            expected_large = sum(large_data)
            
            results['small_number_accuracy'] = abs(small_sum - expected_small) < 1e-15
            results['large_number_accuracy'] = abs(large_sum - expected_large) < 1e5
            results['numerical_stability'] = results['small_number_accuracy'] and results['large_number_accuracy']
            
            logger.info(f"Numerical stability: {results['numerical_stability']}")
        except Exception as e:
            logger.error(f"Numerical stability test failed: {e}")
            results['numerical_stability'] = False
        
        return results
    
    def compare_with_pure_python(self, ffi_impl, implementation_name: str) -> Dict[str, float]:
        """Compare performance with Pure Python implementations.
        
        Args:
            ffi_impl: FFI implementation instance
            implementation_name: Name of the implementation
            
        Returns:
            Dictionary of performance ratios (FFI_time / Python_time)
        """
        logger.info(f"Comparing {implementation_name} performance with Pure Python")
        
        results = {}
        
        # Prime finding comparison
        try:
            n = 5000
            
            # Pure Python timing
            start_time = time.time()
            python_primes = self._sieve_of_eratosthenes(n)
            python_time = time.time() - start_time
            
            # FFI timing
            start_time = time.time()
            ffi_primes = ffi_impl.find_primes(n)
            ffi_time = time.time() - start_time
            
            results['prime_speedup'] = python_time / ffi_time if ffi_time > 0 else float('inf')
            logger.info(f"Prime finding speedup: {results['prime_speedup']:.2f}x")
        except Exception as e:
            logger.error(f"Prime comparison failed: {e}")
            results['prime_speedup'] = 0.0
        
        # Matrix multiplication comparison
        try:
            size = 30
            a = [[float(i * size + j) for j in range(size)] for i in range(size)]
            b = [[float(j * size + i) for j in range(size)] for i in range(size)]
            
            # Pure Python timing
            start_time = time.time()
            python_result = self._matrix_multiply_reference(a, b)
            python_time = time.time() - start_time
            
            # FFI timing
            start_time = time.time()
            ffi_result = ffi_impl.matrix_multiply(a, b)
            ffi_time = time.time() - start_time
            
            results['matrix_speedup'] = python_time / ffi_time if ffi_time > 0 else float('inf')
            logger.info(f"Matrix multiplication speedup: {results['matrix_speedup']:.2f}x")
        except Exception as e:
            logger.error(f"Matrix comparison failed: {e}")
            results['matrix_speedup'] = 0.0
        
        # Sorting comparison
        try:
            test_array = list(range(10000, 0, -1))  # Reverse sorted array (worst case)
            
            # Pure Python timing
            start_time = time.time()
            python_sorted = sorted(test_array)
            python_time = time.time() - start_time
            
            # FFI timing
            start_time = time.time()
            ffi_sorted = ffi_impl.sort_array(test_array)
            ffi_time = time.time() - start_time
            
            results['sort_speedup'] = python_time / ffi_time if ffi_time > 0 else float('inf')
            logger.info(f"Sorting speedup: {results['sort_speedup']:.2f}x")
        except Exception as e:
            logger.error(f"Sorting comparison failed: {e}")
            results['sort_speedup'] = 0.0
        
        return results
    
    def _sieve_of_eratosthenes(self, n: int) -> List[int]:
        """Reference implementation of Sieve of Eratosthenes."""
        if n < 2:
            return []
        
        is_prime = [True] * (n + 1)
        is_prime[0] = is_prime[1] = False
        
        for i in range(2, int(math.sqrt(n)) + 1):
            if is_prime[i]:
                for j in range(i * i, n + 1, i):
                    is_prime[j] = False
        
        return [i for i in range(2, n + 1) if is_prime[i]]
    
    def _matrix_multiply_reference(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Reference implementation of matrix multiplication."""
        rows_a, cols_a = len(a), len(a[0])
        rows_b, cols_b = len(b), len(b[0])
        
        if cols_a != rows_b:
            raise ValueError("Matrix dimensions incompatible")
        
        result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
        
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    result[i][j] += a[i][k] * b[k][j]
        
        return result
    
    def _matrices_equal(self, a: List[List[float]], b: List[List[float]], tolerance: float) -> bool:
        """Check if two matrices are equal within tolerance."""
        if len(a) != len(b) or len(a[0]) != len(b[0]):
            return False
        
        for i in range(len(a)):
            for j in range(len(a[0])):
                if abs(a[i][j] - b[i][j]) > tolerance:
                    return False
        
        return True
    
    def run_comprehensive_verification(self, ffi_implementations: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Run comprehensive verification for all FFI implementations.
        
        Args:
            ffi_implementations: Dictionary of FFI implementation instances
            
        Returns:
            Comprehensive verification results
        """
        logger.info("Starting comprehensive scientific computing verification")
        
        all_results = {}
        
        for name, impl in ffi_implementations.items():
            if not impl.is_available():
                logger.warning(f"Skipping {name} - not available")
                continue
            
            logger.info(f"Verifying {name}")
            
            impl_results = {
                'accuracy': self.verify_numerical_accuracy(impl, name),
                'scientific_features': self.verify_scientific_features(impl, name),
                'performance_comparison': self.compare_with_pure_python(impl, name)
            }
            
            # Calculate overall scores
            accuracy_score = sum(impl_results['accuracy'].values()) / len(impl_results['accuracy'])
            feature_score = sum(1 for v in impl_results['scientific_features'].values() 
                              if isinstance(v, bool) and v) / len([v for v in impl_results['scientific_features'].values() if isinstance(v, bool)])
            
            impl_results['overall_accuracy'] = accuracy_score
            impl_results['overall_features'] = feature_score
            
            all_results[name] = impl_results
            
            logger.info(f"{name} - Accuracy: {accuracy_score:.2%}, Features: {feature_score:.2%}")
        
        return all_results
    
    def generate_verification_report(self, results: Dict[str, Dict[str, Any]]) -> str:
        """Generate a comprehensive verification report.
        
        Args:
            results: Verification results from run_comprehensive_verification
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("# Scientific Computing Performance Verification Report")
        report.append("")
        report.append("## Summary")
        report.append("")
        
        for impl_name, impl_results in results.items():
            accuracy = impl_results.get('overall_accuracy', 0)
            features = impl_results.get('overall_features', 0)
            
            report.append(f"### {impl_name}")
            report.append(f"- **Accuracy Score**: {accuracy:.1%}")
            report.append(f"- **Feature Score**: {features:.1%}")
            
            # Performance summary
            perf = impl_results.get('performance_comparison', {})
            if perf:
                report.append("- **Performance vs Pure Python**:")
                for metric, speedup in perf.items():
                    if speedup > 0:
                        report.append(f"  - {metric}: {speedup:.1f}x faster")
                    else:
                        report.append(f"  - {metric}: Failed")
            
            report.append("")
        
        report.append("## Detailed Results")
        report.append("")
        
        for impl_name, impl_results in results.items():
            report.append(f"### {impl_name} Detailed Results")
            report.append("")
            
            # Accuracy details
            report.append("#### Numerical Accuracy")
            for test, result in impl_results.get('accuracy', {}).items():
                status = "✓ PASS" if result else "✗ FAIL"
                report.append(f"- {test}: {status}")
            report.append("")
            
            # Scientific features
            report.append("#### Scientific Computing Features")
            for feature, result in impl_results.get('scientific_features', {}).items():
                if isinstance(result, bool):
                    status = "✓ PASS" if result else "✗ FAIL"
                    report.append(f"- {feature}: {status}")
                else:
                    report.append(f"- {feature}: {result}")
            report.append("")
            
            # Performance details
            report.append("#### Performance Comparison")
            for metric, speedup in impl_results.get('performance_comparison', {}).items():
                if speedup > 0:
                    report.append(f"- {metric}: {speedup:.2f}x speedup")
                else:
                    report.append(f"- {metric}: Failed to measure")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main function for running scientific verification."""
    # Import FFI implementations
    try:
        from .fortran_ffi import FortranFFI
        from .julia_ffi import JuliaFFI
        
        # Initialize implementations
        implementations = {
            'Fortran FFI': FortranFFI(skip_uv_check=True),
            'Julia FFI': JuliaFFI(skip_uv_check=True)
        }
        
        # Run verification
        verifier = ScientificVerification()
        results = verifier.run_comprehensive_verification(implementations)
        
        # Generate and print report
        report = verifier.generate_verification_report(results)
        print(report)
        
        # Save report to file
        with open('scientific_verification_report.md', 'w') as f:
            f.write(report)
        
        logger.info("Verification completed. Report saved to scientific_verification_report.md")
        
    except ImportError as e:
        logger.error(f"Failed to import FFI implementations: {e}")
        logger.info("Please ensure Fortran and Julia FFI implementations are built")


if __name__ == "__main__":
    main()