#!/usr/bin/env python3
"""
Example: Basic File Operations

This script demonstrates how to use the File Operations module
to perform common file system operations.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.file_operations import FileOperations


async def main():
    """Demonstrate file operations"""
    print("📁 File Operations Example")
    print("=" * 40)
    
    # Initialize file operations
    file_ops = FileOperations()
    await file_ops.initialize()
    
    try:
        # Example 1: Create a new file
        print("\n1. Creating a new file...")
        result = await file_ops.create_file(
            "example.txt", 
            "Hello, AI Developer Assistant!\nThis is a test file."
        )
        if result["success"]:
            print(f"✅ File created: {result['path']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 2: Read the file
        print("\n2. Reading the file...")
        result = await file_ops.read_file("example.txt")
        if result["success"]:
            print(f"✅ File content:\n{result['content']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 3: List directory contents
        print("\n3. Listing directory contents...")
        result = await file_ops.list_directory(".")
        if result["success"]:
            print(f"✅ Directory contents:")
            for item in result["items"]:
                print(f"  - {item['name']} ({item['type']}, {item['size']} bytes)")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 4: Create a directory
        print("\n4. Creating a new directory...")
        result = await file_ops.create_directory("test_dir")
        if result["success"]:
            print(f"✅ Directory created: {result['path']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 5: Copy file
        print("\n5. Copying a file...")
        result = await file_ops.copy_file("example.txt", "test_dir/example_copy.txt")
        if result["success"]:
            print(f"✅ File copied from {result['source']} to {result['destination']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 6: Search for files
        print("\n6. Searching for files...")
        result = await file_ops.search_files("*.txt")
        if result["success"]:
            print(f"✅ Found {len(result['matches'])} text files:")
            for match in result["matches"]:
                print(f"  - {match['path']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 7: Get file information
        print("\n7. Getting file information...")
        result = await file_ops.get_file_info("example.txt")
        if result["success"]:
            info = result
            print(f"✅ File information:")
            print(f"  - Name: {info['name']}")
            print(f"  - Size: {info['size']} bytes")
            print(f"  - Type: {info['mime_type']}")
            print(f"  - Modified: {info['modified']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 8: Directory tree
        print("\n8. Getting directory tree...")
        result = await file_ops.read_directory_tree(".")
        if result["success"]:
            print(f"✅ Directory tree structure:")
            print_tree(result["tree"])
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 9: Delete file
        print("\n9. Deleting files...")
        result = await file_ops.delete_file("example.txt")
        if result["success"]:
            print(f"✅ File deleted: {result['path']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 10: Delete directory
        print("\n10. Deleting directory...")
        result = await file_ops.delete_directory("test_dir")
        if result["success"]:
            print(f"✅ Directory deleted: {result['path']}")
        else:
            print(f"❌ Error: {result['error']}")
        
    finally:
        # Clean up
        await file_ops.stop()
    
    print("\n✅ File operations example completed!")


def print_tree(tree, indent=0):
    """Print directory tree structure"""
    prefix = "  " * indent
    print(f"{prefix}📁 {tree['name']}")
    for child in tree.get("children", []):
        if child["type"] == "directory":
            print_tree(child, indent + 1)
        else:
            print(f"{'  ' * (indent + 1)}📄 {child['name']} ({child['size']} bytes)")


if __name__ == "__main__":
    asyncio.run(main())