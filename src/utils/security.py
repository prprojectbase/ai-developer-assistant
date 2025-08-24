"""
Security utilities for AI Developer Assistant
"""

import re
import shlex
import os
import subprocess
from typing import List, Set, Optional, Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from ..config.settings import get_settings


class CommandRiskLevel(Enum):
    """Risk levels for terminal commands"""
    SAFE = 1
    LOW_RISK = 2
    MEDIUM_RISK = 3
    HIGH_RISK = 4
    DANGEROUS = 5


@dataclass
class CommandRule:
    """Command whitelist rule"""
    pattern: str
    risk_level: CommandRiskLevel
    description: str
    allowed_args: Optional[List[str]] = None
    blocked_args: Optional[List[str]] = None
    require_confirmation: bool = False


class TerminalSecurityManager:
    """Security manager for terminal operations"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Default command whitelist
        self.command_whitelist = self._create_default_whitelist()
        
        # Additional custom rules from configuration
        self.custom_rules: List[CommandRule] = []
        
        # Security settings
        self.enable_sandbox = True
        self.max_command_length = 1000
        self.block_network_commands = True
        self.block_file_modification = False
        
    def _create_default_whitelist(self) -> List[CommandRule]:
        """Create default command whitelist"""
        return [
            # File operations (read-only)
            CommandRule(
                pattern=r"^(ls|dir|ll|la)$",
                risk_level=CommandRiskLevel.SAFE,
                description="List directory contents"
            ),
            CommandRule(
                pattern=r"^(ls|dir|ll|la)\s+",
                risk_level=CommandRiskLevel.SAFE,
                description="List directory contents with arguments",
                blocked_args=["-R", "-r", "--recursive"]  # Block recursive listing
            ),
            CommandRule(
                pattern=r"^(cat|less|more|head|tail)$",
                risk_level=CommandRiskLevel.SAFE,
                description="Read file contents",
                blocked_args=["/dev/*", "/proc/*", "/sys/*"]
            ),
            CommandRule(
                pattern=r"^(pwd|echo|date|whoami|hostname)$",
                risk_level=CommandRiskLevel.SAFE,
                description="System information commands"
            ),
            
            # Development tools (low risk)
            CommandRule(
                pattern=r"^python3?\s+-c\s+",
                risk_level=CommandRiskLevel.LOW_RISK,
                description="Python one-liner",
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^python3?\s+",
                risk_level=CommandRiskLevel.LOW_RISK,
                description="Python script execution",
                allowed_args=["-m", "--version", "-h", "--help"],
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^(pip|pip3)\s+(install|list|show|check)$",
                risk_level=CommandRiskLevel.LOW_RISK,
                description="Python package management",
                blocked_args=["--user", "--system", "--root"],
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^npm\s+(list|view|audit)$",
                risk_level=CommandRiskLevel.LOW_RISK,
                description="Node package management (read-only)"
            ),
            CommandRule(
                pattern=r"^(git\s+(status|log|diff|show|branch|tag))$",
                risk_level=CommandRiskLevel.LOW_RISK,
                description="Git read-only commands"
            ),
            
            # Build and test tools (medium risk)
            CommandRule(
                pattern=r"^(make|nmake|cmake|meson)$",
                risk_level=CommandRiskLevel.MEDIUM_RISK,
                description="Build tools",
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^(pytest|unittest|test)$",
                risk_level=CommandRiskLevel.MEDIUM_RISK,
                description="Testing frameworks",
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^(gcc|g\+\+|clang|cl)\s+",
                risk_level=CommandRiskLevel.MEDIUM_RISK,
                description="Compilers",
                require_confirmation=True
            ),
            
            # System information (medium risk)
            CommandRule(
                pattern=r"^(ps|top|htop|free|df|du)$",
                risk_level=CommandRiskLevel.MEDIUM_RISK,
                description="System monitoring commands"
            ),
            CommandRule(
                pattern=r"^(uname|lscpu|lsblk|lspci|lsusb)$",
                risk_level=CommandRiskLevel.MEDIUM_RISK,
                description="System information commands"
            ),
            
            # Network commands (high risk - disabled by default)
            CommandRule(
                pattern=r"^(curl|wget|ftp|sftp)$",
                risk_level=CommandRiskLevel.HIGH_RISK,
                description="Network download commands",
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^(ping|traceroute|nslookup|dig)$",
                risk_level=CommandRiskLevel.HIGH_RISK,
                description="Network diagnostic commands",
                require_confirmation=True
            ),
            
            # Dangerous commands (blocked)
            CommandRule(
                pattern=r"^(rm|del|rmdir|move|copy|xcopy)$",
                risk_level=CommandRiskLevel.DANGEROUS,
                description="File deletion/modification commands",
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^(chmod|chown|chgrp)$",
                risk_level=CommandRiskLevel.DANGEROUS,
                description="Permission modification commands",
                require_confirmation=True
            ),
            CommandRule(
                pattern=r"^(sudo|su|doas|runas)$",
                risk_level=CommandRiskLevel.DANGEROUS,
                description="Privilege escalation commands"
            ),
            CommandRule(
                pattern=r"^(\.\.|~/|\.\./|/)",
                risk_level=CommandRiskLevel.DANGEROUS,
                description="Path traversal commands"
            ),
            CommandRule(
                pattern=r"^(\s*&&|\s*\|\|)",
                risk_level=CommandRiskLevel.DANGEROUS,
                description="Command chaining operators"
            ),
            CommandRule(
                pattern=r"^(\s*>\s*|\s*>>\s*|\s*<\s*)",
                risk_level=CommandRiskLevel.DANGEROUS,
                description="Redirection operators"
            ),
        ]
    
    def add_custom_rule(self, rule: CommandRule) -> None:
        """Add a custom command rule"""
        self.custom_rules.append(rule)
        self.logger.info(f"Added custom command rule: {rule.pattern}")
    
    def validate_command(self, command: str) -> Tuple[bool, str, CommandRiskLevel]:
        """Validate a terminal command"""
        # Check command length
        if len(command) > self.max_command_length:
            return False, f"Command too long (max {self.max_command_length} characters)", CommandRiskLevel.DANGEROUS
        
        # Parse command
        try:
            parts = shlex.split(command.strip())
            if not parts:
                return False, "Empty command", CommandRiskLevel.DANGEROUS
            
            base_command = parts[0]
            full_command = command.strip()
            
        except ValueError as e:
            return False, f"Invalid command syntax: {e}", CommandRiskLevel.DANGEROUS
        
        # Check against all rules
        all_rules = self.command_whitelist + self.custom_rules
        
        for rule in all_rules:
            if re.match(rule.pattern, full_command, re.IGNORECASE):
                # Check if command is explicitly allowed
                if rule.risk_level in [CommandRiskLevel.SAFE, CommandRiskLevel.LOW_RISK]:
                    # Check for blocked arguments
                    if rule.blocked_args:
                        for blocked_arg in rule.blocked_args:
                            if blocked_arg in full_command:
                                return False, f"Blocked argument: {blocked_arg}", CommandRiskLevel.DANGEROUS
                    
                    # Check for allowed arguments (if specified)
                    if rule.allowed_args:
                        args_valid = False
                        for allowed_arg in rule.allowed_args:
                            if allowed_arg in full_command:
                                args_valid = True
                                break
                        
                        if not args_valid:
                            return False, f"Command requires one of allowed arguments: {rule.allowed_args}", CommandRiskLevel.DANGEROUS
                    
                    return True, rule.description, rule.risk_level
                
                elif rule.risk_level in [CommandRiskLevel.MEDIUM_RISK, CommandRiskLevel.HIGH_RISK]:
                    # Medium and high risk commands require confirmation
                    if rule.require_confirmation:
                        return True, f"{rule.description} (requires confirmation)", rule.risk_level
                    else:
                        return True, rule.description, rule.risk_level
                
                elif rule.risk_level == CommandRiskLevel.DANGEROUS:
                    # Dangerous commands are blocked
                    return False, f"Dangerous command blocked: {rule.description}", CommandRiskLevel.DANGEROUS
        
        # If no rule matches, command is not allowed
        return False, f"Command not in whitelist: {base_command}", CommandRiskLevel.DANGEROUS
    
    def sanitize_command(self, command: str) -> str:
        """Sanitize a command for safe execution"""
        # Remove potentially dangerous characters
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '{', '}', '<', '>']
        sanitized = command
        
        for char in dangerous_chars:
            if char in ['<', '>']:
                # Only remove redirection if not part of a valid argument
                if self._is_dangerous_redirection(sanitized, char):
                    sanitized = sanitized.replace(char, ' ')
            else:
                sanitized = sanitized.replace(char, ' ')
        
        # Remove excessive whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def _is_dangerous_redirection(self, command: str, char: str) -> bool:
        """Check if redirection character is dangerous"""
        # This is a simplified check - in production, you'd want more sophisticated parsing
        if char in ['<', '>']:
            # Allow redirection to /dev/null or temporary files
            if '/dev/null' in command or '.tmp' in command or '.temp' in command:
                return False
            return True
        return False
    
    def check_command_safety(self, command: str) -> Dict[str, Any]:
        """Comprehensive command safety check"""
        is_valid, message, risk_level = self.validate_command(command)
        
        result = {
            "is_safe": is_valid,
            "message": message,
            "risk_level": risk_level.value,
            "risk_level_name": risk_level.name,
            "requires_confirmation": risk_level in [CommandRiskLevel.MEDIUM_RISK, CommandRiskLevel.HIGH_RISK],
            "sanitized_command": None,
            "warnings": []
        }
        
        # Generate warnings
        if is_valid:
            if risk_level == CommandRiskLevel.HIGH_RISK:
                result["warnings"].append("High risk command - review carefully")
            elif risk_level == CommandRiskLevel.MEDIUM_RISK:
                result["warnings"].append("Medium risk command - exercise caution")
            
            # Check for potentially dangerous patterns
            if self._contains_dangerous_patterns(command):
                result["warnings"].append("Command contains potentially dangerous patterns")
        else:
            result["warnings"].append("Command validation failed")
        
        # Provide sanitized version if possible
        if is_valid:
            sanitized = self.sanitize_command(command)
            if sanitized != command:
                result["sanitized_command"] = sanitized
                result["warnings"].append("Command was sanitized for safety")
        
        return result
    
    def _contains_dangerous_patterns(self, command: str) -> bool:
        """Check for dangerous patterns in command"""
        dangerous_patterns = [
            r'/etc/passwd',
            r'/etc/shadow',
            r'/proc/',
            r'/sys/',
            r'/dev/',
            r'~/.ssh/',
            r'\.ssh/',
            r'password',
            r'secret',
            r'key',
            r'token',
            r'rm\s+-rf',
            r'format',
            r'delete',
            r'drop',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return False
    
    def get_allowed_commands(self) -> List[Dict[str, any]]:
        """Get list of allowed commands"""
        allowed_commands = []
        
        for rule in self.command_whitelist + self.custom_rules:
            if rule.risk_level in [CommandRiskLevel.SAFE, CommandRiskLevel.LOW_RISK]:
                allowed_commands.append({
                    "pattern": rule.pattern,
                    "description": rule.description,
                    "risk_level": rule.risk_level.name,
                    "requires_confirmation": rule.require_confirmation
                })
        
        return allowed_commands
    
    def get_command_statistics(self) -> Dict[str, any]:
        """Get command security statistics"""
        total_rules = len(self.command_whitelist + self.custom_rules)
        safe_commands = sum(1 for rule in self.command_whitelist + self.custom_rules 
                           if rule.risk_level == CommandRiskLevel.SAFE)
        low_risk_commands = sum(1 for rule in self.command_whitelist + self.custom_rules 
                               if rule.risk_level == CommandRiskLevel.LOW_RISK)
        medium_risk_commands = sum(1 for rule in self.command_whitelist + self.custom_rules 
                                  if rule.risk_level == CommandRiskLevel.MEDIUM_RISK)
        high_risk_commands = sum(1 for rule in self.command_whitelist + self.custom_rules 
                                if rule.risk_level == CommandRiskLevel.HIGH_RISK)
        
        return {
            "total_rules": total_rules,
            "safe_commands": safe_commands,
            "low_risk_commands": low_risk_commands,
            "medium_risk_commands": medium_risk_commands,
            "high_risk_commands": high_risk_commands,
            "dangerous_commands": total_rules - safe_commands - low_risk_commands - medium_risk_commands - high_risk_commands,
            "sandbox_enabled": self.enable_sandbox,
            "max_command_length": self.max_command_length,
            "network_commands_blocked": self.block_network_commands
        }
    
    @property
    def logger(self):
        """Get logger instance"""
        import logging
        return logging.getLogger(__name__)


# Global security manager instance
security_manager = TerminalSecurityManager()