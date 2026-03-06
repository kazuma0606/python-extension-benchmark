#!/usr/bin/env python3
"""
Build FFI Docker image with comprehensive language support.

This script builds the Docker image for FFI benchmarks with all
required language environments and shared libraries.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


class FFIDockerBuilder:
    """Builds FFI Docker images."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        
    def build_ffi_image(
        self, 
        tag: str = "py-benchmark-ffi:latest",
        no_cache: bool = False,
        platform: Optional[str] = None
    ) -> bool:
        """Build the FFI Docker image.
        
        Args:
            tag: Docker image tag
            no_cache: Whether to build without cache
            platform: Target platform (e.g., linux/amd64)
            
        Returns:
            True if build successful, False otherwise
        """
        print("🐳 Building FFI Docker Image")
        print("=" * 50)
        print(f"Tag: {tag}")
        print(f"No cache: {no_cache}")
        print(f"Platform: {platform or 'default'}")
        print()
        
        # Build command
        cmd = [
            'docker', 'build',
            '-f', 'Dockerfile.ffi',
            '-t', tag,
            '.'
        ]
        
        if no_cache:
            cmd.append('--no-cache')
            
        if platform:
            cmd.extend(['--platform', platform])
        
        print(f"🔨 Running: {' '.join(cmd)}")
        print()
        
        try:
            start_time = time.time()
            
            # Run build with real-time output
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output in real-time
            for line in process.stdout:
                print(line.rstrip())
            
            # Wait for completion
            return_code = process.wait()
            
            build_time = time.time() - start_time
            
            if return_code == 0:
                print(f"\n✅ FFI Docker image built successfully!")
                print(f"   Build time: {build_time:.1f} seconds")
                print(f"   Image tag: {tag}")
                return True
            else:
                print(f"\n❌ FFI Docker build failed with return code {return_code}")
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️  Build interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Build failed with error: {e}")
            return False
    
    def build_extension_image(
        self, 
        tag: str = "py-benchmark-ext:latest",
        no_cache: bool = False,
        platform: Optional[str] = None
    ) -> bool:
        """Build the extension-only Docker image.
        
        Args:
            tag: Docker image tag
            no_cache: Whether to build without cache
            platform: Target platform
            
        Returns:
            True if build successful, False otherwise
        """
        print("🐳 Building Extension Docker Image")
        print("=" * 50)
        print(f"Tag: {tag}")
        print(f"No cache: {no_cache}")
        print(f"Platform: {platform or 'default'}")
        print()
        
        cmd = [
            'docker', 'build',
            '-f', 'Dockerfile',
            '-t', tag,
            '.'
        ]
        
        if no_cache:
            cmd.append('--no-cache')
            
        if platform:
            cmd.extend(['--platform', platform])
        
        print(f"🔨 Running: {' '.join(cmd)}")
        print()
        
        try:
            start_time = time.time()
            
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in process.stdout:
                print(line.rstrip())
            
            return_code = process.wait()
            build_time = time.time() - start_time
            
            if return_code == 0:
                print(f"\n✅ Extension Docker image built successfully!")
                print(f"   Build time: {build_time:.1f} seconds")
                print(f"   Image tag: {tag}")
                return True
            else:
                print(f"\n❌ Extension Docker build failed with return code {return_code}")
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️  Build interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Build failed with error: {e}")
            return False
    
    def test_image(self, tag: str) -> bool:
        """Test the built Docker image.
        
        Args:
            tag: Docker image tag to test
            
        Returns:
            True if test successful, False otherwise
        """
        print(f"\n🧪 Testing Docker image: {tag}")
        print("-" * 40)
        
        try:
            # Run health check
            result = subprocess.run([
                'docker', 'run', '--rm', tag, 'health-check-ffi'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Health check passed")
                print(result.stdout)
                return True
            else:
                print("❌ Health check failed")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Health check timed out")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def build_and_test_all(
        self,
        ffi_tag: str = "py-benchmark-ffi:latest",
        ext_tag: str = "py-benchmark-ext:latest",
        no_cache: bool = False,
        platform: Optional[str] = None,
        test_images: bool = True
    ) -> bool:
        """Build and test both Docker images.
        
        Args:
            ffi_tag: FFI image tag
            ext_tag: Extension image tag
            no_cache: Whether to build without cache
            platform: Target platform
            test_images: Whether to test images after building
            
        Returns:
            True if all builds successful, False otherwise
        """
        print("🚀 Building All Docker Images")
        print("=" * 60)
        
        success = True
        
        # Build extension image first (simpler)
        print("1️⃣  Building Extension Image...")
        if not self.build_extension_image(ext_tag, no_cache, platform):
            print("❌ Extension image build failed")
            success = False
        
        # Build FFI image
        print("\n2️⃣  Building FFI Image...")
        if not self.build_ffi_image(ffi_tag, no_cache, platform):
            print("❌ FFI image build failed")
            success = False
        
        # Test images if requested
        if test_images and success:
            print("\n3️⃣  Testing Images...")
            
            if not self.test_image(ext_tag):
                print(f"❌ Extension image test failed: {ext_tag}")
                success = False
            
            if not self.test_image(ffi_tag):
                print(f"❌ FFI image test failed: {ffi_tag}")
                success = False
        
        # Final summary
        print("\n" + "=" * 60)
        if success:
            print("🎉 All Docker images built successfully!")
            print(f"   Extension image: {ext_tag}")
            print(f"   FFI image: {ffi_tag}")
            print("\nUsage:")
            print(f"   docker run --rm {ext_tag}")
            print(f"   docker run --rm {ffi_tag}")
            print(f"   docker-compose -f docker-compose.ffi.yml up")
        else:
            print("❌ Some Docker builds failed. Check logs above.")
        
        print("=" * 60)
        return success


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build FFI Docker images for benchmark system"
    )
    
    parser.add_argument(
        '--mode',
        choices=['ffi', 'extension', 'all'],
        default='all',
        help='Which images to build (default: all)'
    )
    
    parser.add_argument(
        '--ffi-tag',
        default='py-benchmark-ffi:latest',
        help='Tag for FFI image (default: py-benchmark-ffi:latest)'
    )
    
    parser.add_argument(
        '--ext-tag',
        default='py-benchmark-ext:latest',
        help='Tag for extension image (default: py-benchmark-ext:latest)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Build without Docker cache'
    )
    
    parser.add_argument(
        '--platform',
        help='Target platform (e.g., linux/amd64)'
    )
    
    parser.add_argument(
        '--no-test',
        action='store_true',
        help='Skip image testing after build'
    )
    
    args = parser.parse_args()
    
    builder = FFIDockerBuilder()
    
    if args.mode == 'ffi':
        success = builder.build_ffi_image(
            args.ffi_tag, args.no_cache, args.platform
        )
        if not args.no_test and success:
            success = builder.test_image(args.ffi_tag)
    elif args.mode == 'extension':
        success = builder.build_extension_image(
            args.ext_tag, args.no_cache, args.platform
        )
        if not args.no_test and success:
            success = builder.test_image(args.ext_tag)
    else:  # all
        success = builder.build_and_test_all(
            args.ffi_tag, args.ext_tag, args.no_cache, 
            args.platform, not args.no_test
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()