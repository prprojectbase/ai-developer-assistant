"""
Unit tests for File Operations module
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.modules.file_operations import FileOperations
from src.config.settings import get_settings


class TestFileOperations:
    """Test cases for FileOperations class"""
    
    @pytest.fixture
    def file_ops(self):
        """Create a FileOperations instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = get_settings()
            settings.workspace_dir = temp_dir
            ops = FileOperations()
            ops.workspace_dir = Path(temp_dir)
            yield ops
    
    @pytest.fixture
    def sample_content(self):
        """Sample file content for testing"""
        return """def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()"""
    
    @pytest.mark.asyncio
    async def test_initialize(self, file_ops):
        """Test FileOperations initialization"""
        # Patch the logger directly on the instance
        with patch.object(file_ops, 'logger') as mock_logger:
            await file_ops.initialize()
            
            assert file_ops.workspace_dir.exists()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_write_and_read_file(self, file_ops, sample_content):
        """Test writing and reading a file"""
        # Write file
        result = await file_ops.write_file("test.py", sample_content)
        assert result["success"] is True
        assert result["path"] == "test.py"
        assert result["size"] == len(sample_content)
        
        # Read file back
        result = await file_ops.read_file("test.py")
        assert result["success"] is True
        assert result["content"] == sample_content
        assert result["size"] == len(sample_content)
    
    @pytest.mark.asyncio
    async def test_create_file(self, file_ops, sample_content):
        """Test creating a new file"""
        result = await file_ops.create_file("new_file.py", sample_content)
        assert result["success"] is True
        
        # Verify file exists
        file_path = file_ops.workspace_dir / "new_file.py"
        assert file_path.exists()
        
        # Try to create same file again (should fail)
        result = await file_ops.create_file("new_file.py", sample_content)
        assert "error" in result
        assert "already exists" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_file(self, file_ops, sample_content):
        """Test deleting a file"""
        # Create file first
        await file_ops.write_file("to_delete.py", sample_content)
        
        # Delete file
        result = await file_ops.delete_file("to_delete.py")
        assert result["success"] is True
        
        # Verify file is deleted
        file_path = file_ops.workspace_dir / "to_delete.py"
        assert not file_path.exists()
        
        # Try to delete non-existent file
        result = await file_ops.delete_file("nonexistent.py")
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_directory(self, file_ops, sample_content):
        """Test listing directory contents"""
        # Create test files
        await file_ops.write_file("file1.py", sample_content)
        await file_ops.write_file("file2.py", sample_content)
        await file_ops.create_directory("subdir")
        
        # List directory
        result = await file_ops.list_directory(".")
        assert result["success"] is True
        assert len(result["items"]) == 3
        
        # Check items are properly sorted
        item_names = [item["name"] for item in result["items"]]
        assert "file1.py" in item_names
        assert "file2.py" in item_names
        assert "subdir" in item_names
    
    @pytest.mark.asyncio
    async def test_create_and_delete_directory(self, file_ops):
        """Test creating and deleting directories"""
        # Create directory
        result = await file_ops.create_directory("test_dir")
        assert result["success"] is True
        
        # Verify directory exists
        dir_path = file_ops.workspace_dir / "test_dir"
        assert dir_path.exists()
        assert dir_path.is_dir()
        
        # Delete directory
        result = await file_ops.delete_directory("test_dir")
        assert result["success"] is True
        
        # Verify directory is deleted
        assert not dir_path.exists()
    
    @pytest.mark.asyncio
    async def test_copy_file(self, file_ops, sample_content):
        """Test copying files"""
        # Create source file
        await file_ops.write_file("source.py", sample_content)
        
        # Copy file
        result = await file_ops.copy_file("source.py", "destination.py")
        assert result["success"] is True
        
        # Verify both files exist and have same content
        source_path = file_ops.workspace_dir / "source.py"
        dest_path = file_ops.workspace_dir / "destination.py"
        assert source_path.exists()
        assert dest_path.exists()
        
        source_content = source_path.read_text()
        dest_content = dest_path.read_text()
        assert source_content == dest_content == sample_content
    
    @pytest.mark.asyncio
    async def test_move_file(self, file_ops, sample_content):
        """Test moving files"""
        # Create source file
        await file_ops.write_file("source.py", sample_content)
        
        # Move file
        result = await file_ops.move_file("source.py", "moved.py")
        assert result["success"] is True
        
        # Verify source is gone and destination exists
        source_path = file_ops.workspace_dir / "source.py"
        dest_path = file_ops.workspace_dir / "moved.py"
        assert not source_path.exists()
        assert dest_path.exists()
        
        # Verify content is preserved
        moved_content = dest_path.read_text()
        assert moved_content == sample_content
    
    @pytest.mark.asyncio
    async def test_file_exists(self, file_ops, sample_content):
        """Test file existence checking"""
        # Test non-existent file
        result = await file_ops.file_exists("nonexistent.py")
        assert result["success"] is True
        assert result["exists"] is False
        
        # Create file and test
        await file_ops.write_file("exists.py", sample_content)
        result = await file_ops.file_exists("exists.py")
        assert result["success"] is True
        assert result["exists"] is True
        assert result["is_file"] is True
        assert result["is_directory"] is False
    
    @pytest.mark.asyncio
    async def test_get_file_info(self, file_ops, sample_content):
        """Test getting file information"""
        # Create file
        await file_ops.write_file("info_test.py", sample_content)
        
        # Get file info
        result = await file_ops.get_file_info("info_test.py")
        assert result["success"] is True
        assert result["name"] == "info_test.py"
        assert result["size"] == len(sample_content)
        assert result["is_file"] is True
        assert result["is_directory"] is False
        assert "mime_type" in result
        assert "permissions" in result
    
    @pytest.mark.asyncio
    async def test_search_files(self, file_ops, sample_content):
        """Test file searching"""
        # Create test files
        await file_ops.write_file("test1.py", sample_content)
        await file_ops.write_file("test2.py", sample_content)
        await file_ops.write_file("other.txt", "different content")
        await file_ops.create_directory("subdir")
        await file_ops.write_file("subdir/nested.py", sample_content)
        
        # Search for Python files
        result = await file_ops.search_files("*.py", ".")
        assert result["success"] is True
        assert len(result["matches"]) == 3
        
        # Verify matches
        match_names = [match["name"] for match in result["matches"]]
        assert "test1.py" in match_names
        assert "test2.py" in match_names
        assert "nested.py" in match_names
    
    @pytest.mark.asyncio
    async def test_read_directory_tree(self, file_ops, sample_content):
        """Test reading directory tree structure"""
        # Create directory structure
        await file_ops.create_directory("project")
        await file_ops.create_directory("project/src")
        await file_ops.create_directory("project/tests")
        await file_ops.write_file("project/main.py", sample_content)
        await file_ops.write_file("project/src/utils.py", sample_content)
        await file_ops.write_file("project/tests/test_main.py", sample_content)
        
        # Read directory tree
        result = await file_ops.read_directory_tree("project")
        assert result["success"] is True
        
        # Verify tree structure
        tree = result["tree"]
        assert tree["name"] == "project"
        assert tree["type"] == "directory"
        assert len(tree["children"]) == 3
        
        # Find main.py in tree
        main_file = None
        for child in tree["children"]:
            if child["name"] == "main.py":
                main_file = child
                break
        
        assert main_file is not None
        assert main_file["type"] == "file"
        assert main_file["size"] == len(sample_content)
    
    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, file_ops):
        """Test path traversal protection"""
        # Test various path traversal attempts
        malicious_paths = [
            "../etc/passwd",
            "/etc/passwd",
            "..\\windows\\system32\\config\\sam",
            "file/../../etc/passwd"
        ]
        
        for malicious_path in malicious_paths:
            with pytest.raises(ValueError, match="Invalid path"):
                file_ops._get_full_path(malicious_path)
    
    @pytest.mark.asyncio
    async def test_file_size_limit(self, file_ops):
        """Test file size limit enforcement"""
        # Set a small file size limit for testing
        original_limit = file_ops.settings.max_file_size
        file_ops.settings.max_file_size = 100  # 100 bytes
        
        # Create a large file
        large_content = "x" * 200  # 200 bytes
        
        result = await file_ops.write_file("large_file.txt", large_content)
        assert result["success"] is True
        
        # Try to read it back (should fail due to size limit)
        result = await file_ops.read_file("large_file.txt")
        assert "error" in result
        assert "too large" in result["error"]
        
        # Restore original limit
        file_ops.settings.max_file_size = original_limit
    
    @pytest.mark.asyncio
    async def test_execute_operation(self, file_ops, sample_content):
        """Test the execute_operation method"""
        # Test write operation
        result = await file_ops.execute_operation({
            "type": "write_file",
            "path": "exec_test.py",
            "content": sample_content
        })
        assert result["success"] is True
        
        # Test read operation
        result = await file_ops.execute_operation({
            "type": "read_file",
            "path": "exec_test.py"
        })
        assert result["success"] is True
        assert result["content"] == sample_content
        
        # Test unknown operation
        result = await file_ops.execute_operation({
            "type": "unknown_operation"
        })
        assert "error" in result
        assert "Unknown operation type" in result["error"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, file_ops):
        """Test error handling for various scenarios"""
        # Test reading non-existent file
        result = await file_ops.read_file("nonexistent.py")
        assert "error" in result
        assert "not found" in result["error"]
        
        # Test writing to invalid path
        with pytest.raises(ValueError):
            await file_ops.write_file("../invalid.py", "content")
        
        # Test listing non-existent directory
        result = await file_ops.list_directory("nonexistent_dir")
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_binary_file_handling(self, file_ops):
        """Test handling of binary files"""
        # Create binary content
        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        
        # Write binary file using direct file operations (simulating binary write)
        binary_path = file_ops.workspace_dir / "binary.png"
        binary_path.write_bytes(binary_content)
        
        # Read binary file
        result = await file_ops.read_file("binary.png")
        assert result["success"] is True
        assert result["binary"] is True
        assert result["content"] == binary_content.hex()
        assert result["size"] == len(binary_content)